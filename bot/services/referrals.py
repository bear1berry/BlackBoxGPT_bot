# bot/services/referrals.py
from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import User, Referral
from .crypto_utils import normalize_username  # если нужно, можно убрать


def build_referral_link(bot_username: str, ref_code: str) -> str:
    return f"https://t.me/{bot_username}?start={ref_code}"


async def get_or_create_user(session: AsyncSession, tg_user) -> User:
    stmt = select(User).where(User.tg_id == tg_user.id)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()

    if user is None:
        user = User(
            tg_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            language_code=tg_user.language_code,
            current_mode="universal",
            is_premium=False,
        )
        user.ensure_ref_code()
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return user


async def apply_referral(
    session: AsyncSession,
    new_user: User,
    ref_code: str | None,
) -> None:
    """
    Привязка реферала при первом запуске.
    """
    if not ref_code or new_user.referred_by_id is not None:
        return

    stmt = select(User).where(User.ref_code == ref_code)
    res = await session.execute(stmt)
    referrer = res.scalar_one_or_none()

    if referrer is None or referrer.id == new_user.id:
        return

    # Записываем связь + бонус можно начислять при оплате
    new_user.referred_by_id = referrer.id
    session.add(
        Referral(
            referrer_id=referrer.id,
            referral_user_id=new_user.id,
        )
    )
    await session.commit()
