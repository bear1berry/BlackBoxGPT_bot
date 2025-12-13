from __future__ import annotations

import json
import time
import secrets
from dataclasses import dataclass
from typing import List, Optional

import aiosqlite


@dataclass
class ContinueState:
    token: str
    user_id: int
    parts: List[str]
    idx: int
    created_at: int


def new_token() -> str:
    return secrets.token_urlsafe(16)


async def create(db: aiosqlite.Connection, user_id: int, parts: list[str]) -> ContinueState:
    token = new_token()
    await db.execute(
        "INSERT INTO continues(token, user_id, parts_json, idx, created_at) VALUES(?, ?, ?, 0, ?)",
        (token, user_id, json.dumps(parts, ensure_ascii=False), int(time.time())),
    )
    await db.commit()
    return ContinueState(token=token, user_id=user_id, parts=parts, idx=0, created_at=int(time.time()))


async def get(db: aiosqlite.Connection, token: str) -> Optional[ContinueState]:
    async with db.execute("SELECT * FROM continues WHERE token=?", (token,)) as cur:
        r = await cur.fetchone()
    if not r:
        return None
    try:
        parts = json.loads(r["parts_json"] or "[]")
    except Exception:
        parts = []
    return ContinueState(token=r["token"], user_id=r["user_id"], parts=parts, idx=r["idx"], created_at=r["created_at"])


async def bump(db: aiosqlite.Connection, token: str) -> None:
    await db.execute("UPDATE continues SET idx = idx + 1 WHERE token=?", (token,))
    await db.commit()


async def delete(db: aiosqlite.Connection, token: str) -> None:
    await db.execute("DELETE FROM continues WHERE token=?", (token,))
    await db.commit()
