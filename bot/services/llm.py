from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator, Optional

import httpx

from ..config import settings
from .web_search import research as web_research

log = logging.getLogger(__name__)


class Mode(str, Enum):
    """
    Режимы работы бота.

    Сейчас в интерфейсе используются только:
    - UNIVERSAL
    - PROFESSIONAL

    MENTOR / MEDICINE оставлены для обратной совместимости и
    внутри маппятся на PROFESSIONAL.
    """

    UNIVERSAL = "universal"
    PROFESSIONAL = "professional"

    # legacy / внутренняя совместимость
    MENTOR = "mentor"
    MEDICINE = "medicine"
    RESEARCH = "research"


@dataclass
class StyleParams:
    """
    Простая модель стиля:
    0 – минимальное значение, 4 – максимальное.
    """

    formality: int = 2
    emotionality: int = 2
    length: int = 2

    def clamp(self) -> "StyleParams":
        def _c(v: int) -> int:
            return max(0, min(4, int(v)))

        return StyleParams(
            formality=_c(self.formality),
            emotionality=_c(self.emotionality),
            length=_c(self.length),
        )


def normalize_mode(mode: Mode) -> Mode:
    """Любые старые режимы приводим к актуальным."""
    if mode in (Mode.MENTOR, Mode.MEDICINE):
        return Mode.PROFESSIONAL
    return mode


def build_system_prompt(mode: Mode, style: StyleParams) -> str:
    """
    Общий системный промпт.

    Здесь мы «запихиваем» наставника и медицину в профессиональный режим.
    """
    style = style.clamp()

    base = (
        "Ты — умный, точный и аккуратный русскоязычный ассистент. "
        "Отвечай структурировано, коротко, без воды, строго по запросу пользователя. "
        "Если не хватает данных, задавай уточняющие вопросы."
    )

    # Небольшое влияние стиля на тон
    tones = {
        0: "Стиль: максимально разговорный, дружелюбный, без формальностей.",
        1: "Стиль: более свободный, допускается немного юмора.",
        2: "Стиль: баланс между разговорным и деловым тоном.",
        3: "Стиль: деловой, сдержанный.",
        4: "Стиль: максимально формальный, как официальный документ.",
    }

    emotional = {
        0: "Эмоции: почти полное отсутствие эмоциональной окраски.",
        1: "Эмоции: легкая поддержка, но без пафоса.",
        2: "Эмоции: умеренная мотивация и поддержка.",
        3: "Эмоции: яркая мотивация, вдохновляющие формулировки.",
        4: "Эмоции: максимально сильные мотивационные и вдохновляющие формулировки.",
    }

    length = {
        0: "Длина ответа: максимально коротко (1–2 предложения).",
        1: "Длина ответа: коротко, только суть.",
        2: "Длина ответа: средне – несколько абзацев, если нужно.",
        3: "Длина ответа: можно развернуто, но без лишней воды.",
        4: "Длина ответа: детально, с примерами и списками.",
    }

    mode = normalize_mode(mode)

    if mode == Mode.UNIVERSAL:
        role = (
            "Режим: универсальный ассистент для повседневных задач, работы, учебы, "
            "повседневных вопросов, идей, планирования. "
            "Не давай медицинских диагнозов и не выдавай себя за врача."
        )
    elif mode == Mode.PROFESSIONAL:
        role = (
            "Режим: профессиональный. "
            "Ты совмещаешь роли наставника, ментального коуча и медицинского помощника. "
            "В медицинских вопросах: отвечай как врач-специалист, но всегда подчёркивай, "
            "что это не замена очной консультации. Не ставь диагнозов, не назначай лекарства "
            "без формулировки вида 'обсудите с лечащим врачом'. "
            "В немедицинских запросах – как жёсткий, но доброжелательный наставник: "
            "конкретика, структура, план действий."
        )
    else:
        # На всякий случай
        role = "Режим: универсальный."

    return "\n\n".join(
        [
            base,
            role,
            tones[style.formality],
            emotional[style.emotionality],
            length[style.length],
        ]
    )


def needs_web_search(query: str) -> bool:
    """
    Очень простая эвристика, когда в проф-режиме переключаться на Perplexity (WEB).
    Можно потом заменить на нормальный классификатор.
    """
    q = query.lower()

    trigger_words = [
        "в интернете",
        "найди",
        "поиск",
        "search",
        "последние новости",
        "что сейчас",
        "что нового",
        "тренды",
        "статистика",
        "актуальные данные",
        "цен",
        "стоимость",
    ]

    if any(word in q for word in trigger_words):
        return True

    # Частые запросы про «что происходит сейчас» без прямых ключей
    if "сейчас" in q and "как" not in q and "почему" not in q:
        return True

    return False


class LLMClient:
    def __init__(self) -> None:
        self._deepseek_url = "https://api.deepseek.com/chat/completions"
        self._perplexity_url = "https://api.perplexity.ai/chat/completions"

    async def _ask_deepseek_stream(
        self,
        user_prompt: str,
        system_prompt: str,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        if not settings.deepseek_api_key:
            yield "DeepSeek API-ключ не настроен. Добавь DEEPSEEK_API_KEY в .env."
            return

        headers = {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": settings.deepseek_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            async with client.stream("POST", self._deepseek_url, headers=headers, json=payload) as resp:
                resp.raise_for_status()

                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    if not line.startswith("data:"):
                        continue

                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue

                    delta = (
                        chunk.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content")
                    )
                    if delta:
                        yield delta

    async def _ask_perplexity_once(
        self,
        user_prompt: str,
        system_prompt: str,
        temperature: float = 0.2,
    ) -> str:
        """
        Обычный (нестриминговый) вызов Perplexity. Используется для web-режима
        и как «умный» проф-режим.
        """
        if not settings.perplexity_api_key:
            return (
                "Perplexity API-ключ не настроен. Добавь PERPLEXITY_API_KEY в .env "
                "или используй универсальный режим."
            )

        headers = {
            "Authorization": f"Bearer {settings.perplexity_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": settings.perplexity_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        system_prompt
                        + "\n\nТы можешь использовать актуальные данные из интернета. "
                        "Если информации нет или она противоречива — честно скажи об этом."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "top_p": 0.9,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0)) as client:
            resp = await client.post(self._perplexity_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def ask_stream(
        self,
        user_prompt: str,
        mode: Mode,
        style: StyleParams,
    ) -> AsyncGenerator[str, None]:
        """
        Главная точка входа.

        - UNIVERSAL → DeepSeek
        - PROFESSIONAL:
            - если needs_web_search == True → Perplexity (web)
            - иначе → DeepSeek
        - RESEARCH → всегда Perplexity (web)
        """
        mode = normalize_mode(mode)
        style = style.clamp()

        try:
            # Чистый web-режим: всегда Perplexity + web_search()
            if mode == Mode.RESEARCH:
                web_answer = await web_research(user_prompt)
                yield web_answer
                return

            system_prompt = build_system_prompt(mode, style)

            # Профессиональный режим: умеет сам включать Perplexity
            if mode == Mode.PROFESSIONAL and needs_web_search(user_prompt):
                answer = await self._ask_perplexity_once(
                    user_prompt=user_prompt,
                    system_prompt=system_prompt,
                    temperature=0.3,
                )
                yield answer
                return

            # Всё остальное — DeepSeek стримом
            async for chunk in self._ask_deepseek_stream(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7 if mode == Mode.UNIVERSAL else 0.6,
            ):
                yield chunk

        except httpx.HTTPStatusError as e:
            log.exception("LLM HTTP error: %s", e)
            yield "Модель сейчас недоступна или вернула ошибку. Попробуй ещё раз чуть позже."
        except Exception as e:  # noqa: BLE001
            log.exception("LLM unexpected error: %s", e)
            yield "Произошла внутренняя ошибка при обращении к модели."


llm_client = LLMClient()


def infer_style_from_text(text: str) -> StyleParams:
    """
    Очень грубая эвристика для автоподстройки стиля по тексту пользователя.
    Можно потом заменить на нормальный анализатор.
    """
    text_l = text.lower()

    formality = 2
    if any(w in text_l for w in ("уважаемый", "доклад", "отчёт", "официальное")):
        formality = 3
    if any(w in text_l for w in ("чувак", "бро", "лол", "ахаха")):
        formality = 1

    emotionality = 2
    if any(w in text_l for w in ("ненавижу", "ужасно", "бесит", "очень хочу")):
        emotionality = 3
    if any(w in text_l for w in ("нормально", "ладно", "в целом ок")):
        emotionality = 1

    length = 2
    if len(text) < 40:
        length = 1
    if len(text) > 500:
        length = 3

    return StyleParams(
        formality=formality,
        emotionality=emotionality,
        length=length,
    )
