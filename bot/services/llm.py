from __future__ import annotations

import enum

import httpx

from ..config import get_settings


class Mode(str, enum.Enum):
    UNIVERSAL = "universal"
    PROFESSIONAL = "professional"


async def _call_deepseek(prompt: str) -> str:
    settings = get_settings()
    if not settings.deepseek_api_key:
        return "DeepSeek API key is not configured."

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    json_body = {
        "model": settings.deepseek_model,
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt},
        ],
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.deepseek.com/chat/completions",
            json=json_body,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return str(data)


async def _call_perplexity(prompt: str) -> str:
    settings = get_settings()
    if not settings.perplexity_api_key:
        return "Perplexity API key is not configured."

    headers = {
        "Authorization": f"Bearer {settings.perplexity_api_key}",
        "Content-Type": "application/json",
    }
    json_body = {
        "model": settings.perplexity_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an advanced research assistant with access to the web. "
                    "Use up-to-date sources and provide concise, structured answers."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            "https://api.perplexity.ai/chat/completions",
            json=json_body,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return str(data)


async def generate_answer(
    user_message: str,
    mode: Mode = Mode.UNIVERSAL,
    use_web: bool = False,
) -> str:
    """Единственная точка входа для генерации ответа.

    Universal:
        - Всегда DeepSeek
    Professional:
        - По умолчанию DeepSeek
        - Если use_web=True — Perplexity с web-поиском
    """
    if mode == Mode.UNIVERSAL:
        return await _call_deepseek(user_message)

    # PROFESSIONAL
    if use_web:
        return await _call_perplexity(user_message)

    # Проф. режим без web — используем DeepSeek, но в будущем можно
    # подменить на более мощную модель
    return await _call_deepseek(
        "Ты выступаешь как профессиональный эксперт. Отвечай структурировано и по делу.\n\n"
        + user_message
    )
