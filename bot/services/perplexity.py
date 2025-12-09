# bot/services/perplexity.py
from __future__ import annotations
import logging
from typing import Literal

import httpx

from ..config import settings
from ..texts import format_llm_answer

logger = logging.getLogger(__name__)

ModeType = Literal["universal", "medicine", "mentor", "business", "creative"]

MODE_TO_MODEL: dict[ModeType, str] = {
    "universal": "sonar",
    "medicine": "sonar-reasoning",
    "mentor": "sonar-reasoning",
    "business": "sonar",
    "creative": "sonar",
}


async def ask_perplexity(
    *,
    mode: ModeType,
    user_prompt: str,
    system_prompt: str | None = None,
) -> str:
    model = MODE_TO_MODEL.get(mode, "sonar")
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": user_prompt})

    headers = {
        "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }

    async with httpx.AsyncClient(base_url=settings.PERPLEXITY_BASE_URL, timeout=60) as client:
        resp = await client.post("/chat/completions", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]
    return format_llm_answer(content)
