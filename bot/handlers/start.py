from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.filters.command import CommandObject
from aiogram.types import Message

from bot.db.base import async_session_factory
from bot.keyboards import main_menu_kb
from services.user_service import get_or_create_user, apply_referral


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject | None = None) -> None:
    """
    Обрабатывает как обычный /start, так и deep-link /start ref_xxx.
    """
    args = command.args if command else None

    async with async_session_factory() as session:
        user = await get_or_create_user(session, message.from_user)

        # Если старт по реферальной ссылке
        if args and args.startswith("ref_"):
            await apply_referral(session, user, args.removeprefix("ref_"))

        await session.commit()

    text = (
        "🖤 <b>BlackBox GPT — Universal AI Assistant</b>\n\n"
        "Я — твой универсальный ИИ-ассистент. "
        "Выбирай режим работы через нижнее меню и просто пиши сообщения — "
        "остальное сделаю я."
    )

    await message.answer(text, reply_markup=main_menu_kb())
