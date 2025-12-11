from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import httpx

from ..config import settings
from .text_postprocess import clean_llm_answer

log = logging.getLogger(__name__)


class Mode(str, Enum):
    UNIVERSAL = "universal"
    PROFESSIONAL = "professional"


WEB_KEYWORDS: List[str] = [
    "найди",
    "последние",
    "новые исследования",
    "новые статьи",
    "что сейчас",
    "актуальные данные",
    "последние новости",
    "в 2024",
    "в 2025",
    "курс",
    "цену",
    "стоимость",
    "рейтинги",
    "обновления",
    "reddit",
    "форум",
    "сравни",
    "vs ",
    "review",
    "отзывы",
]


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str


def _need_web_search(prompt: str) -> bool:
    lowered = prompt.lower()
    return any(k in lowered for k in WEB_KEYWORDS)


async def _call_deepseek(prompt: str, system_prompt: Optional[str] = None) -> LLMResult:
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": settings.deepseek_model,
        "messages": messages,
        "temperature": 0.4,
        "top_p": 0.9,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]
    return LLMResult(
        text=clean_llm_answer(content),
        provider="deepseek",
        model=settings.deepseek_model,
    )


async def _call_perplexity(
    prompt: str,
    system_prompt: Optional[str] = None,
) -> LLMResult:
    if not settings.perplexity_api_key:
        raise RuntimeError("PERPLEXITY_API_KEY is not configured")

    headers = {
        "Authorization": f"Bearer {settings.perplexity_api_key}",
        "Content-Type": "application/json",
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": settings.perplexity_model,
        "messages": messages,
        "temperature": 0.2,
        "top_p": 0.9,
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]
    return LLMResult(
        text=clean_llm_answer(content),
        provider="perplexity",
        model=settings.perplexity_model,
    )


async def ask_llm(prompt: str, mode: Mode) -> LLMResult:
    """
    Универсальный вход для бота.

    - UNIVERSAL  -> DeepSeek, без веба.
    - PROFESSIONAL:
         * если запрос «про мир сейчас» → Perplexity (веб)
         * иначе → DeepSeek как умный эксперт.
    """
    system_universal = (
        "Ты универсальный интеллектуальный ассистент BlackBox GPT. "
        "Отвечай понятно, по делу, без лишней воды."
    )

    system_professional = (
        "Ты профессиональный ассистент-консультант. "
        "Умеешь говорить строго, ёмко, без сюсюканья. "
        "Дай структуру, логику, практику. Если нужно, опирайся на свежие данные из интернета."
    )

    try:
        if mode is Mode.UNIVERSAL:
            return await _call_deepseek(prompt, system_universal)

        # PROFESSIONAL
        use_web = _need_web_search(prompt) and bool(settings.perplexity_api_key)

        if use_web:
            log.info("Professional mode: using Perplexity (web) for prompt")
            return await _call_perplexity(prompt, system_professional)

        # Если веб явно не требуется или нет ключа Perplexity — идём в DeepSeek
        log.info("Professional mode: using DeepSeek (no web) for prompt")
        return await _call_deepseek(prompt, system_professional)

    except Exception:
        log.exception("LLM request failed, falling back to simple error message")
        return LLMResult(
            text=(
                "Произошла ошибка при обращении к модели.\n"
                "Попробуй ещё раз чуть позже или измени формулировку запроса."
            ),
            provider="error",
            model="n/a",
        )
