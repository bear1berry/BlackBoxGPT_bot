from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.main import main_menu_keyboard
from bot.texts import build_main_menu_text, build_welcome_text

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    name = message.from_user.first_name if message.from_user else None
    await message.answer(
        build_welcome_text(name),
        reply_markup=main_menu_keyboard(),
    )
    await message.answer(build_main_menu_text(), reply_markup=main_menu_keyboard())
