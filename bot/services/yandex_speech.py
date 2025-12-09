# bot/services/yandex_speech.py
from __future__ import annotations
import logging
from typing import Optional

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

STT_URL = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
TTS_URL = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"


def _check_speechkit_config() -> bool:
    return bool(settings.YANDEX_IAM_TOKEN and settings.YANDEX_FOLDER_ID)


async def recognize_speech(audio_bytes: bytes) -> Optional[str]:
    """
    STT: распознаёт речь (ogg/opus) через Yandex SpeechKit.
    """
    if not _check_speechkit_config():
        logger.warning("YANDEX_IAM_TOKEN / YANDEX_FOLDER_ID не заданы")
        return None

    headers = {
        "Authorization": f"Bearer {settings.YANDEX_IAM_TOKEN}",
    }
    params = {
        "lang": "ru-RU",
        "folderId": settings.YANDEX_FOLDER_ID,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(STT_URL, params=params, headers=headers, content=audio_bytes)
        resp.raise_for_status()
        data = resp.json()

    if data.get("error_code"):
        logger.error("SpeechKit STT error: %s", data)
        return None

    return data.get("result")


async def synthesize_speech(text: str) -> Optional[bytes]:
    """
    TTS: генерирует аудио по тексту.
    Возвращает байты OGG/OPUS.
    """
    if not _check_speechkit_config():
        logger.warning("YANDEX_IAM_TOKEN / YANDEX_FOLDER_ID не заданы")
        return None

    headers = {
        "Authorization": f"Bearer {settings.YANDEX_IAM_TOKEN}",
    }
    data = {
        "text": text,
        "lang": settings.YANDEX_TTS_LANG,
        "voice": settings.YANDEX_TTS_VOICE,
        "folderId": settings.YANDEX_FOLDER_ID,
        "format": "oggopus",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(TTS_URL, data=data, headers=headers)
        resp.raise_for_status()

    return resp.content
