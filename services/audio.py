from __future__ import annotations

import logging
from typing import Optional

import httpx

from bot.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SpeechKitService:
    """
    Обработка голосовых сообщений через Yandex SpeechKit (STT).
    """

    async def transcribe_bytes(self, audio_bytes: bytes, *, lang: str = "ru-RU") -> Optional[str]:
        if not settings.speechkit_api_key:
            logger.error("SPEECHKIT_API_KEY is not configured")
            return None

        headers = {
            "Authorization": f"Api-Key {settings.speechkit_api_key}",
        }
        params = {
            "lang": lang,
            "format": "oggopus",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                str(settings.speechkit_stt_endpoint),
                params=params,
                headers=headers,
                content=audio_bytes,
            )
            if resp.status_code != 200:
                logger.error("SpeechKit STT failed: %s", resp.text)
                return None
            data = resp.json()
            return data.get("result")
