from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from bot.config import get_settings
from bot.utils import postprocess_text
from storage.models import User

logger = logging.getLogger(__name__)

settings = get_settings()


class LLMProvider(ABC):
    @abstractmethod
    async def ask(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        ...


class DeepSeekProvider(LLMProvider):
    async def ask(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        if not settings.deepseek_api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not configured")

        headers = {
            "Authorization": f"Bearer {settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": settings.deepseek_model,
            "messages": messages,
            "stream": stream,
        }

        client = httpx.AsyncClient(base_url=str(settings.deepseek_api_base), timeout=60.0)

        if not stream:
            async with client as c:
                resp = await c.post("/chat/completions", json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return postprocess_text(content)

        async def _stream() -> AsyncIterator[str]:
            async with client as c:
                async with c.stream(
                    "POST",
                    "/chat/completions",
                    json=payload,
                    headers=headers,
                ) as r:
                    r.raise_for_status()
                    async for line in r.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            chunk = line[len("data:") :].strip()
                            obj = json.loads(chunk)
                        except Exception:
                            continue
                        delta = obj["choices"][0]["delta"].get("content") or ""
                        if delta:
                            yield delta

        return _stream()


class PerplexityProvider(LLMProvider):
    async def ask(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        if not settings.perplexity_api_key:
            raise RuntimeError("PERPLEXITY_API_KEY is not configured")

        headers = {
            "Authorization": f"Bearer {settings.perplexity_api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": settings.perplexity_model,
            "messages": messages,
            "stream": stream,
        }

        client = httpx.AsyncClient(base_url=str(settings.perplexity_api_base), timeout=60.0)

        if not stream:
            async with client as c:
                resp = await c.post("/chat/completions", json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return postprocess_text(content)

        async def _stream() -> AsyncIterator[str]:
            async with client as c:
                async with c.stream(
                    "POST",
                    "/chat/completions",
                    json=payload,
                    headers=headers,
                ) as r:
                    r.raise_for_status()
                    async for line in r.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        if line.strip() == "data: [DONE]":
                            break
                        try:
                            chunk = line[len("data:") :].strip()
                            obj = json.loads(chunk)
                        except Exception:
                            continue
                        delta = obj["choices"][0]["delta"].get("content") or ""
                        if delta:
                            yield delta

        return _stream()


class LLMRouter:
    """
    Маршрутизатор провайдеров:
    - Perplexity: когда нужен выход в веб / свежая инфа.
    - DeepSeek: когда нужен глубокий разбор и стилизация.
    """

    def __init__(self) -> None:
        self.deepseek = DeepSeekProvider()
        self.perplexity = PerplexityProvider()

    def _needs_web(self, user: User, user_message: str) -> bool:
        keywords = [
            "сегодня",
            "сейчас",
            "новости",
            "курс",
            "стоимость",
            "цена",
            "тренд",
            "тренды",
            "апдейт",
            "обновление",
            "что происходит",
            "свеж",
            "последние",
        ]
        low = user_message.lower()
        return any(k in low for k in keywords)

    def _is_complex(self, user_message: str) -> bool:
        return len(user_message) > 400 or user_message.count("?") > 2

    async def _verify_answer(
        self,
        draft_answer: str,
        user_message: str,
    ) -> str:
        """
        Простейшая проверка достоверности: просим DeepSeek критически
        проверить и переформулировать ответ Perplexity.
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Ты проверяешь ответ другого ассистента на корректность и достоверность. "
                        "Если находишь потенциальные ошибки, исправляешь и отмечаешь, что было уточнено. "
                        "Пиши на русском, структурировано и без воды."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Вопрос пользователя:\n{user_message}\n\n"
                        f"Черновой ответ ассистента:\n{draft_answer}\n\n"
                        "Проверь факты и переформулируй ответ, если нужно что-то уточнить."
                    ),
                },
            ]
            resp = await self.deepseek.ask(messages, stream=False)  # type: ignore[arg-type]
            assert isinstance(resp, str)
            return resp
        except Exception:
            logger.exception("LLM verification failed, fallback to draft answer")
            return draft_answer

    async def ask(
        self,
        user: User,
        messages: List[Dict[str, str]],
        *,
        stream: bool = True,
        web_priority: Optional[bool] = None,
    ) -> str | AsyncIterator[str]:
        """
        Основной вход: выбирает провайдера, при необходимости делает web-запрос
        + верификацию.
        """
        user_message = ""
        for m in reversed(messages):
            if m["role"] == "user":
                user_message = m["content"]
                break

        needs_web = web_priority if web_priority is not None else self._needs_web(
            user, user_message
        )
        complex_q = self._is_complex(user_message)

        # Web-first: Perplexity -> DeepSeek верификация.
        if needs_web:
            logger.info("Using Perplexity (web) for user_id=%s", user.id)
            web_resp = await self.perplexity.ask(messages, stream=False)
            assert isinstance(web_resp, str)
            final = await self._verify_answer(web_resp, user_message)
            return final

        # DeepSeek основной, при очень сложном запросе можно включить стриминг
        logger.info("Using DeepSeek for user_id=%s", user.id)
        if stream and complex_q:
            return await self.deepseek.ask(messages, stream=True)
        return await self.deepseek.ask(messages, stream=False)
