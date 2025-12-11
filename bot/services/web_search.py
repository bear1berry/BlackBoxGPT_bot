from __future__ import annotations

import logging
from typing import List, Dict, Any

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


async def research(query: str) -> str:
    """
    Выполнить web-исследование запроса `query` через Perplexity.

    Возвращает готовый к отправке в Telegram Markdown-текст.
    """

    # 1. Проверяем, настроен ли Perplexity
    if not settings.perplexity_api_key:
        return (
            "⚠️ Web-режим сейчас недоступен.\n\n"
            "Не задан `PERPLEXITY_API_KEY` в `.env`.\n"
            "Добавь ключ Perplexity, перезапусти бота — и web-поиск заработает."
        )

    system_prompt = (
        "Ты — веб-исследователь для Telegram-бота BlackBoxGPT.\n"
        "У тебя есть доступ к интернету через Perplexity. "
        "Твоя задача — сделать краткое, но насыщенное исследование по запросу пользователя.\n\n"
        "Обязательно:\n"
        "1) Найди свежую и релевантную информацию по запросу (используй несколько источников).\n"
        "2) Ответь на русском языке, структурированно, с подзаголовками и списками.\n"
        "3) Сначала дай краткое резюме (2–3 предложения).\n"
        "4) Затем перечисли ключевые выводы и рекомендации.\n"
        "5) В конце добавь блок **«Источники»** — 3–7 ссылок в формате Markdown: [Название](URL).\n"
        "Не выдумывай ссылки — используй только реальные источники."
    )

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.perplexity_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.perplexity_model,
                    "messages": messages,
                },
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPError as e:
        logger.exception("Web research HTTP error: %s", e)
        return (
            "⚠️ Не удалось выполнить web-поиск: проблема с подключением к Perplexity.\n"
            "Попробуй ещё раз чуть позже."
        )
    except Exception as e:  # noqa: BLE001
        logger.exception("Unexpected error in web research: %s", e)
        return (
            "⚠️ Не удалось выполнить web-поиск из-за внутренней ошибки.\n"
            "Попробуй изменить формулировку запроса или повтори попытку позже."
        )

    try:
        return data["choices"][0]["message"]["content"]
    except Exception as e:  # noqa: BLE001
        logger.error("Unexpected Perplexity response format: %r (%s)", data, e)
        return (
            "⚠️ Web-режим вернул неожиданный ответ от Perplexity.\n"
            "Попробуй повторить запрос или переформулировать его."
        )
