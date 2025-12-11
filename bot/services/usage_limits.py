from __future__ import annotations

from datetime import datetime, timezone
from typing import Tuple, Optional

from ..db.db import db

# Лимиты по ТЗ
BASIC_TOTAL_LIMIT = 10          # Бесплатный план: всего 10 запросов
PREMIUM_DAILY_LIMIT = 100       # Premium: 100 запросов в сутки


async def _has_active_premium(user_id: int) -> bool:
    """
    Проверяем флаг is_premium + срок жизни подписки.
    Если подписка протухла — аккуратно её обнуляем.
    """
    row = await db.fetchrow(
        """
        SELECT is_premium, subscription_expires_at
        FROM users
        WHERE id = $1
        """,
        user_id,
    )
    if not row:
        return False

    is_premium: bool = row["is_premium"]
    expires_at: Optional[datetime] = row["subscription_expires_at"]

    now = datetime.now(timezone.utc)

    if is_premium and expires_at and expires_at > now:
        # Всё ок, активная подписка.
        return True

    # Если флаг ещё висит, но срок уже прошёл — подчистим.
    if is_premium:
        await db.execute(
            """
            UPDATE users
            SET is_premium = FALSE
            WHERE id = $1
            """,
            user_id,
        )

    return False


async def check_message_limit(user_id: int) -> Tuple[bool, Optional[str]]:
    """
    Главная функция для чата.

    Возвращает:
      (True, None)  — можно отвечать пользователю;
      (False, text) — лимит исчерпан, text нужно показать в сообщении.
    """
    # 1. Premium-пользователи
    if await _has_active_premium(user_id):
        row = await db.fetchrow(
            """
            SELECT messages_count
            FROM usage_stats
            WHERE user_id = $1 AND date = CURRENT_DATE
            """,
            user_id,
        )
        used_today = row["messages_count"] if row else 0

        if used_today >= PREMIUM_DAILY_LIMIT:
            return False, (
                "💎 У тебя активна подписка Premium, но на сегодня "
                "лимит в 100 запросов уже исчерпан.\n\n"
                "Попробуй завтра 👌"
            )

        return True, None

    # 2. Бесплатный план — считаем суммарно все запросы
    row = await db.fetchrow(
        """
        SELECT COALESCE(SUM(messages_count), 0) AS total_messages
        FROM usage_stats
        WHERE user_id = $1
        """,
        user_id,
    )
    total = row["total_messages"] if row else 0

    if total >= BASIC_TOTAL_LIMIT:
        return False, (
            "🔒 Бесплатный лимит в 10 запросов исчерпан.\n\n"
            "Оформи подписку 💎 <b>Premium</b> и получай до 100 запросов в день, "
            "плюс доступ к профессиональному режиму с web-поиском."
        )

    return True, None
