from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from bot.keyboards import main_menu_kb
from bot.db.session import async_session_maker
from bot.services.profiles import get_or_create_user

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    async with async_session_maker() as session:
        tg = message.from_user
        assert tg is not None
        await get_or_create_user(
            session=session,
            tg_id=tg.id,
            username=tg.username,
            first_name=tg.first_name,
            last_name=tg.last_name,
            language_code=tg.language_code,
        )
        await session.commit()

    text = (
        "Добро пожаловать в BlackBox GPT — Universal AI Assistant.\n\n"
        "Здесь минимум интерфейса и максимум мозга.\n\n"
        "Выбери режим работы или просто задай свой первый вопрос."
    )
    await message.answer(text, reply_markup=main_menu_kb())


@router.callback_query(F.data == "menu:root")
@router.callback_query(F.data == "menu:back")
async def cb_main_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Главное меню BlackBox GPT.\n\n"
        "Выбери, что хочешь настроить, или просто пиши вопросы в чат.",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()
