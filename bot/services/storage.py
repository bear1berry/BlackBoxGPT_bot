from __future__ import annotations

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


async def set_current_mode(user_id: int, mode: Mode) -> None:
    await db.execute(
        "UPDATE users SET current_mode=$1 WHERE id=$2",
        mode.value,
        user_id,
    )


async def get_current_mode(user_row: asyncpg.Record) -> Mode:
    raw = user_row["current_mode"] if "current_mode" in user_row else "universal"
    try:
        return Mode(raw)
    except Exception:
        return Mode.UNIVERSAL
