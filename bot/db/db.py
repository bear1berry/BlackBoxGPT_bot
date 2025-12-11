from __future__ import annotations

from typing import Any, Iterable, Optional

import asyncpg

from ..config import settings


class Database:
    def __init__(self, dsn: str):
        self._dsn = dsn
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=5)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def fetchrow(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        assert self._pool is not None, "DB pool is not initialised"
        async with self._pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetch(self, query: str, *args: Any) -> Iterable[asyncpg.Record]:
        assert self._pool is not None, "DB pool is not initialised"
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def execute(self, query: str, *args: Any) -> str:
        assert self._pool is not None, "DB pool is not initialised"
        async with self._pool.acquire() as conn:
            return await conn.execute(query, *args)


db = Database(settings.db_dsn)
