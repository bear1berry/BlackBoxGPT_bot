from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import AsyncIterator, Optional, List, Dict, Any

import httpx

from ..config import settings
from .text_postprocess import prepare_answer


class Mode(str, Enum):
    UNIVERSAL = "universal"
    PROFESSIONAL = "professional"
    MENTOR = "mentor"
    MEDICINE = "medicine"


@dataclass
class StyleParams:
    formality: int = 2        # 1 — неформально, 3 — максимально официально
    emotionality: int = 2     # 1 — сухо, 3 — эмоционально
    length: int = 2           # 1 — очень коротко, 3 — развёрнуто


def infer_style_from_text(text: str) -> StyleParams:
    lowered = text.lower()
    has_slang = any(word in lowered for word in ["бро", "брат", "ахах", "лол", "хаха"])
    has_hello = any(
        word in lowered
        for word in ["здравствуйте", "добрый день", "доброе утро", "добрый вечер"]
    )
    emojies = sum(ch >= "\U0001F300" for ch in text)
    exclam = text.count("!")

    if has_slang or emojies >= 1:
        formality = 1
    elif has_hello:
        formality = 3
    else:
        formality = 2

    if exclam >= 2 or emojies >= 2:
        emotionality = 3
    elif exclam == 0 and emojies == 0:
        emotionality = 1
    else:
        emotionality = 2

    length = 2
    return StyleParams(formality=formality, emotionality=emotionality, length=length)


class LLMClient:
    def __init__(
        self,
        deepseek_api_key: str,
        deepseek_model: str = "deepseek-chat",
        perplexity_api_key: Optional[str] = None,
        perplexity_model: str = "llama-3.1-sonar-small-128k-online",
    ) -> None:
        self.deepseek_api_key = deepseek_api_key
        self.deepseek_model = deepseek_model
        self.perplexity_api_key = perplexity_api_key
        self.perplexity_model = perplexity_model

    async def ask(
        self,
        user_prompt: str,
        mode: Mode = Mode.UNIVERSAL,
        style: Optional[StyleParams] = None,
        dialog_history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        messages = self._build_messages(
            user_prompt,
            mode=mode,
            style=style,
            dialog_history=dialog_history,
        )
        raw = await self._call_provider(messages, mode=mode)
        return prepare_answer(raw)

    async def ask_stream(
        self,
        user_prompt: str,
        mode: Mode = Mode.UNIVERSAL,
        style: Optional[StyleParams] = None,
        dialog_history: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncIterator[str]:
        """
        Псевдо-стриминг: сначала получаем полный ответ от модели, затем отдаём его по кусочкам.
        Это проще и стабильнее, чем работать с настоящим SSE-стримингом.
        """
        full = await self.ask(
            user_prompt=user_prompt,
            mode=mode,
            style=style,
            dialog_history=dialog_history,
        )
        chunk_size = 400
        for i in range(0, len(full), chunk_size):
            yield full[i : i + chunk_size]

    def _build_messages(
        self,
        user_prompt: str,
        mode: Mode,
        style: Optional[StyleParams],
        dialog_history: Optional[List[Dict[str, Any]]],
    ) -> List[Dict[str, str]]:
        system_parts = [
            "Ты — BlackBoxGPT, универсальный AI-ассистент в Telegram.",
            "Отвечай структурированно, короткими абзацами, с подзаголовками и списками, где это уместно.",
            "Пиши на русском, если пользователь не попросил другое.",
            "Используй Markdown: **жирный**, списки, но без чрезмерного форматирования.",
            "Если тема связана с медициной — давай только общие рекомендации без точных дозировок и диагнозов.",
        ]

        if mode == Mode.MENTOR:
            system_parts.append(
                "Ты выступаешь как наставник по дисциплине, режиму дня, целям. "
                "Отвечай жёстко, но поддерживающе: короткая мотивация + практическая задача."
            )
        elif mode == Mode.MEDICINE:
            system_parts.append(
                "Ты — врач-эпидемиолог-консультант. Даёшь только общие справочные сведения, "
                "не ставишь диагнозы и не назначаешь лечение. Всегда добавляй предупреждение "
                "о необходимости очного осмотра врача при серьёзных симптомах."
            )
        elif mode == Mode.PROFESSIONAL:
            system_parts.append(
                "Режим профессиональной аналитики: отвечай максимально строго, логично и структурировано, "
                "с фокусом на факты и аргументацию."
            )

        if style:
            system_parts.append(
                f"Формальность: {style.formality}/3, эмоциональность: {style.emotionality}/3, "
                f"развёрнутость: {style.length}/3. Подстрой формат ответа под эти параметры."
            )

        system_prompt = " ".join(system_parts)

        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if dialog_history:
            messages.extend(dialog_history)
        messages.append({"role": "user", "content": user_prompt})
        return messages

    async def _call_provider(self, messages: List[Dict[str, str]], mode: Mode) -> str:
        if mode == Mode.PROFESSIONAL and self.perplexity_api_key:
            try:
                return await self._call_perplexity(messages)
            except Exception:
                # При ошибке Perplexity тихо откатываемся на DeepSeek
                pass
        return await self._call_deepseek(messages)

    async def _call_deepseek(self, messages: List[Dict[str, str]]) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.deepseek_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.deepseek_model,
                    "messages": messages,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def _call_perplexity(self, messages: List[Dict[str, str]]) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.perplexity_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.perplexity_model,
                    "messages": messages,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]


llm_client = LLMClient(
    deepseek_api_key=settings.deepseek_api_key,
    deepseek_model=getattr(settings, "deepseek_model", "deepseek-chat"),
    perplexity_api_key=getattr(settings, "perplexity_api_key", None),
    perplexity_model=getattr(settings, "perplexity_model", "llama-3.1-sonar-small-128k-online"),
)
