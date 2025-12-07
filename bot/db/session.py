from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bot.config import Settings
from .base import Base

_settings = Settings()


def _make_async_url(url: str) -> str:
    """
    Преобразует postgresql:// в postgresql+asyncpg://
    чтобы одна и та же строка работала и для psql, и для SQLAlchemy async.
    """
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


ASYNC_DATABASE_URL = _make_async_url(_settings.database_url)

engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=_settings.environment == "development",
)

async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        yield session


async def init_models() -> None:
    """Создание таблиц из моделей (если без миграций)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
