from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from bot.storage.db import async_session_maker
from bot.storage.models import User, UserMode


class UserRepository:
    def __init__(self, session: AsyncSession | None = None) -> None:
        self._external_session = session

    async def _get_session(self) -> AsyncSession:
        if self._external_session is not None:
            return self._external_session
        if async_session_maker is None:
            raise RuntimeError("DB is not initialized")
        return async_session_maker()

    async def get_or_create(self, user_id: int, username: str | None) -> User:
        session = await self._get_session()
        stmt = select(User).where(User.telegram_id == user_id)
        res = await session.execute(stmt)
        user: User | None = res.scalar_one_or_none()

        if user:
            if username and user.username != username:
                user.username = username
                await session.commit()
            return user

        user = User(
            telegram_id=user_id,
            username=username,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def set_mode(self, user_id: int, username: str | None, mode: UserMode) -> None:
        session = await self._get_session()
        stmt = insert(User).values(
            telegram_id=user_id,
            username=username,
            mode=mode,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=[User.telegram_id],
            set_={
                "username": username,
                "mode": mode,
            },
        )
        await session.execute(stmt)
        await session.commit()

    async def count_users(self) -> int:
        session = await self._get_session()
        stmt = select(User)
        res = await session.execute(stmt)
        return len(res.scalars().all())
