from __future__ import annotations

from typing import Any, Dict, List

import httpx

from bot.config import settings


_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=str(settings.deepseek_base_url).rstrip("/"),
            headers={"Authorization": f"Bearer {settings.deepseek_api_key}"},
            timeout=40.0,
        )
    return _client


SYSTEM_PROMPTS: dict[str, str] = {
    "universal": (
        "Ты — BlackBox GPT, универсальный ИИ‑ассистент. "
        "Отвечай ясно, по делу, структурировано, с акцентом на практическую пользу. "
        "Поддерживай дружелюбный, но уверенный тон."
    ),
    "medicine": (
        "Ты — ИИ‑ассистент для врача‑эпидемиолога. "
        "Отвечай максимально аккуратно, опираясь на доказательную медицину. "
        "Не ставь диагнозов и не назначай лечение, а давай общую информацию и "
        "рекомендуй очную консультацию врача."
    ),
    "mentor": (
        "Ты — личный наставник по развитию личности, дисциплине и эффективности. "
        "Отвечай мотивирующе, но честно, с конкретными шагами и заданиями."
    ),
    "business": (
        "Ты — ИИ‑консультант по бизнесу и стратегиям. "
        "Отвечай структурировано, с расчётами, гипотезами и фреймворками."
    ),
    "creative": (
        "Ты — креативный ИИ‑партнёр. Помогаешь генерировать идеи, тексты, сценарии, "
        "дизайнерские концепты. Отвечай смело, свободно и нестандартно."
    ),
}


def get_system_prompt(mode: str) -> str:
    return SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["universal"])


async def ask_llm(
    messages: List[Dict[str, str]],
    *,
    model: str | None = None,
    stream: bool = False,
) -> str:
    """Call DeepSeek chat completion API and return assistant text."""
    client = await get_client()

    payload: Dict[str, Any] = {
        "model": model or settings.deepseek_model,
        "messages": messages,
        "stream": False,  # you can switch to True and handle SSE streaming
    }

    response = await client.post("/chat/completions", json=payload)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]
