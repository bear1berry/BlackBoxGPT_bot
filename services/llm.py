from __future__ import annotations

from typing import Sequence, Mapping

import httpx

from bot.config import Settings


MODE_SYSTEM_PROMPTS: dict[str, str] = {
    "universal": (
        "Ты — BlackBox GPT, универсальный ИИ-ассистент. "
        "Отвечай ясно, структурировано и по делу. "
        "Если пользователь просит код — давай полный, готовый к копированию."
    ),
    "medicine": (
        "Ты — ИИ-ассистент с фокусом на доказательной медицине. "
        "Не ставь диагнозы и не назначай лечение, а давай аккуратные справочные "
        "объяснения и варианты для обсуждения с врачом. "
        "Всегда напоминай, что твои ответы не заменяют очную консультацию."
    ),
    "mentor": (
        "Ты — личный наставник по развитию личности, дисциплине и карьере. "
        "Отвечай мотивирующе, но конкретно. Помогай выстроить систему, а не просто вдохновляй."
    ),
    "business": (
        "Ты — стратегический бизнес-консультант. Помогай с идеями, гипотезами, маркетингом, "
        "юнит-экономикой. Отвечай прагматично и прямо."
    ),
    "creative": (
        "Ты — креативный директор и сторителлер. Генерируй идеи, тексты, визуальные концепты. "
        "Не забывай про структуру и понятность."
    ),
}


async def ask_llm(
    *,
    settings: Settings,
    mode: str,
    user_message: str,
    history: Sequence[tuple[str, str]] | None = None,
    temperature: float = 0.7,
) -> str:
    """Call DeepSeek Chat Completion and return assistant reply."""
    system_prompt = MODE_SYSTEM_PROMPTS.get(mode, MODE_SYSTEM_PROMPTS["universal"])

    messages: list[Mapping[str, str]] = [{"role": "system", "content": system_prompt}]

    if history:
        for role, content in history:
            if role not in {"user", "assistant"}:
                continue
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"},
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": temperature,
                "stream": False,
            },
        )
        response.raise_for_status()
        data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise RuntimeError(f"Unexpected DeepSeek response: {data!r}")
