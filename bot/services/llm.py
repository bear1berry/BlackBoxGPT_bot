from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, Iterable, List, Literal, Optional

import httpx

from bot.config import settings


BACKEND = Literal["perplexity", "deepseek"]


TEMP_ERROR_MESSAGE = (
    "⚠️ <b>Временная ошибка модели</b>.\n"
    "Попробуй ещё раз чуть позже."
)

FATAL_ERROR_MESSAGE = (
    "❌ <b>Ошибка при обращении к модели</b>.\n"
    "Я уже запомнил это и передам разработчику."
)


@dataclass
class LlmResponse:
    text: str
    model: str
    backend: BACKEND
    finish_reason: Optional[str] = None


def _normalize_messages(
    prompt: Optional[str] = None,
    *,
    messages: Optional[Iterable[Dict[str, str]]] = None,
    system_prompt: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Приводим запрос к формату сообщений OpenAI-стиля."""
    result: List[Dict[str, str]] = []

    if system_prompt:
        result.append({"role": "system", "content": system_prompt})

    if messages:
        result.extend(messages)

    if prompt is not None:
        result.append({"role": "user", "content": prompt})

    if not result:
        raise ValueError("Нужен либо prompt, либо messages")

    return result


class LlmService:
    def __init__(self) -> None:
        self.perplexity_base = settings.perplexity_api_base
        self.perplexity_key = settings.perplexity_api_key
        self.perplexity_default_model = settings.perplexity_default_model

        self.deepseek_base = settings.deepseek_api_base
        self.deepseek_key = settings.deepseek_api_key
        self.deepseek_default_model = settings.deepseek_default_model

        self.timeout = settings.llm_timeout_sec

    def _select_backend(self, mode: str | None, backend: Optional[BACKEND]) -> BACKEND:
        """Логика выбора бэкенда."""
        if backend is not None:
            return backend

        # Например, Наставник — в DeepSeek, остальное — в Perplexity
        if mode in {"mentor"}:
            return "deepseek"

        return "perplexity"

    def _model_for_mode(self, backend: BACKEND, mode: Optional[str]) -> str:
        if backend == "perplexity":
            mapping: Dict[str, str] = getattr(
                settings,
                "perplexity_mode_models",
                {},
            )
            if mode and mode in mapping:
                return mapping[mode]
            return self.perplexity_default_model

        mapping: Dict[str, str] = getattr(
            settings,
            "deepseek_mode_models",
            {},
        )
        if mode and mode in mapping:
            return mapping[mode]
        return self.deepseek_default_model

    async def _ask_perplexity_stream(
        self,
        *,
        messages: List[Dict[str, str]],
        model: str,
        use_web: bool,
    ) -> AsyncIterator[str]:
        """Стрим из Perplexity (OpenAI-совместимый /v1/chat/completions)."""
        headers = {
            "Authorization": f"Bearer {self.perplexity_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
        }

        # Примерно даём движку возможность ходить в веб
        if use_web:
            payload["search_domain_filter"] = ["perplexity.ai"]

        async with httpx.AsyncClient(
            base_url=self.perplexity_base,
            timeout=self.timeout,
        ) as client:
            async with client.stream("POST", "/v1/chat/completions", json=payload) as r:
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        line = line[len("data: ") :]
                    if line.strip() == "[DONE]":
                        break
                    try:
                        data = httpx.Response(
                            status_code=200, content=line.encode("utf-8")
                        ).json()
                    except Exception:
                        continue

                    for choice in data.get("choices", []):
                        delta = choice.get("delta") or {}
                        content = delta.get("content")
                        if content:
                            yield content

    async def _ask_deepseek_stream(
        self,
        *,
        messages: List[Dict[str, str]],
        model: str,
    ) -> AsyncIterator[str]:
        """Стрим из DeepSeek /chat/completions."""
        headers = {
            "Authorization": f"Bearer {self.deepseek_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
        }

        async with httpx.AsyncClient(
            base_url=self.deepseek_base,
            timeout=self.timeout,
        ) as client:
            async with client.stream("POST", "/chat/completions", json=payload) as r:
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data: "):
                        line = line[len("data: ") :]
                    if line.strip() == "[DONE]":
                        break
                    try:
                        data = httpx.Response(
                            status_code=200, content=line.encode("utf-8")
                        ).json()
                    except Exception:
                        continue

                    for choice in data.get("choices", []):
                        delta = choice.get("delta") or {}
                        content = delta.get("content")
                        if content:
                            yield content

    async def ask_stream(
        self,
        *,
        prompt: Optional[str] = None,
        messages: Optional[Iterable[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        mode: Optional[str] = None,
        backend: Optional[BACKEND] = None,
        use_web: bool = True,
        **_: Any,
    ) -> AsyncIterator[str]:
        """Главный метод: отдаёт части ответа по мере генерации."""
        merged_messages = _normalize_messages(
            prompt=prompt,
            messages=messages,
            system_prompt=system_prompt,
        )

        backend_name = self._select_backend(mode, backend)
        model = self._model_for_mode(backend_name, mode)

        try:
            if backend_name == "perplexity":
                async for chunk in self._ask_perplexity_stream(
                    messages=merged_messages,
                    model=model,
                    use_web=use_web,
                ):
                    yield chunk
            else:
                async for chunk in self._ask_deepseek_stream(
                    messages=merged_messages,
                    model=model,
                ):
                    yield chunk
        except asyncio.TimeoutError:
            # Временная ошибка / таймаут
            yield TEMP_ERROR_MESSAGE
        except Exception:
            # Любая другая ошибка
            yield FATAL_ERROR_MESSAGE

    async def ask(
        self,
        *,
        prompt: Optional[str] = None,
        messages: Optional[Iterable[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        mode: Optional[str] = None,
        backend: Optional[BACKEND] = None,
        use_web: bool = True,
        **kwargs: Any,
    ) -> LlmResponse:
        """Нестримающая версия — просто строка."""
        parts: List[str] = []
        async for chunk in self.ask_stream(
            prompt=prompt,
            messages=messages,
            system_prompt=system_prompt,
            mode=mode,
            backend=backend,
            use_web=use_web,
            **kwargs,
        ):
            parts.append(chunk)

        backend_name = self._select_backend(mode, backend)
        model = self._model_for_mode(backend_name, mode)

        return LlmResponse(
            text="".join(parts),
            model=model,
            backend=backend_name,
        )


_llm_service = LlmService()


async def ask_llm_stream(
    prompt: Optional[str] = None,
    *,
    messages: Optional[Iterable[Dict[str, str]]] = None,
    system_prompt: Optional[str] = None,
    mode: Optional[str] = None,
    backend: Optional[BACKEND] = None,
    use_web: bool = True,
    **kwargs: Any,
) -> AsyncIterator[str]:
    """Функция-обёртка для совместимости со старым кодом."""
    async for chunk in _llm_service.ask_stream(
        prompt=prompt,
        messages=messages,
        system_prompt=system_prompt,
        mode=mode,
        backend=backend,
        use_web=use_web,
        **kwargs,
    ):
        yield chunk


async def ask_llm(
    prompt: Optional[str] = None,
    *,
    messages: Optional[Iterable[Dict[str, str]]] = None,
    system_prompt: Optional[str] = None,
    mode: Optional[str] = None,
    backend: Optional[BACKEND] = None,
    use_web: bool = True,
    **kwargs: Any,
) -> str:
    """Просто вернуть строку ответа."""
    resp = await _llm_service.ask(
        prompt=prompt,
        messages=messages,
        system_prompt=system_prompt,
        mode=mode,
        backend=backend,
        use_web=use_web,
        **kwargs,
    )
    return resp.text


def get_llm_service() -> LlmService:
    return _llm_service
