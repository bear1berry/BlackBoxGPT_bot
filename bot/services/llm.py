from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from bot.config import settings
from bot.storage.models import UserMode
from bot.storage.repo import UserRepository
from bot.texts import LLM_TEMP_ERROR_TEXT

logger = logging.getLogger(__name__)


async def _call_deepseek(prompt: str, user_mode: UserMode) -> str:
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    system_prompt = (
        "Ты — умный, аккуратный ассистент BlackBox GPT. "
        "Отвечай по делу, без воды, учитывая режим пользователя: "
        f"{user_mode.value}."
    )
    payload: Dict[str, Any] = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }

    timeout = httpx.Timeout(settings.llm_timeout_sec)
    async with httpx.AsyncClient(base_url=settings.deepseek_api_base, timeout=timeout) as client:
        resp = await client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        logger.exception("Unexpected DeepSeek response structure: %s", data)
        return LLM_TEMP_ERROR_TEXT


async def _call_perplexity(prompt: str, user_mode: UserMode) -> str:
    headers = {
        "Authorization": f"Bearer {settings.perplexity_api_key}",
        "Content-Type": "application/json",
    }
    system_prompt = (
        "Ты — BlackBox GPT, ассистент с доступом к актуальным данным через Perplexity. "
        "Отвечай кратко, структурированно, с ссылкой на факты, учитывая режим: "
        f"{user_mode.value}."
    )
    payload: Dict[str, Any] = {
        "model": settings.perplexity_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    }

    timeout = httpx.Timeout(settings.llm_timeout_sec)
    async with httpx.AsyncClient(base_url=settings.perplexity_api_base, timeout=timeout) as client:
        resp = await client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        logger.exception("Unexpected Perplexity response structure: %s", data)
        return LLM_TEMP_ERROR_TEXT


async def generate_answer(user_id: int, username: str | None, message: str) -> str:
    repo = UserRepository()
    user = await repo.get_or_create(user_id=user_id, username=username)

    provider = settings.llm_provider
    try:
        if provider == "perplexity" and settings.perplexity_api_key:
            return await _call_perplexity(message, user.mode)
        if provider == "deepseek" and settings.deepseek_api_key:
            return await _call_deepseek(message, user.mode)

        # fallback
        if settings.deepseek_api_key:
            return await _call_deepseek(message, user.mode)
        if settings.perplexity_api_key:
            return await _call_perplexity(message, user.mode)

        return (
            "⚠️ Не настроен ни один ключ LLM.\n"
            "Добавь хотя бы DEEPSEEK_API_KEY или PERPLEXITY_API_KEY в .env."
        )
    except httpx.HTTPError as e:
        logger.error("LLM HTTP error: %s", e, exc_info=True)
        return LLM_TEMP_ERROR_TEXT
    except Exception:
        logger.exception("Unexpected LLM error")
        return LLM_TEMP_ERROR_TEXT
