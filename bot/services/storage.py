import asyncio
import json
from pathlib import Path
from typing import Any, Dict


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_FILE = DATA_DIR / "users.json"

_LOCK = asyncio.Lock()


def _ensure_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("{}", encoding="utf-8")


def _read() -> Dict[str, Any]:
    _ensure_files()
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def _write(data: Dict[str, Any]) -> None:
    _ensure_files()
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def get_user(user_id: int) -> Dict[str, Any]:
    async with _LOCK:
        data = _read()
        return data.get(str(user_id), {})


async def ensure_user(user_id: int, full_name: str | None = None) -> Dict[str, Any]:
    async with _LOCK:
        data = _read()
        user = data.get(str(user_id))
        if not user:
            user = {
                "id": user_id,
                "full_name": full_name,
                "mode": "universal",
            }
            data[str(user_id)] = user
            _write(data)
        return user


async def set_user_mode(user_id: int, mode: str) -> None:
    async with _LOCK:
        data = _read()
        user = data.get(str(user_id)) or {"id": user_id}
        user["mode"] = mode
        data[str(user_id)] = user
        _write(data)


async def get_user_mode(user_id: int) -> str:
    async with _LOCK:
        data = _read()
        user = data.get(str(user_id))
        if not user:
            return "universal"
        return user.get("mode", "universal")
