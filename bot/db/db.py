from __future__ import annotations

import asyncpg
from typing import Optional, Any

_pool: Optional[asyncpg.Pool] = None


async def create_db_pool(dsn: str) -> None:
    global _pool
    _pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)


async def close_db_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def init_db() -> None:
    # Таблицы создаются миграциями, здесь можно сделать лёгкий healthcheck
    async with _pool.acquire() as conn:  # type: ignore[arg-type]
        await conn.execute("SELECT 1")


class Database:
    async def fetchrow(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        assert _pool is not None, "DB pool is not initialised"
        async with _pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]:
        assert _pool is not None, "DB pool is not initialised"
        async with _pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            return list(rows)

    async def execute(self, query: str, *args: Any) -> str:
        assert _pool is not None, "DB pool is not initialised"
        async with _pool.acquire() as conn:
            return await conn.execute(query, *args)


db = Database()
