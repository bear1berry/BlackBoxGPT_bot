from __future__ import annotations

from datetime import date
from typing import List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import DialogMessage, User

LIMITS = {
    "free": 30,
    "pro": 200,
    "vip": 1000,
}


def get_daily_limit(tier: str) -> int:
    return LIMITS.get(tier.lower(), LIMITS["free"])


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
    language_code: str | None,
    referred_by_code: str | None = None,
) -> User:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if user:
        return user

    ref_code = f"ref_{telegram_id}"

    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        language_code=language_code,
        current_mode="universal",
        subscription_tier="free",
        daily_message_count=0,
        last_message_date=None,
        ref_code=ref_code,
        referred_by_code=referred_by_code,
        referrals_count=0,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def increment_daily_counter(
    session: AsyncSession,
    user: User,
) -> Tuple[bool, int, int]:
    today = date.today()
    limit = get_daily_limit(user.subscription_tier)

    if user.last_message_date != today:
        user.last_message_date = today
        user.daily_message_count = 0

    user.daily_message_count += 1
    used = user.daily_message_count

    await session.commit()
    return used <= limit, used, limit


async def log_message(
    session: AsyncSession,
    user_id: int,
    role: str,
    content: str,
) -> None:
    msg = DialogMessage(
        user_id=user_id,
        role=role,
        content=content,
    )
    session.add(msg)
    await session.commit()


async def get_last_dialog_history(
    session: AsyncSession,
    user_id: int,
    limit: int = 10,
) -> List[Tuple[str, str]]:
    stmt = (
        select(DialogMessage)
        .where(DialogMessage.user_id == user_id)
        .order_by(DialogMessage.id.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = list(result.scalars().all())
    rows.reverse()
    return [(m.role, m.content) for m in rows]
