from __future__ import annotations

import time
from dataclasses import dataclass

import aiosqlite


@dataclass
class RefStats:
    total: int
    premium: int


async def get_ref_stats(db: aiosqlite.Connection, user_id: int) -> RefStats:
    async with db.execute("SELECT COUNT(*) AS c FROM users WHERE referrer_id = ?", (user_id,)) as cur:
        total = int((await cur.fetchone())["c"])

    now = int(time.time())
    async with db.execute(
        "SELECT COUNT(*) AS c FROM users WHERE referrer_id = ? AND plan='premium' AND premium_until > ?",
        (user_id, now),
    ) as cur:
        premium = int((await cur.fetchone())["c"])

    return RefStats(total=total, premium=premium)
