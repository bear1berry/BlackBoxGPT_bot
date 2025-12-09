from __future__ import annotations

import logging
from typing import Literal, List, Dict, Any

import httpx

from bot.config import settings
from bot import texts


logger = logging.getLogger(__name__)

LLMProvider = Literal["deepseek", "perplexity"]


class LLMClient:
    def __init__(self) -> None:
        self._timeout = settings.llm_timeout_sec

    async def ask(
        self,
        messages: List[Dict[str, Any]],
        provider: LLMProvider,
    ) -> str:
        if provider == "deepseek":
            return await self._ask_deepseek(messages)
        if provider == "perplexity":
            return await self._ask_perplexity(messages)
        raise ValueError(f"Unknown LLM provider: {provider}")

    async def _ask_deepseek(self, messages: List[Dict[str, Any]]) -> str:
        if not settings.deepseek_api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not configured")

        url = settings.deepseek_api_base.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.deepseek_model,
            "messages": messages,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected DeepSeek response: %s", exc)
            raise RuntimeError(f"DeepSeek response format error: {data}") from exc

    async def _ask_perplexity(self, messages: List[Dict[str, Any]]) -> str:
        if not settings.perplexity_api_key:
            raise RuntimeError("PERPLEXITY_API_KEY is not configured")

        url = settings.perplexity_api_base.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.perplexity_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.perplexity_model,
            "messages": messages,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected Perplexity response: %s", exc)
            raise RuntimeError(f"Perplexity response format error: {data}") from exc


llm_client = LLMClient()


def _build_system_prompt(mode: str, profile: dict | None) -> str:
    parts: list[str] = []

    if mode == "universal":
        parts.append(
            "Ты — универсальный ИИ-ассистент BlackBox GPT. "
            "Отвечай чётко, по делу, без воды."
        )
    elif mode == "med":
        parts.append(
            "Ты — медицинский ассистент. "
            "Объясняй медицинские темы простым языком, но НЕ ставь диагнозов и "
            "НЕ назначай лечение. Всегда напоминай о необходимости очной консультации врача."
        )
    elif mode == "mentor":
        parts.append(
            "Ты — личный наставник. Помогаешь с дисциплиной, развитием, карьерой. "
            "Говори прямолинейно, но поддерживающе."
        )
    elif mode == "business":
        parts.append(
            "Ты — бизнес-ассистент. Помогаешь с идеями, стратегией, маркетингом, "
            "анализом продуктов и рынков."
        )
    elif mode == "creative":
        parts.append(
            "Ты — креативный ассистент. Генерируешь идеи, тексты, концепции, сценарии. "
            "Можешь быть смелее и свободнее в формулировках."
        )
    else:
        parts.append(
            "Ты — универсальный ИИ-ассистент BlackBox GPT. Отвечай максимально полезно."
        )

    if profile:
        parts.append(f"Информация о пользователе: {profile}.")

    return " ".join(parts)


def _pick_provider(user_text: str) -> LLMProvider:
    """
    Очень лёгкое адаптивное правило выбора модели:
    • если пользователь явно просит «поиск», «найди в интернете», используем Perplexity;
    • иначе — DeepSeek (по умолчанию).
    """
    text = user_text.lower()
    if any(word in text for word in ("поиск", "найди в интернете", "google", "искать в сети")):
        return "perplexity"

    default = settings.default_llm_provider.lower()
    return "perplexity" if default == "perplexity" else "deepseek"


async def ask_llm(
    user_id: int,
    mode: str,
    user_text: str,
    profile: dict | None = None,
) -> str:
    system_prompt = _build_system_prompt(mode, profile)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ]

    provider = _pick_provider(user_text)

    try:
        reply = await llm_client.ask(messages=messages, provider=provider)
        logger.info("LLM provider=%s user_id=%s mode=%s", provider, user_id, mode)
        return reply
    except Exception as exc:  # noqa: BLE001
        logger.exception("LLM error for user %s: %s", user_id, exc)
        return texts.LLM_ERROR_FALLBACK
