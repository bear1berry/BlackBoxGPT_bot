from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import settings
from bot.storage.repo import UserRepository

router = Router(name="admin")


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@router.message(Command("stats"))
async def bot_stats(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return

    repo = UserRepository()
    total_users = await repo.count_users()

    text = (
        "<b>Статистика бота</b>\n\n"
        f"Всего пользователей: <b>{total_users}</b>\n"
    )
    await message.answer(text)


@router.message(F.text == "debug_id")
async def debug_id(message: Message) -> None:
    if not is_admin(message.from_user.id):
        return
    await message.answer(f"Твой id: <code>{message.from_user.id}</code>")
