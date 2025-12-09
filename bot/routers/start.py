from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.keyboards.reply import main_menu_kb
from bot.texts import onboarding_text, main_menu_text
from bot.services.storage import ensure_user

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    if user is None:
        return

    await ensure_user(user.id, user.full_name)
    text = onboarding_text(user.full_name) + "\n\n" + main_menu_text()
    await message.answer(text, reply_markup=main_menu_kb())
