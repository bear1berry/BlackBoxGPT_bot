from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from bot.storage.repo import UserRepository

router = Router(name="profile")


@router.message(F.text == "👤 Профиль")
async def profile_menu(message: Message) -> None:
    repo = UserRepository()
    user = await repo.get_or_create(
        user_id=message.from_user.id,
        username=message.from_user.username,
    )

    text = (
        "<b>Твой профиль</b>\n\n"
        f"ID: <code>{user.telegram_id}</code>\n"
        f"Username: @{user.username if user.username else '—'}\n"
        f"Режим: <b>{user.mode.value}</b>\n"
        f"Статус подписки: <b>{user.subscription_tier}</b>\n"
    )
    await message.answer(text)
