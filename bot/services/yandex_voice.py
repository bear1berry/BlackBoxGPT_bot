from __future__ import annotations

import logging
from pathlib import Path
import uuid

import httpx

from bot.config import settings


logger = logging.getLogger(__name__)


async def tts_to_file(text: str, out_dir: Path) -> Path:
    """
    Синтез речи через Yandex Cloud TTS в ogg/opus файл.
    """
    if not settings.yandex_iam_token or not settings.yandex_folder_id:
        raise RuntimeError("Yandex TTS is not configured (yandex_iam_token / yandex_folder_id)")

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

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, data=data)
        resp.raise_for_status()
        audio_bytes = resp.content

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"tts_{uuid.uuid4().hex}.ogg"
    path.write_bytes(audio_bytes)
    return path


async def stt_from_file(path: Path) -> str:
    """
    Преобразование голоса в текст через Yandex Cloud STT.
    """
    if not settings.yandex_iam_token or not settings.yandex_folder_id:
        raise RuntimeError("Yandex STT is not configured (yandex_iam_token / yandex_folder_id)")

    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
    headers = {
        "Authorization": f"Bearer {settings.yandex_iam_token}",
    }
    params = {
        "folderId": settings.yandex_folder_id,
        "lang": settings.yandex_tts_lang,
    }

    audio_bytes = path.read_bytes()

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, params=params, content=audio_bytes)
        resp.raise_for_status()
        data = resp.json()

    if data.get("error_code"):
        logger.error("Yandex STT error: %s", data)
        raise RuntimeError(f"Yandex STT error: {data}")

    return str(data.get("result", "")).strip()
