from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Referral, User


def build_ref_code(tg_id: int) -> str:
    # простой вариант: префикс + tg_id
    return f"bb{tg_id}"


def parse_ref_code(code: str) -> int | None:
    if not code.startswith("bb"):
        return None
    try:
        return int(code[2:])
    except ValueError:
        return None


async def register_referral(
    session: AsyncSession,
    referrer_tg_id: int,
    invitee: User,
) -> Referral:
    stmt = select(User).where(User.tg_id == referrer_tg_id)
    res = await session.execute(stmt)
    referrer = res.scalar_one_or_none()
    if not referrer:
        referral = Referral(referrer_id=None, invitee_id=invitee.id, reward_granted=False)
        session.add(referral)
        await session.flush()
        return referral

    referral = Referral(
        referrer_id=referrer.id,
        invitee_id=invitee.id,
        reward_granted=False,
    )
    session.add(referral)
    await session.flush()
    return referral


async def get_referral_stats(session: AsyncSession, user: User) -> tuple[int, int]:
    """
    Возвращает: (кол-во приглашённых, кол-во с выданной наградой).
    """
    invited_stmt = select(Referral).where(Referral.referrer_id == user.id)
    res = await session.execute(invited_stmt)
    referrals = res.scalars().all()
    total = len(referrals)
    rewarded = sum(1 for r in referrals if r.reward_granted)
    return total, rewarded
