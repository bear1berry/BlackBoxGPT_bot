# bot/services/perplexity_client.py

from __future__ import annotations

import logging
import os
from typing import Mapping, Sequence

import httpx

logger = logging.getLogger(__name__)

PERPLEXITY_API_BASE = os.getenv("PERPLEXITY_API_BASE", "https://api.perplexity.ai")

# Модели Perplexity по режимам
_PERPLEXITY_MODELS: dict[str, str] = {
    "universal": os.getenv("PERPLEXITY_MODEL_UNIVERSAL", "sonar-pro"),
    "medicine": os.getenv("PERPLEXITY_MODEL_MEDICINE", "sonar-medical"),
    "mentor": os.getenv("PERPLEXITY_MODEL_MENTOR", "sonar-reasoning"),
    "business": os.getenv("PERPLEXITY_MODEL_BUSINESS", "sonar-reasoning"),
    "creative": os.getenv("PERPLEXITY_MODEL_CREATIVE", "sonar-pro"),
}

DEFAULT_PERPLEXITY_MODEL = os.getenv("PERPLEXITY_DEFAULT_MODEL", "sonar-pro")


async def chat(
    *,
    mode: str,
    messages: Sequence[Mapping[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """
    Вызов Perplexity Sonar / Sonar Pro / Sonar Reasoning в режиме chat.completions.
    messages — список [{"role": "system"/"user"/"assistant", "content": "..."}]
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise RuntimeError(
            "PERPLEXITY_API_KEY не задан в окружении. Добавь его в .env"
        )

    mode = (mode or "universal").lower()
    model = _PERPLEXITY_MODELS.get(mode, DEFAULT_PERPLEXITY_MODEL)

    payload = {
        "model": model,
        "messages": list(messages),
        "temperature": temperature,
        "max_tokens": max_tokens,
        # Включён веб-поиск — бот может ходить в интернет
        "search_mode": "internet",
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{PERPLEXITY_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.exception("Perplexity HTTP error: %s", e)
        raise

    data = resp.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except Exception as e:  # noqa: BLE001
        logger.exception("Unexpected Perplexity response: %s", data)
        raise RuntimeError(f"Unexpected Perplexity response: {e}") from e

    return content.strip()
