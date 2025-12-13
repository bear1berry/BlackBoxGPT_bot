# services/speechkit.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx


class SpeechKitError(RuntimeError):
    pass


@dataclass(frozen=True)
class SpeechKitSTTResult:
    text: str
    raw: dict[str, Any]


def _auth_headers(settings) -> dict[str, str]:
    """
    Поддерживаем оба варианта:
    - IAM токен: Authorization: Bearer <token>
    - API Key:  Authorization: Api-Key <key>
    """
    iam = getattr(settings, "speechkit_iam_token", "") or ""
    api_key = getattr(settings, "speechkit_api_key", "") or ""
    if iam.strip():
        return {"Authorization": f"Bearer {iam.strip()}"}
    if api_key.strip():
        return {"Authorization": f"Api-Key {api_key.strip()}"}
    return {}


async def recognize_oggopus(audio_bytes: bytes, *, settings) -> SpeechKitSTTResult:
    """
    Telegram voice note = OGG/OPUS -> SpeechKit понимает format=oggopus.
    """
    headers = _auth_headers(settings)
    if not headers:
        raise SpeechKitError("SpeechKit не настроен: нет SPEECHKIT_API_KEY или SPEECHKIT_IAM_TOKEN")

    folder_id = (getattr(settings, "speechkit_folder_id", "") or "").strip()
    lang = (getattr(settings, "speechkit_lang", "ru-RU") or "ru-RU").strip()
    topic = (getattr(settings, "speechkit_topic", "general") or "general").strip()
    timeout_sec = int(getattr(settings, "speechkit_timeout_sec", 25) or 25)

    params = {
        "lang": lang,
        "format": "oggopus",
        "topic": topic,  # general | maps | ... (можно оставить general)
    }
    if folder_id:
        params["folderId"] = folder_id

    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"

    timeout = httpx.Timeout(timeout_sec, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, params=params, headers=headers, content=audio_bytes)

    try:
        data = r.json()
    except Exception:
        raise SpeechKitError(f"SpeechKit вернул не-JSON (HTTP {r.status_code})")

    if r.status_code != 200:
        msg = data.get("message") or data.get("error_message") or str(data)
        raise SpeechKitError(f"SpeechKit error HTTP {r.status_code}: {msg}")

    text = (data.get("result") or "").strip()
    if not text:
        raise SpeechKitError("SpeechKit вернул пустой результат распознавания")

    return SpeechKitSTTResult(text=text, raw=data)
