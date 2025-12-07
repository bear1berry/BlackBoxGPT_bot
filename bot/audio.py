import logging
from pathlib import Path
from typing import Optional
import httpx
from .config import YANDEX_SPEECHKIT_API_KEY, YANDEX_FOLDER_ID, AUDIO_PROVIDER, DATA_DIR

log = logging.getLogger(__name__)
YANDEX_STT_URL = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
YANDEX_TTS_URL = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"

async def speech_to_text(file_path: Path) -> str:
    if AUDIO_PROVIDER != "yandex": return ""
    if not YANDEX_SPEECHKIT_API_KEY: return ""
    
    headers = {"Authorization": f"Api-Key {YANDEX_SPEECHKIT_API_KEY}"}
    params = {"lang": "ru-RU", "format": "oggopus", "folderId": YANDEX_FOLDER_ID}
    
    async with httpx.AsyncClient() as client:
        with file_path.open("rb") as f:
            resp = await client.post(YANDEX_STT_URL, params=params, content=f.read(), headers=headers)
    
    if resp.status_code != 200:
        log.error(f"STT Error: {resp.text}")
        return ""
    return resp.json().get("result", "")

async def text_to_speech(text: str) -> Optional[Path]:
    if AUDIO_PROVIDER != "yandex": return None
    if not YANDEX_SPEECHKIT_API_KEY: return None

    headers = {"Authorization": f"Api-Key {YANDEX_SPEECHKIT_API_KEY}"}
    data = {"text": text, "lang": "ru-RU", "voice": "alena", "format": "oggopus", "folderId": YANDEX_FOLDER_ID}
    
    out_path = DATA_DIR / "tmp_voice.ogg"
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(YANDEX_TTS_URL, data=data, headers=headers)
        
    if resp.status_code == 200:
        out_path.write_bytes(resp.content)
        return out_path
    return None
