from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery

from sqlalchemy import select

from bot.db.models import User
from bot.db.session import async_session_maker
from bot.keyboards import modes_menu_kb
from bot.services.modes import get_mode

router = Router(name="modes")


@router.callback_query(F.data == "menu:modes")
async def cb_show_modes(callback: CallbackQuery) -> None:
    tg = callback.from_user
    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == tg.id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

    current_mode = user.current_mode if user else "universal"
    await callback.message.edit_text(
        "Выбери режим работы ассистента:",
        reply_markup=modes_menu_kb(current_mode=current_mode),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mode:"))
async def cb_set_mode(callback: CallbackQuery) -> None:
    mode_key = callback.data.split(":", 1)[1]
    mode = get_mode(mode_key)

    tg = callback.from_user
    async with async_session_maker() as session:
        stmt = select(User).where(User.tg_id == tg.id)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        if user:
            user.current_mode = mode.key
            await session.commit()

    await callback.message.edit_text(
        f"Режим переключён на {mode.emoji} <b>{mode.title}</b>.\n\n"
        f"{mode.description}",
        reply_markup=modes_menu_kb(current_mode=mode.key),
    )
    await callback.answer("Режим обновлён.")
