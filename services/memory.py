from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Tuple

import aiosqlite


@dataclass
class MemoryMessage:
    role: str
    content: str
    ts: int


async def add(db: aiosqlite.Connection, user_id: int, role: str, content: str) -> None:
    await db.execute(
        "INSERT INTO memory(user_id, role, content, ts) VALUES(?, ?, ?, ?)",
        (user_id, role, content, int(time.time())),
    )
    await db.commit()


async def get_recent(db: aiosqlite.Connection, user_id: int, limit: int) -> List[MemoryMessage]:
    async with db.execute(
        "SELECT role, content, ts FROM memory WHERE user_id=? ORDER BY ts DESC LIMIT ?",
        (user_id, limit),
    ) as cur:
        rows = await cur.fetchall()
    msgs = [MemoryMessage(role=r["role"], content=r["content"], ts=r["ts"]) for r in rows]
    return list(reversed(msgs))
