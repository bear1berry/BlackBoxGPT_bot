from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from services.llm.streaming import sse_content


class LLMError(RuntimeError):
    pass


@dataclass
class LLMResponse:
    content: str
    raw: dict[str, Any]


class OpenAICompatClient:
    def __init__(self, *, api_key: str, base_url: str, default_model: str, extra_headers: dict[str, str] | None = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                **(extra_headers or {}),
            },
            timeout=60.0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def chat(self, *, messages: list[dict[str, str]], model: str | None = None, temperature: float = 0.2, max_tokens: int = 1200, extra: dict[str, Any] | None = None) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if extra:
            payload.update(extra)

        resp = await self._client.post("/chat/completions", json=payload)
        if resp.status_code >= 400:
            raise LLMError(f"HTTP {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"] or ""
        except Exception:
            raise LLMError(f"Bad response: {json.dumps(data)[:500]}")
        return LLMResponse(content=content, raw=data)

    async def chat_stream(self, *, messages: list[dict[str, str]], model: str | None = None, temperature: float = 0.2, max_tokens: int = 1200, extra: dict[str, Any] | None = None) -> AsyncIterator[str]:
        payload: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if extra:
            payload.update(extra)

        async with self._client.stream("POST", "/chat/completions", json=payload) as resp:
            if resp.status_code >= 400:
                txt = await resp.aread()
                raise LLMError(f"HTTP {resp.status_code}: {txt[:500]}")
            async for chunk in sse_content(resp):
                yield chunk
