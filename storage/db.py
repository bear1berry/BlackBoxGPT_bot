from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.config import get_settings

settings = get_settings()

async_engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

async_session_factory = async_sessionmaker(
    async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)
