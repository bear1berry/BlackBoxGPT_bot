from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

from bot.config import Settings
from .modes import ChatMode

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Единая точка общения с LLM (DeepSeek).
    При желании сюда же легко добавляются другие модели/провайдеры.
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url="https://api.deepseek.com",
            timeout=60.0,
        )

    async def ask(
        self,
        *,
        mode: ChatMode,
        user_message: str,
        profile_summary: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Обычный запрос без стрима. Возвращает текст ответа.
        history — список сообщений вида {"role": "user"/"assistant", "content": "..."}
        """
        messages: List[Dict[str, str]] = []

        system_content = mode.system_prompt
        if profile_summary:
            system_content += (
                "\n\nКраткая информация о пользователе, учитывай её в ответах:\n"
                f"{profile_summary}"
            )

        messages.append({"role": "system", "content": system_content})

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})

        payload: Dict[str, Any] = {
            "model": self._settings.deepseek_model,
            "messages": messages,
            "stream": False,
        }

        try:
            resp = await self._client.post(
                "/chat/completions",
                headers={"Authorization": f"Bearer {self._settings.deepseek_api_key}"},
                json=payload,
            )
            resp.raise_for_status()
        except httpx.HTTPError:
            logger.exception("LLM request failed")
            raise

        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            logger.error("Unexpected LLM response format: %s", data)
            return "Сейчас я не смог получить ответ от модели. Попробуй ещё раз чуть позже."

    async def aclose(self) -> None:
        await self._client.aclose()
