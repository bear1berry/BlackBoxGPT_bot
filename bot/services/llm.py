from __future__ import annotations

from typing import Iterable, Tuple, Literal

import httpx

from bot.config import Settings
from bot.modes import get_mode_config

Backend = Literal["deepseek", "perplexity"]


def _choose_backend(settings: Settings, mode: str) -> Backend:
    strategy = (settings.llm_provider or "auto").lower()

    if strategy in {"deepseek", "perplexity"}:
        return strategy  # type: ignore[return-value]

    if mode in {"universal", "business", "creative"} and settings.perplexity_api_key:
        return "perplexity"
    if settings.deepseek_api_key:
        return "deepseek"
    return "deepseek"


async def _call_deepseek(
    settings: Settings,
    mode: str,
    user_message: str,
    history: Iterable[Tuple[str, str]] | None,
) -> str:
    mode_cfg = get_mode_config(mode)
    messages = [{"role": "system", "content": mode_cfg.system_prompt}]

    if history:
        for role, content in history:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": settings.deepseek_model,
        "messages": messages,
        "temperature": 0.7,
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.deepseek.com/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    return data["choices"][0]["message"]["content"].strip()


async def _call_perplexity(
    settings: Settings,
    mode: str,
    user_message: str,
    history: Iterable[Tuple[str, str]] | None,
) -> str:
    mode_cfg = get_mode_config(mode)
    messages = [{"role": "system", "content": mode_cfg.system_prompt}]

    if history:
        for role, content in history:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": settings.perplexity_model,
        "messages": messages,
        "temperature": 0.7,
    }

    headers = {
        "Authorization": f"Bearer {settings.perplexity_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://api.perplexity.ai/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"].strip()
    if "</think>" in content:
        content = content.split("</think>", 1)[-1].strip()
    return content


async def ask_llm(
    settings: Settings,
    mode: str,
    user_message: str,
    history: Iterable[Tuple[str, str]] | None = None,
) -> str:
    backend = _choose_backend(settings, mode)

    async def _try_backend(b: Backend) -> str:
        if b == "deepseek":
            if not settings.deepseek_api_key:
                raise RuntimeError("DEEPSEEK_API_KEY is not set")
            return await _call_deepseek(settings, mode, user_message, history)
        if not settings.perplexity_api_key:
            raise RuntimeError("PERPLEXITY_API_KEY is not set")
        return await _call_perplexity(settings, mode, user_message, history)

    try:
        return await _try_backend(backend)
    except Exception:
        alt: Backend = "perplexity" if backend == "deepseek" else "deepseek"
        try:
            return await _try_backend(alt)
        except Exception as exc:
            return (
                "⚠️ Не удалось получить ответ от LLM-сервисов. "
                "Попробуй ещё раз чуть позже. "
                f"(техническая ошибка: {type(exc).__name__})"
            )
