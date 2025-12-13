from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import aiosqlite

from services import users as users_repo


@dataclass
class LimitResult:
    ok: bool
    reason: str | None  # 'trial' | 'daily' | None


def today_str(tz: str) -> str:
    return datetime.now(ZoneInfo(tz)).strftime("%Y-%m-%d")


async def ensure_plan_fresh(db: aiosqlite.Connection, user_id: int) -> users_repo.User:
    u = await users_repo.get_user(db, user_id)
    if not u:
        raise RuntimeError("User not found")

    now = int(time.time())
    if u.plan == "premium" and u.premium_until <= now:
        # auto-downgrade
        await users_repo.set_plan(db, user_id, "basic", 0)
        u = await users_repo.get_user(db, user_id)
        assert u is not None
    return u


async def peek(
    db: aiosqlite.Connection,
    user_id: int,
    *,
    timezone: str,
    basic_trial_limit: int,
    premium_daily_limit: int,
    is_admin: bool = False,
) -> LimitResult:
    """
    Проверка лимитов БЕЗ списания.
    Удобно для дорогих операций (например, SpeechKit STT),
    чтобы не тратить деньги, если пользователь уже упёрся в лимит.
    """
    if is_admin:
        return LimitResult(ok=True, reason=None)

    u = await ensure_plan_fresh(db, user_id)
    now = int(time.time())

    # premium daily limit
    if u.plan == "premium" and u.premium_until > now:
        t = today_str(timezone)
        daily_used = 0 if u.daily_date != t else u.daily_used
        if daily_used >= premium_daily_limit:
            return LimitResult(ok=False, reason="daily")
        return LimitResult(ok=True, reason=None)

    # basic trial limit (total cap)
    if u.trial_used >= basic_trial_limit:
        return LimitResult(ok=False, reason="trial")

    return LimitResult(ok=True, reason=None)


async def consume(
    db: aiosqlite.Connection,
    user_id: int,
    *,
    timezone: str,
    basic_trial_limit: int,
    premium_daily_limit: int,
    is_admin: bool = False,
) -> LimitResult:
    """
    Списывает лимит.
    """
    if is_admin:
        # Админ тестирует продукт — лимиты не режем.
        return LimitResult(ok=True, reason=None)

    u = await ensure_plan_fresh(db, user_id)
    now = int(time.time())

    # premium daily limit
    if u.plan == "premium" and u.premium_until > now:
        t = today_str(timezone)
        if u.daily_date != t:
            await users_repo.set_daily_usage(db, user_id, daily_used=0, daily_date=t)
            u.daily_used = 0
            u.daily_date = t

        if u.daily_used >= premium_daily_limit:
            return LimitResult(ok=False, reason="daily")

        await users_repo.set_daily_usage(db, user_id, daily_used=u.daily_used + 1, daily_date=t)
        return LimitResult(ok=True, reason=None)

    # basic trial (total cap)
    if u.trial_used >= basic_trial_limit:
        return LimitResult(ok=False, reason="trial")

    await users_repo.bump_trial_used(db, user_id, 1)
    return LimitResult(ok=True, reason=None)
