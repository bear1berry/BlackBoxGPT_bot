from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards import main_menu_kb
from bot import texts
from bot.services import storage


router = Router(name="start-router")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    if user is None:
        return

    await storage.upsert_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    await message.answer(
        texts.main_welcome(user.first_name),
        reply_markup=main_menu_kb,
    )
