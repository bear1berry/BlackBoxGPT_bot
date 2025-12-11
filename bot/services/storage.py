from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional

import asyncpg
from aiogram.types import User as TgUser

from ..db.db import db
from .llm import Mode


def generate_referral_code(telegram_id: int) -> str:
    """Простая стабильная генерация реферального кода на основе telegram_id."""
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    n = telegram_id
    if n <= 0:
        return "0"
    result = []
    while n > 0:
        n, r = divmod(n, 36)
        result.append(alphabet[r])
    return "".join(reversed(result))


# ==== Пользователи ====

async def get_user_by_id(user_id: int) -> Optional[asyncpg.Record]:
    return await db.fetchrow("SELECT * FROM users WHERE id=$1", user_id)


async def get_user_by_telegram_id(telegram_id: int) -> Optional[asyncpg.Record]:
    return await db.fetchrow("SELECT * FROM users WHERE telegram_id=$1", telegram_id)


async def get_user_by_referral_code(ref_code: str) -> Optional[asyncpg.Record]:
    return await db.fetchrow("SELECT * FROM users WHERE referral_code=$1", ref_code)


async def ensure_user(tg_user: TgUser, ref_code: Optional[str] = None) -> asyncpg.Record:
    """
    Возвращает существующего пользователя или создаёт нового.
    Если передан реф-код и он валиден — привязывает referrer_id.
    """
    existing = await get_user_by_telegram_id(tg_user.id)
    if existing:
        return existing

    referrer_id: Optional[int] = None
    if ref_code:
        referrer = await get_user_by_referral_code(ref_code)
        if referrer:
            referrer_id = referrer["id"]

    referral_code = generate_referral_code(tg_user.id)

    row = await db.fetchrow(
        """
        INSERT INTO users (telegram_id, username, first_name, last_name, referrer_id, referral_code)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
        """,
        tg_user.id,
        tg_user.username,
        tg_user.first_name,
        tg_user.last_name,
        referrer_id,
        referral_code,
    )

    if referrer_id:
        await db.execute(
            """
            INSERT INTO referrals (referrer_id, referee_id, reward_type, reward_value)
            VALUES ($1, $2, $3, $4)
            """,
            referrer_id,
            row["id"],
            "days",
            0,
        )

    return row


async def set_user_mode(user_id: int, mode: Mode) -> None:
    await db.execute(
        "UPDATE users SET current_mode=$1, updated_at=NOW() WHERE id=$2",
        mode.value,
        user_id,
    )


async def get_user_mode(user_id: int) -> Mode:
    row = await db.fetchrow("SELECT current_mode FROM users WHERE id=$1", user_id)
    if not row or row["current_mode"] not in {m.value for m in Mode}:
        return Mode.UNIVERSAL
    return Mode(row["current_mode"])


# ==== Подписки и лимиты ====

async def get_active_subscription(user_id: int) -> Optional[asyncpg.Record]:
    return await db.fetchrow(
        """
        SELECT * FROM subscriptions
        WHERE user_id = $1
          AND is_active = TRUE
          AND expires_at > NOW()
        ORDER BY expires_at DESC
        LIMIT 1
        """,
        user_id,
    )


async def deactivate_expired_subscriptions() -> None:
    await db.execute(
        """
        UPDATE subscriptions
        SET is_active = FALSE
        WHERE is_active = TRUE
          AND expires_at <= NOW()
        """
    )
    await db.execute(
        """
        UPDATE users
        SET is_premium = FALSE, premium_until = NULL, updated_at = NOW()
        WHERE is_premium = TRUE AND (premium_until IS NULL OR premium_until <= NOW())
        """
    )


async def sync_user_premium_flag(user_id: int) -> asyncpg.Record:
    """
    Синхронизирует флаг is_premium / premium_until в users
    с таблицей subscriptions. Возвращает обновлённого юзера.
    """
    await deactivate_expired_subscriptions()
    active_sub = await get_active_subscription(user_id)

    if active_sub:
        await db.execute(
            """
            UPDATE users
            SET is_premium = TRUE,
                premium_until = $2,
                updated_at = NOW()
            WHERE id = $1
            """,
            user_id,
            active_sub["expires_at"],
        )
    else:
        await db.execute(
            """
            UPDATE users
            SET is_premium = FALSE,
                premium_until = NULL,
                updated_at = NOW()
            WHERE id = $1
            """,
            user_id,
        )

    row = await get_user_by_id(user_id)
    assert row is not None
    return row


async def create_subscription(
    user_id: int,
    plan_code: str,
    months: int,
    payment_id: int,
) -> asyncpg.Record:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=30 * months)

    # деактивируем старые активные подписки
    await db.execute(
        """
        UPDATE subscriptions
        SET is_active = FALSE
        WHERE user_id = $1 AND is_active = TRUE
        """,
        user_id,
    )

    sub = await db.fetchrow(
        """
        INSERT INTO subscriptions (user_id, plan_code, started_at, expires_at, is_active, payment_id)
        VALUES ($1, $2, $3, $4, TRUE, $5)
        RETURNING *
        """,
        user_id,
        plan_code,
        now,
        expires_at,
        payment_id,
    )

    # обновляем юзера
    await db.execute(
        """
        UPDATE users
        SET is_premium = TRUE,
            premium_until = $2,
            updated_at = NOW()
        WHERE id = $1
        """,
        user_id,
        expires_at,
    )

    return sub


# ==== Usage / лимиты ====

async def get_usage_today(user_id: int) -> int:
    today = date.today()
    row = await db.fetchrow(
        "SELECT request_count FROM usage_stats WHERE user_id=$1 AND day=$2",
        user_id,
        today,
    )
    if not row:
        return 0
    return int(row["request_count"])


async def increment_usage(user_id: int) -> int:
    today = date.today()
    row = await db.fetchrow(
        """
        INSERT INTO usage_stats (user_id, day, request_count)
        VALUES ($1, $2, 1)
        ON CONFLICT (user_id, day)
        DO UPDATE SET request_count = usage_stats.request_count + 1
        RETURNING request_count
        """,
        user_id,
        today,
    )
    return int(row["request_count"])
