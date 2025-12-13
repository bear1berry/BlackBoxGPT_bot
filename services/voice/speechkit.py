# services/voice/speechkit.py
from __future__ import annotations

import httpx


class SpeechkitError(RuntimeError):
    pass


async def speech_to_text_oggopus(
    audio_bytes: bytes,
    *,
    api_key: str,
    folder_id: str = "",
    lang: str = "ru-RU",
    topic: str = "general",
    timeout_sec: int = 25,
) -> str:
    """
    Telegram voice -> ogg/opus. SpeechKit умеет format=oggopus.
    """
    if not api_key:
        raise SpeechkitError("SPEECHKIT_API_KEY is empty")

    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
    params = {"lang": lang, "format": "oggopus"}
    if topic:
        params["topic"] = topic
    if folder_id:
        params["folderId"] = folder_id

    headers = {"Authorization": f"Api-Key {api_key}"}

    timeout = httpx.Timeout(timeout_sec, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, params=params, headers=headers, content=audio_bytes)

    try:
        data = r.json()
    except Exception as e:
        raise SpeechkitError(f"SpeechKit non-JSON response, status={r.status_code}") from e

    if r.status_code != 200:
        raise SpeechkitError(f"SpeechKit HTTP {r.status_code}: {data}")

    text = (data.get("result") or "").strip()
    if not text:
        raise SpeechkitError(f"SpeechKit empty result: {data}")

    return text
