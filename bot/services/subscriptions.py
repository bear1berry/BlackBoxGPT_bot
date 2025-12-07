from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Subscription
from bot.services.tariffs import TariffPlan, resolve_user_plan


async def get_active_subscription(session: AsyncSession, user_id: int) -> Subscription | None:
    now = datetime.utcnow()
    stmt: Select[Subscription] = select(Subscription).where(
        Subscription.user_id == user_id,
        Subscription.status == "active",
        (Subscription.expires_at.is_(None)) | (Subscription.expires_at > now),
    )
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def get_user_plan_code(session: AsyncSession, user_id: int) -> str:
    sub = await get_active_subscription(session, user_id)
    if not sub:
        return "free"
    return sub.plan_code


async def grant_subscription(
    session: AsyncSession,
    user_id: int,
    plan_code: str,
    duration_days: int,
) -> Subscription:
    now = datetime.utcnow()
    expires_at = now + timedelta(days=duration_days)

    sub = Subscription(
        user_id=user_id,
        plan_code=plan_code,
        status="active",
        started_at=now,
        expires_at=expires_at,
    )
    session.add(sub)
    await session.flush()
    return sub


async def get_user_tariff(session: AsyncSession, user_id: int) -> TariffPlan:
    code = await get_user_plan_code(session, user_id)
    return resolve_user_plan(code)
