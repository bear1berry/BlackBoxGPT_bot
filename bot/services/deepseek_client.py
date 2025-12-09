# bot/services/deepseek_client.py

from __future__ import annotations

import logging
import os
from typing import Mapping, Sequence

import httpx

logger = logging.getLogger(__name__)

DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")

# Все режимы по умолчанию на deepseek-chat, при желании можно развести по моделям
_DEEPSEEK_MODELS: dict[str, str] = {
    "universal": os.getenv("DEEPSEEK_MODEL_UNIVERSAL", "deepseek-chat"),
    "medicine": os.getenv("DEEPSEEK_MODEL_MEDICINE", "deepseek-chat"),
    "mentor": os.getenv("DEEPSEEK_MODEL_MENTOR", "deepseek-chat"),
    "business": os.getenv("DEEPSEEK_MODEL_BUSINESS", "deepseek-chat"),
    "creative": os.getenv("DEEPSEEK_MODEL_CREATIVE", "deepseek-chat"),
}

DEFAULT_DEEPSEEK_MODEL = os.getenv("DEEPSEEK_DEFAULT_MODEL", "deepseek-chat")


async def chat(
    *,
    mode: str,
    messages: Sequence[Mapping[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """
    Вызов DeepSeek chat API (OpenAI-совместимый эндпоинт).
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY не задан в окружении. Добавь его в .env"
        )

    mode = (mode or "universal").lower()
    model = _DEEPSEEK_MODELS.get(mode, DEFAULT_DEEPSEEK_MODEL)

    payload = {
        "model": model,
        "messages": list(messages),
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        # DeepSeek сейчас использует /v1/chat/completions
        resp = await client.post(
            f"{DEEPSEEK_API_BASE}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.exception("DeepSeek HTTP error: %s", e)
        raise

    data = resp.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except Exception as e:  # noqa: BLE001
        logger.exception("Unexpected DeepSeek response: %s", data)
        raise RuntimeError(f"Unexpected DeepSeek response: {e}") from e

    return content.strip()
