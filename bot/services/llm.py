# bot/services/llm.py

from __future__ import annotations

from enum import Enum
from typing import Optional

from . import deepseek_client, perplexity_client


class Provider(str, Enum):
    PERPLEXITY = "perplexity"
    DEEPSEEK = "deepseek"


# Маршрутизация по режимам:
# — наставник и медицина → Perplexity sonar-reasoning / sonar-medical
# — универсальный / бизнес / креатив → DeepSeek
MODE_PROVIDER: dict[str, Provider] = {
    "universal": Provider.DEEPSEEK,
    "business": Provider.DEEPSEEK,
    "creative": Provider.DEEPSEEK,
    "mentor": Provider.PERPLEXITY,
    "medicine": Provider.PERPLEXITY,
}


async def generate_answer(
    *,
    mode: str,
    user_text: str,
    system_prompt: Optional[str] = None,
    provider: str = "auto",
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """
    Единая точка входа для генерации ответа.

    mode       — текущий режим бота (universal / medicine / mentor / business / creative)
    user_text  — текст пользователя
    system_prompt — системный промпт (стиль ответа / инструкции)
    provider   — "auto" | "perplexity" | "deepseek"
    """
    mode = (mode or "universal").lower()

    # Определяем провайдера
    if provider.lower() == "perplexity":
        backend = Provider.PERPLEXITY
    elif provider.lower() == "deepseek":
        backend = Provider.DEEPSEEK
    else:  # auto
        backend = MODE_PROVIDER.get(mode, Provider.DEEPSEEK)

    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_text})

    if backend is Provider.PERPLEXITY:
        return await perplexity_client.chat(
            mode=mode,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    return await deepseek_client.chat(
        mode=mode,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
