import logging
from typing import Literal, List, Dict, Any

import httpx

from bot.config import settings
from bot.texts import temporary_llm_error_text

logger = logging.getLogger(__name__)

Provider = Literal["deepseek", "perplexity"]


def build_system_prompt(mode: str) -> str:
    base = (
        "Ты — BlackBox GPT, универсальный русскоязычный AI-ассистент. "
        "Отвечай структурировано, понятно и по делу. "
        "Используй разметку HTML (теги <b>, <i>, <code>, <pre>, <u>, <a>), но не Markdown. "
        "Если пользователь спрашивает о медицине, помни, что это не заменяет очную консультацию."
    )

    if mode == "medicine":
        return (
            base
            + " Ты говоришь как грамотный врач-эпидемиолог. Указывай, что твой ответ не является "
            "медицинской консультацией и необходим очный осмотр специалиста."
        )
    if mode == "mentor":
        return (
            base
            + " Ты выступаешь как личный наставник по развитию личности, дисциплине и продуктивности. "
            "Никакой эзотерики, только рациональный подход и практические рекомендации."
        )
    if mode == "business":
        return (
            base
            + " Ты помогаешь с бизнес-идеями, стратегией, анализом рынков и продуктов. "
            "Отвечай как предприниматель с опытом."
        )
    if mode == "creative":
        return (
            base
            + " Ты помогаешь генерировать креативные идеи: тексты, названия, сценарии, концепции."
        )
    return base


class LLMClient:
    def __init__(self) -> None:
        self._timeout = settings.llm_timeout_sec

    async def ask(
        self,
        *,
        user_message: str,
        mode: str,
        user_id: int | None = None,
        provider: Provider | None = None,
    ) -> str:
        provider = provider or settings.default_provider
        system_prompt = build_system_prompt(mode=mode)

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        try:
            if provider == "perplexity":
                return await self._call_perplexity(messages)
            return await self._call_deepseek(messages)
        except Exception:
            logger.exception("LLM request failed")
            return temporary_llm_error_text()

    async def _call_deepseek(self, messages: List[Dict[str, str]]) -> str:
        if not settings.deepseek_api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not set")

        url = settings.deepseek_api_base.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": settings.deepseek_model,
            "messages": messages,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        return data["choices"][0]["message"]["content"].strip()

    async def _call_perplexity(self, messages: List[Dict[str, str]]) -> str:
        if not settings.perplexity_api_key:
            raise RuntimeError("PERPLEXITY_API_KEY is not set")

        url = settings.perplexity_api_base.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.perplexity_api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": settings.perplexity_model,
            "messages": messages,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        return data["choices"][0]["message"]["content"].strip()


llm_client = LLMClient()


async def ask_llm(
    *,
    user_message: str,
    mode: str,
    user_id: int | None = None,
    provider: Provider | None = None,
) -> str:
    return await llm_client.ask(
        user_message=user_message,
        mode=mode,
        user_id=user_id,
        provider=provider,
    )
