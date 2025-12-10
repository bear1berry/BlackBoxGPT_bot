from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.config import settings
from bot.storage.models import Base

engine: AsyncEngine | None = None
async_session_maker: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    global engine, async_session_maker
    engine = create_async_engine(settings.postgres_dsn, echo=False, future=True)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if async_session_maker is None:
        raise RuntimeError("DB is not initialized")
    async with async_session_maker() as session:
        yield session
