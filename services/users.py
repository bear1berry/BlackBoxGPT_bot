from __future__ import annotations

import json
import time
import hashlib
from dataclasses import dataclass
from typing import Any, Optional

import aiosqlite


def _base36(n: int) -> str:
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    if n == 0:
        return "0"
    s = ""
    while n:
        n, r = divmod(n, 36)
        s = chars[r] + s
    return s


def make_ref_code(user_id: int, salt: str) -> str:
    core = _base36(user_id)
    chk = hashlib.sha1(f"{user_id}:{salt}".encode("utf-8")).hexdigest()[:4]
    return f"{core}{chk}"


@dataclass
class User:
    user_id: int
    created_at: int
    last_seen: int
    mode: str
    plan: str
    premium_until: int
    trial_used: int
    daily_used: int
    daily_date: str
    style: dict[str, Any]
    long_memory: str
    ref_code: str
    referrer_id: Optional[int]
    checkin_enabled: bool

    @property
    def is_premium(self) -> bool:
        return self.plan == "premium" and self.premium_until > int(time.time())


async def ensure_user(
    db: aiosqlite.Connection,
    user_id: int,
    *,
    referrer_id: Optional[int],
    ref_salt: str,
) -> User:
    u = await get_user(db, user_id)
    if u:
        await touch_user(db, user_id)
        return u

    now = int(time.time())
    ref_code = make_ref_code(user_id, ref_salt)
    await db.execute(
        """
        INSERT INTO users(user_id, created_at, last_seen, ref_code, referrer_id)
        VALUES(?, ?, ?, ?, ?)
        """,
        (user_id, now, now, ref_code, referrer_id),
    )
    await db.commit()
    return await get_user(db, user_id)  # type: ignore[return-value]


async def get_user(db: aiosqlite.Connection, user_id: int) -> Optional[User]:
    async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
        row = await cur.fetchone()
        if not row:
            return None
        style = {}
        try:
            style = json.loads(row["style_json"] or "{}")
        except Exception:
            style = {}
        return User(
            user_id=row["user_id"],
            created_at=row["created_at"],
            last_seen=row["last_seen"],
            mode=row["mode"],
            plan=row["plan"],
            premium_until=row["premium_until"],
            trial_used=row["trial_used"],
            daily_used=row["daily_used"],
            daily_date=row["daily_date"],
            style=style,
            long_memory=row["long_memory"] or "",
            ref_code=row["ref_code"],
            referrer_id=row["referrer_id"],
            checkin_enabled=bool(row["checkin_enabled"]),
        )


async def touch_user(db: aiosqlite.Connection, user_id: int) -> None:
    await db.execute("UPDATE users SET last_seen = strftime('%s','now') WHERE user_id = ?", (user_id,))
    await db.commit()


async def set_mode(db: aiosqlite.Connection, user_id: int, mode: str) -> None:
    await db.execute("UPDATE users SET mode = ? WHERE user_id = ?", (mode, user_id))
    await db.commit()


async def set_plan(db: aiosqlite.Connection, user_id: int, plan: str, premium_until: int = 0) -> None:
    await db.execute(
        "UPDATE users SET plan = ?, premium_until = ? WHERE user_id = ?",
        (plan, premium_until, user_id),
    )
    await db.commit()


async def add_premium(db: aiosqlite.Connection, user_id: int, seconds: int) -> int:
    now = int(time.time())
    u = await get_user(db, user_id)
    current = (u.premium_until if u else 0)
    base = current if current > now else now
    new_until = base + seconds
    await db.execute(
        "UPDATE users SET plan='premium', premium_until=? WHERE user_id=?",
        (new_until, user_id),
    )
    await db.commit()
    return new_until


async def toggle_checkin(db: aiosqlite.Connection, user_id: int) -> bool:
    u = await get_user(db, user_id)
    new_val = 0 if (u and u.checkin_enabled) else 1
    await db.execute("UPDATE users SET checkin_enabled=? WHERE user_id=?", (new_val, user_id))
    await db.commit()
    return bool(new_val)


async def bump_trial_used(db: aiosqlite.Connection, user_id: int, by: int = 1) -> None:
    await db.execute("UPDATE users SET trial_used = trial_used + ? WHERE user_id=?", (by, user_id))
    await db.commit()


async def set_daily_usage(db: aiosqlite.Connection, user_id: int, *, daily_used: int, daily_date: str) -> None:
    await db.execute(
        "UPDATE users SET daily_used=?, daily_date=? WHERE user_id=?",
        (daily_used, daily_date, user_id),
    )
    await db.commit()


async def set_style(db: aiosqlite.Connection, user_id: int, style: dict[str, Any]) -> None:
    await db.execute("UPDATE users SET style_json=? WHERE user_id=?", (json.dumps(style, ensure_ascii=False), user_id))
    await db.commit()


async def append_long_memory(db: aiosqlite.Connection, user_id: int, text: str) -> None:
    await db.execute("UPDATE users SET long_memory=? WHERE user_id=?", (text, user_id))
    await db.commit()


async def find_user_by_ref_code(db: aiosqlite.Connection, ref_code: str) -> Optional[int]:
    async with db.execute("SELECT user_id FROM users WHERE ref_code=?", (ref_code,)) as cur:
        row = await cur.fetchone()
        return int(row["user_id"]) if row else None
