from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from sqlalchemy import select

from bot.config import settings
from bot.db.base import async_session_factory
from bot.db.models import User
from services.user_service import set_subscription_tier


router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@router.message(Command("set_tier"))
async def cmd_set_tier(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: <code>/set_tier user_id tier</code>")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await message.answer("user_id должен быть числом.")
        return

    tier = parts[2].lower()
    if tier not in ("free", "pro", "vip"):
        await message.answer("Тариф должен быть: free, pro или vip.")
        return

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.id == target_id))
        user = result.scalar_one_or_none()
        if user is None:
            await message.answer("Пользователь не найден.")
            return

        await set_subscription_tier(session, user, tier)
        await session.commit()

    await message.answer(
        f"Тариф пользователя <code>{target_id}</code> обновлён на <b>{tier}</b>."
    )
