from __future__ import annotations

import logging
from typing import List

import httpx

from bot.config import settings
from db.models import DialogMessage, User

logger = logging.getLogger(__name__)


SYSTEM_PROMPT_BASE = (
    "Ты — BlackBox GPT, универсальный русскоязычный ассистент."
    " Отвечай кратко, но содержательно. "
    "Оформляй ответ как мини-статью: сначала ёмкий заголовок (выдели его <b>жирным</b>), "
    "затем структурируй текст на блоки с подзаголовками, списками и короткими абзацами. "
    "Избегай воды. Если пользователь пишет на русском — отвечай по-русски."
)


def _mode_to_perplexity_model(mode: str | None) -> str:
    mode = (mode or "universal").lower()
    if mode == "mentor":
        return settings.perplexity_model_mentor
    if mode == "medicine":
        return settings.perplexity_model_medicine
    if mode == "business":
        return settings.perplexity_model_business
    if mode == "creative":
        return settings.perplexity_model_creative
    return settings.perplexity_model_universal


def _build_messages(prompt: str, history: List[DialogMessage]) -> list[dict]:
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT_BASE}]
    for msg in history:
        if msg.role not in {"user", "assistant"}:
            continue
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": prompt})
    return messages


async def _ask_perplexity(
    user: User,
    prompt: str,
    history: List[DialogMessage],
) -> str:
    if not settings.perplexity_api_key:
        raise RuntimeError("PERPLEXITY_API_KEY не задан")

    model = _mode_to_perplexity_model(user.current_mode)
    messages = _build_messages(prompt, history)

    headers = {
        "Authorization": f"Bearer {settings.perplexity_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 1200,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.perplexity.ai/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # noqa: BLE001
            logger.exception("Perplexity response parse error: %s", exc)
            raise RuntimeError("Не удалось разобрать ответ Perplexity") from exc


async def _ask_deepseek(
    user: User,
    prompt: str,
    history: List[DialogMessage],
) -> str:
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY не задан")

    messages = _build_messages(prompt, history)
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.deepseek_model,
        "messages": messages,
        "max_tokens": 1200,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.deepseek.com/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:  # noqa: BLE001
            logger.exception("DeepSeek response parse error: %s", exc)
            raise RuntimeError("Не удалось разобрать ответ DeepSeek") from exc


async def ask_llm(
    user: User,
    prompt: str,
    history: List[DialogMessage],
) -> str:
    provider = (settings.llm_provider or "perplexity").lower()

    try:
        if provider == "perplexity":
            return await _ask_perplexity(user, prompt, history)
        if provider == "deepseek":
            return await _ask_deepseek(user, prompt, history)

        # auto
        if settings.perplexity_api_key:
            return await _ask_perplexity(user, prompt, history)
        if settings.deepseek_api_key:
            return await _ask_deepseek(user, prompt, history)

        raise RuntimeError("Не настроен ни один LLM-провайдер")
    except Exception as exc:  # noqa: BLE001
        logger.exception("LLM error: %s", exc)
        return (
            "⚠️ <b>Временная ошибка модели</b>.
"
            "Попробуй ещё раз через минуту или проверь конфиг LLM на сервере."
        )
