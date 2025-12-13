# services/speechkit.py
from __future__ import annotations

from dataclasses import dataclass

import httpx


class SpeechKitError(RuntimeError):
    pass


@dataclass(slots=True)
class SpeechKitSTT:
    """
    Yandex SpeechKit STT (REST recognize).
    Telegram voice -> ogg/opus -> SpeechKit format=oggopus.
    """
    api_key: str = ""
    iam_token: str = ""
    folder_id: str = ""
    lang: str = "ru-RU"
    topic: str = "general"
    endpoint: str = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
    timeout_s: float = 45.0

    def is_enabled(self) -> bool:
        return bool(self.api_key or self.iam_token)

    def _auth_headers(self) -> dict[str, str]:
        if self.api_key:
            return {"Authorization": f"Api-Key {self.api_key}"}
        if self.iam_token:
            return {"Authorization": f"Bearer {self.iam_token}"}
        raise SpeechKitError("No auth: set SPEECHKIT_API_KEY or SPEECHKIT_IAM_TOKEN")

    async def recognize_oggopus(self, audio_bytes: bytes) -> str:
        if not self.is_enabled():
            raise SpeechKitError("SpeechKit disabled: no credentials")

        params: dict[str, str] = {
            "lang": self.lang,
            "topic": self.topic,
            "format": "oggopus",
        }
        if self.folder_id:
            params["folderId"] = self.folder_id

        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            r = await client.post(
                self.endpoint,
                params=params,
                headers=self._auth_headers(),
                content=audio_bytes,
            )

        if r.status_code != 200:
            raise SpeechKitError(f"HTTP {r.status_code}: {r.text[:400]}")

        data = r.json()
        text = (data.get("result") or "").strip()
        if not text:
            # иногда возвращает error_code/error_message
            if data.get("error_message") or data.get("error_code"):
                raise SpeechKitError(f"{data.get('error_code')} {data.get('error_message')}".strip())
        return text
