from __future__ import annotations

import time
from dataclasses import dataclass

import aiosqlite

from services import users as users_repo


def months_to_seconds(months: int) -> int:
    if months == 12:
        return 365 * 24 * 3600
    return months * 30 * 24 * 3600


async def activate_premium(db: aiosqlite.Connection, user_id: int, months: int) -> int:
    seconds = months_to_seconds(months)
    return await users_repo.add_premium(db, user_id, seconds)


async def downgrade_expired(db: aiosqlite.Connection) -> int:
    now = int(time.time())
    async with db.execute(
        "SELECT user_id FROM users WHERE plan='premium' AND premium_until <= ?",
        (now,),
    ) as cur:
        rows = await cur.fetchall()

    count = 0
    for r in rows:
        await users_repo.set_plan(db, int(r["user_id"]), "basic", 0)
        count += 1

    return count
