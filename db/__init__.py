from __future__ import annotations

import datetime as dt
import os
from typing import Optional, List, Tuple

from sqlalchemy import (
    String,
    DateTime,
    Date,
    Integer,
    Text,
    func,
)
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

_engine = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)

    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    subscription_tier: Mapped[str] = mapped_column(
        String(16), default="free", server_default="free"
    )
    current_mode: Mapped[str] = mapped_column(
        String(32), default="universal", server_default="universal"
    )

    # Optional profile fields (задел под расширение)
    profile_role: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    profile_goals: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)
    profile_language: Mapped[str] = mapped_column(
        String(16), default="ru", server_default="ru"
    )
    profile_style: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    last_message_date: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    daily_message_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )

    # Simple referral system
    ref_code: Mapped[str] = mapped_column(String(64), unique=True)
    referred_by_code: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True
    )
    referrals_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    role: Mapped[str] = mapped_column(String(16))  # 'user' / 'assistant'
    content: Mapped[str] = mapped_column(Text())
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


async def init_engine(db_url: str) -> None:
    """Initialize global engine and session factory."""
    global _engine, _session_factory
    if _engine is not None:
        return

    # Ensure directory for SQLite exists
    if db_url.startswith("sqlite"):
        path_part = db_url.split("///")[-1]
        dir_name = os.path.dirname(path_part)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

    _engine = create_async_engine(db_url, echo=False, future=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def create_all() -> None:
    """Create all tables if they do not exist."""
    if _engine is None:
        raise RuntimeError("DB engine is not initialized; call init_engine() first")

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError(
            "Session factory is not initialized; call init_engine() first"
        )
    return _session_factory


async def get_or_create_user(
    session: AsyncSession,
    *,
    telegram_id: int,
    username: Optional[str],
    first_name: Optional[str],
    last_name: Optional[str],
    referred_by_code: Optional[str] = None,
) -> User:
    from sqlalchemy import select, update

    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if user is None:
        # Generate simple referral code based on telegram_id
        ref_code = f"ref_{telegram_id}"

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            subscription_tier="free",
            current_mode="universal",
            ref_code=ref_code,
            referred_by_code=referred_by_code,
        )
        session.add(user)

        # If there is a referrer — increment their counter
        if referred_by_code:
            await session.execute(
                update(User)
                .where(User.ref_code == referred_by_code)
                .values(referrals_count=User.referrals_count + 1)
            )

        await session.commit()
        await session.refresh(user)
        return user

    # Update basic fields on every /start
    user.username = username
    user.first_name = first_name
    user.last_name = last_name
    await session.commit()
    return user


async def log_message(
    session: AsyncSession,
    *,
    user_id: int,
    role: str,
    content: str,
) -> None:
    msg = Message(user_id=user_id, role=role, content=content)
    session.add(msg)
    await session.commit()


async def get_last_dialog_history(
    session: AsyncSession,
    *,
    user_id: int,
    limit: int = 10,
) -> List[Tuple[str, str]]:
    """Return list of (role, content) pairs for the last `limit` messages."""
    from sqlalchemy import select

    result = await session.execute(
        select(Message)
        .where(Message.user_id == user_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    rows = list(result.scalars().all())
    rows.reverse()
    return [(m.role, m.content) for m in rows]


TIER_LIMITS = {
    "free": 30,
    "pro": 200,
    "vip": 1000,
}


def get_daily_limit(tier: str) -> int:
    return TIER_LIMITS.get(tier, TIER_LIMITS["free"])


async def increment_daily_counter(user: User) -> Tuple[bool, int, int]:
    """Increment daily message counter and check limit.

    Returns (allowed, used, limit).
    """
    today = dt.date.today()
    limit = get_daily_limit(user.subscription_tier)

    if user.last_message_date != today:
        user.last_message_date = today
        user.daily_message_count = 0

    if user.daily_message_count >= limit:
        return False, user.daily_message_count, limit

    user.daily_message_count += 1
    return True, user.daily_message_count, limit
