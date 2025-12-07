from __future__ import annotations

from datetime import date
from typing import Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, Referral
from bot.config import settings


SUBSCRIPTION_LIMITS: dict[str, int] = {
    "free": 30,
    "pro": 200,
    "vip": 1000,
}


def generate_ref_code(user_id: int) -> str:
    """Generate deterministic referral code from user ID."""
    return f"{user_id:x}"  # hex


async def get_or_create_user(session: AsyncSession, tg_user) -> User:
    result = await session.execute(
        select(User).where(User.id == tg_user.id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            ref_code=generate_ref_code(tg_user.id),
        )
        session.add(user)
        await session.flush()
    else:
        # lightweight update
        user.username = tg_user.username
        user.first_name = tg_user.first_name
        user.last_name = tg_user.last_name
    return user


async def apply_referral(session: AsyncSession, user: User, payload: str) -> None:
    """Apply referral by payload (value after 'ref_' in deep link)."""
    if user.referred_by:
        return  # already set

    if payload == user.ref_code:
        return  # self-ref is ignored

    result = await session.execute(
        select(User).where(User.ref_code == payload)
    )
    referrer = result.scalar_one_or_none()
    if referrer is None:
        return

    user.referred_by = payload
    referral = Referral(
        referrer_id=referrer.id,
        referred_user_id=user.id,
    )
    session.add(referral)


async def ensure_daily_quota(session: AsyncSession, user: User) -> Tuple[bool, str | None]:
    today = date.today()
    if user.last_usage_date != today:
        user.last_usage_date = today
        user.daily_usage = 0

    limit = SUBSCRIPTION_LIMITS.get(user.subscription_tier, SUBSCRIPTION_LIMITS["free"])
    if user.daily_usage >= limit:
        return False, (
            f"Ты достиг дневного лимита сообщений ({limit}) для тарифа "
            f"<b>{user.subscription_tier.upper()}</b>.\n\n"
            "Обнови подписку в разделе «💎 Подписка», чтобы получить больше запросов."
        )

    user.daily_usage += 1
    session.add(user)
    return True, None


def get_referral_link(user: User) -> str:
    return f"https://t.me/{settings.bot_username}?start=ref_{user.ref_code}"


async def set_mode(session: AsyncSession, user: User, mode: str) -> None:
    user.mode = mode
    session.add(user)


async def set_subscription_tier(
    session: AsyncSession, user: User, tier: str, *, days: int | None = None
) -> None:
    from datetime import datetime, timedelta, timezone

    tier = tier.lower()
    user.subscription_tier = tier

    if days is not None:
        now = datetime.now(timezone.utc)
        if user.subscription_until and user.subscription_until > now:
            user.subscription_until = user.subscription_until + timedelta(days=days)
        else:
            user.subscription_until = now + timedelta(days=days)

    session.add(user)
