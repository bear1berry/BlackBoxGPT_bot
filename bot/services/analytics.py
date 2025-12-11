from datetime import date

from ..db.db import db


def estimate_tokens(text: str) -> int:
    """Очень грубая оценка количества токенов по длине строки."""
    return max(1, len(text) // 4)


async def increment_usage(user_id: int, tokens_used: int) -> None:
    today = date.today()
    await db.execute(
        """
        INSERT INTO usage_stats (user_id, date, messages_count, tokens_used)
        VALUES ($1, $2, 1, $3)
        ON CONFLICT (user_id, date)
        DO UPDATE SET
            messages_count = usage_stats.messages_count + 1,
            tokens_used = usage_stats.tokens_used + EXCLUDED.tokens_used
        """,
        user_id,
        today,
        tokens_used,
    )
