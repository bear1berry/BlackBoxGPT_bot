from __future__ import annotations

from typing import Any, Dict

import httpx

from ..config import settings

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


async def _post_perplexity(payload: Dict[str, Any]) -> str:
    """
    Низкоуровневый вызов Perplexity API.
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            PERPLEXITY_API_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {settings.perplexity_api_key}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return "Не удалось получить ответ от web-поиска Perplexity."


async def research(query: str) -> str:
    """
    Web-поиск через Perplexity.

    Используется в профессиональном режиме, когда запрос явно про
    «что сейчас», «найди в интернете», новости, цены и т.п.
    """
    payload: Dict[str, Any] = {
        "model": settings.perplexity_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты ассистент-исследователь. Используй web-поиск, "
                    "чтобы давать максимально свежие и точные ответы. "
                    "Обязательно указывай, если информация может устаревать "
                    "или данных недостаточно."
                ),
            },
            {
                "role": "user",
                "content": query,
            },
        ],
        "stream": False,
    }

    return await _post_perplexity(payload)
