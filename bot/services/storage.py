from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ..config import get_settings
from ..db.db import db
from .payments_crypto import create_invoice
from .text_utils import plural_ru


async def get_or_create_user(telegram_id: int, username: str | None) -> dict:
    row = await db.fetchrow(
        "SELECT * FROM users WHERE telegram_id = $1",
        telegram_id,
    )
    if row:
        return dict(row)

    row = await db.fetchrow(
        """
        INSERT INTO users (telegram_id, username)
        VALUES ($1, $2)
        RETURNING *
        """,
        telegram_id,
        username,
    )
    return dict(row)


async def ensure_daily_limit(user_id: int) -> tuple[bool, str | None]:
    settings = get_settings()

    user = await db.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    if not user:
        return False, "Пользователь не найден."

    is_premium = bool(user.get("is_premium"))

    limit = settings.premium_daily_limit if is_premium else settings.free_daily_limit

    today = datetime.now(timezone.utc).date()

    row = await db.fetchrow(
        """
        SELECT * FROM daily_limits
        WHERE user_id = $1 AND day = $2
        """,
        user_id,
        today,
    )

    if not row:
        used = 0
    else:
        used = row["used_requests"]

    if used >= limit:
        if is_premium:
            return False, (
                "Ты достиг дневного лимита запросов по Premium.\n"
                "Лимит обновится завтра."
            )
        else:
            return False, (
                "Ты использовал все 10 бесплатных запросов на сегодня.\n\n"
                "Оформи Premium, чтобы получить 100 запросов в день 💎"
            )

    return True, None


async def mark_request_used(user_id: int) -> None:
    today = datetime.now(timezone.utc).date()

    await db.execute(
        """
        INSERT INTO daily_limits (user_id, day, used_requests)
        VALUES ($1, $2, 1)
        ON CONFLICT (user_id, day)
        DO UPDATE SET used_requests = daily_limits.used_requests + 1
        """,
        user_id,
        today,
    )


async def deactivate_expired_subscriptions() -> None:
    # Деактивируем просроченные подписки и снимаем флаг is_premium у пользователей.
    now = datetime.now(timezone.utc)

    rows = await db.fetch(
        """
        SELECT DISTINCT user_id
        FROM subscriptions
        WHERE is_active = TRUE
          AND premium_until IS NOT NULL
          AND premium_until < $1
        """,
        now,
    )
    if not rows:
        return

    user_ids = [r["user_id"] for r in rows]

    await db.execute(
        "UPDATE users SET is_premium = FALSE WHERE id = ANY($1::bigint[])",
        user_ids,
    )

    await db.execute(
        """
        UPDATE subscriptions
        SET is_active = FALSE
        WHERE user_id = ANY($1::bigint[])
          AND is_active = TRUE
        """,
        user_ids,
    )


async def sync_user_premium_flag(user_id: int) -> None:
    # Обновляет флаг is_premium у пользователя на основе активной подписки.
    await deactivate_expired_subscriptions()

    now = datetime.now(timezone.utc)
    row = await db.fetchrow(
        """
        SELECT *
        FROM subscriptions
        WHERE user_id = $1
          AND is_active = TRUE
          AND premium_until IS NOT NULL
          AND premium_until > $2
        ORDER BY premium_until DESC
        LIMIT 1
        """,
        user_id,
        now,
    )

    is_premium = row is not None

    await db.execute(
        "UPDATE users SET is_premium = $1 WHERE id = $2",
        is_premium,
        user_id,
    )


async def create_subscription_invoice(user_id: int, months: int) -> str | None:
    # Создаёт запись в subscriptions и выставляет счёт через Crypto Bot.
    settings = get_settings()
    if not settings.has_crypto:
        return None

    if months == 1:
        amount_usdt = 6.99
    elif months == 3:
        amount_usdt = 20.99
    elif months == 12:
        amount_usdt = 59.99
    else:
        amount_usdt = 6.99

    months_label = plural_ru(months, "месяц", "месяца", "месяцев")
    description = f"Подписка BlackBox GPT Premium на {months_label}"

    now = datetime.now(timezone.utc)
    premium_until = now + timedelta(days=30 * months)

    row = await db.fetchrow(
        """
        INSERT INTO subscriptions (user_id, tier, status, premium_until, is_active)
        VALUES ($1, $2, $3, $4, FALSE)
        RETURNING id
        """,
        user_id,
        "premium",
        "pending",
        premium_until,
    )
    sub_id = row["id"]

    payload = f"sub:{sub_id}"
    invoice_link = await create_invoice(
        amount_usdt=amount_usdt,
        description=description,
        payload=payload,
    )

    if not invoice_link:
        await db.execute(
            "UPDATE subscriptions SET status = $1 WHERE id = $2",
            "canceled",
            sub_id,
        )
        return None

    return invoice_link
