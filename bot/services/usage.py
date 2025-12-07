from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import UsageStat
from .tariffs import TariffPlan


async def get_or_create_usage(
    session: AsyncSession,
    user_id: int,
    day: date | None = None,
) -> UsageStat:
    if day is None:
        day = date.today()

    stmt = select(UsageStat).where(
        UsageStat.user_id == user_id,
        UsageStat.day == day,
    )
    res = await session.execute(stmt)
    usage = res.scalar_one_or_none()
    if usage:
        return usage

    usage = UsageStat(user_id=user_id, day=day)
    session.add(usage)
    await session.flush()
    return usage


async def can_make_request(
    session: AsyncSession,
    user_id: int,
    plan: TariffPlan,
) -> bool:
    usage = await get_or_create_usage(session, user_id)
    return usage.requests_count < plan.daily_requests_limit


async def register_request(
    session: AsyncSession,
    user_id: int,
    plan: TariffPlan,
    tokens_prompt: int = 0,
    tokens_completion: int = 0,
) -> None:
    usage = await get_or_create_usage(session, user_id)
    usage.requests_count += 1
    usage.tokens_prompt += tokens_prompt
    usage.tokens_completion += tokens_completion
    await session.flush()
