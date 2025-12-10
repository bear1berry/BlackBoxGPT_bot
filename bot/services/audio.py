from __future__ import annotations

import logging

import httpx

from bot.config import settings

logger = logging.getLogger(__name__)


async def speech_to_text(audio_bytes: bytes) -> str:
    if not settings.yandex_iam_token or not settings.yandex_folder_id:
        raise RuntimeError("Yandex STT not configured")

    params = {
        "lang": settings.yandex_tts_lang,
        "folderId": settings.yandex_folder_id,
        "format": "oggopus",
    }
    headers = {
        "Authorization": f"Bearer {settings.yandex_iam_token}",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize",
            params=params,
            headers=headers,
            content=audio_bytes,
        )
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error("Yandex STT HTTP error: %s - %s", resp.status_code, resp.text)
            raise e

        data = resp.json()
        if data.get("error_code"):
            raise RuntimeError(f"Yandex STT error: {data}")

        return data["result"]
