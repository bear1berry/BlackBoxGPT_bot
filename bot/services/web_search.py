from __future__ import annotations

import logging

import httpx

from ..config import settings

log = logging.getLogger(__name__)


async def research(query: str) -> str:
    """
    Web-поиск через Perplexity.

    В проде используется в:
    - режиме PROFESSIONAL (когда нужно «гуглить»),
    - режиме RESEARCH (если когда-нибудь включим его в интерфейсе).
    """
    if not settings.perplexity_api_key:
        return (
            "WEB-поиск пока не подключён.\n\n"
            "Добавь PERPLEXITY_API_KEY и PERPLEXITY_MODEL в .env, "
            "чтобы я мог использовать Perplexity."
        )

    url = "https://api.perplexity.ai/chat/completions"

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
                    "Ты — ассистент для web-поиска. "
                    "Используй Интернет, чтобы находить актуальную информацию, "
                    "но всегда проверяй факты и пиши кратко и структурировано."
                ),
            },
            {"role": "user", "content": query},
        ],
        "temperature": 0.2,
        "top_p": 0.9,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0)) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:  # noqa: BLE001
        log.exception("Perplexity web_search error: %s", e)
        return (
            "Не получилось выполнить web-поиск (ошибка сервиса). "
            "Попробуй ещё раз чуть позже или переформулируй запрос."
        )
