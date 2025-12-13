from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import aiosqlite


MIGRATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations(
  id TEXT PRIMARY KEY,
  applied_at INTEGER NOT NULL
);
"""


async def connect(db_path: str) -> aiosqlite.Connection:
    Path(os.path.dirname(db_path) or ".").mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(db_path)
    await db.execute("PRAGMA foreign_keys = ON;")
    await db.execute("PRAGMA journal_mode=WAL;")
    db.row_factory = aiosqlite.Row
    return db


async def apply_migrations(db: aiosqlite.Connection, migrations_dir: str) -> None:
    await db.execute(MIGRATIONS_TABLE_SQL)
    await db.commit()

    applied = set()
    async with db.execute("SELECT id FROM schema_migrations") as cur:
        async for row in cur:
            applied.add(row["id"])

    paths = sorted(Path(migrations_dir).glob("*.sql"))
    for path in paths:
        mid = path.name
        if mid in applied:
            continue

        sql = path.read_text(encoding="utf-8")
        await db.executescript(sql)
        await db.execute(
            "INSERT INTO schema_migrations(id, applied_at) VALUES(?, strftime('%s','now'))",
            (mid,),
        )
        await db.commit()
