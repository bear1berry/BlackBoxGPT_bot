from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import Settings
from db import get_session_factory, User

router = Router(name="admin")


@router.message(Command("set_tier"))
async def cmd_set_tier(message: Message) -> None:
    settings = Settings()

    if message.from_user.id not in settings.admin_ids_list:
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Использование: <code>/set_tier user_id tier</code>")
        return

    try:
        target_user_id = int(parts[1])
    except ValueError:
        await message.answer("user_id должен быть числом (Telegram ID).")
        return

    tier = parts[2].strip().lower()
    if tier not in {"free", "pro", "vip"}:
        await message.answer("tier должен быть: free / pro / vip.")
        return

    session_factory = get_session_factory()
    async with session_factory() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(User).where(User.telegram_id == target_user_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            await message.answer("Пользователь с таким ID не найден.")
            return

        user.subscription_tier = tier
        await session.commit()

    await message.answer(
        f"Тариф пользователя <code>{target_user_id}</code> изменён на <b>{tier.upper()}</b>."
    )
