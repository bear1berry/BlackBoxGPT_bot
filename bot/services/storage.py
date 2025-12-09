from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"


def _load_users() -> Dict[str, Any]:
    if not USERS_FILE.exists():
        return {}
    try:
        raw = USERS_FILE.read_text(encoding="utf-8")
        return json.loads(raw) if raw else {}
    except Exception:
        # В крайнем случае начинаем с пустой БД
        return {}


def _save_users(data: Dict[str, Any]) -> None:
    USERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


async def get_user(user_id: int) -> Dict[str, Any]:
    data = _load_users()
    return data.get(str(user_id), {})


async def upsert_user(user_id: int, **fields: Any) -> Dict[str, Any]:
    data = _load_users()
    user = data.get(str(user_id), {})
    user.update(fields)
    data[str(user_id)] = user
    _save_users(data)
    return user


async def get_user_mode(user_id: int) -> str:
    user = await get_user(user_id)
    return user.get("mode", "universal")


async def set_user_mode(user_id: int, mode: str) -> None:
    await upsert_user(user_id, mode=mode)


async def get_profile(user_id: int) -> Dict[str, Any]:
    user = await get_user(user_id)
    return user.get("profile", {})


async def set_profile(user_id: int, profile: Dict[str, Any]) -> None:
    await upsert_user(user_id, profile=profile)


async def get_referral_code(user_id: int) -> str:
    """
    Очень лёгкая заглушка: реф-код = 'BB' + user_id.
    """
    user = await get_user(user_id)
    code = user.get("ref_code")
    if not code:
        code = f"BB{user_id}"
        await upsert_user(user_id, ref_code=code)
    return code
