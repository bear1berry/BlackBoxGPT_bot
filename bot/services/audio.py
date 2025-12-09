import logging
from typing import Optional

import httpx

from bot.config import settings

logger = logging.getLogger(__name__)


async def text_to_speech(text: str) -> Optional[bytes]:
    """Синтез речи через Yandex SpeechKit (TTS). Возвращает OGG OPUS или None при ошибке."""
    if not (settings.yandex_iam_token and settings.yandex_folder_id):
        logger.warning("Yandex TTS credentials are not configured")
        return None

    url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
    headers = {
        "Authorization": f"Bearer {settings.yandex_iam_token}",
    }
    data = {
        "text": text,
        "lang": settings.yandex_tts_lang,
        "voice": settings.yandex_tts_voice,
        "folderId": settings.yandex_folder_id,
        "format": "oggopus",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, data=data)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError:
            logger.exception("Yandex TTS HTTP error: %s - %s", resp.status_code, resp.text)
            return None

        return resp.content


async def speech_to_text(ogg_bytes: bytes) -> Optional[str]:
    """Распознавание речи через Yandex SpeechKit (STT). Возвращает текст или None."""
    if not (settings.yandex_iam_token and settings.yandex_folder_id):
        logger.warning("Yandex STT credentials are not configured")
        return None

    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
    headers = {
        "Authorization": f"Bearer {settings.yandex_iam_token}",
    }
    params = {
        "lang": settings.yandex_tts_lang,
        "folderId": settings.yandex_folder_id,
        "format": "oggopus",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, params=params, content=ogg_bytes)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError:
            logger.exception("Yandex STT HTTP error: %s - %s", resp.status_code, resp.text)
            return None

        try:
            data = resp.json()
        except ValueError:
            logger.error("Yandex STT returned non-JSON body: %r", resp.text)
            return None

        if "result" in data:
            return data["result"]

        logger.error("Yandex STT error payload: %s", data)
        return None
