from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery

from ..db.db import db
from ..services.storage import ensure_user
from ..services.llm import Mode
from ..keyboards.main_menu import modes_keyboard

router = Router()


async def _set_mode(user_id: int, mode: Mode) -> None:
    await db.execute(
        """
        UPDATE users
        SET current_mode = $2
        WHERE id = $1
        """,
        user_id,
        mode.value,
    )


@router.callback_query(F.data == "menu:modes")
async def open_modes_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🧠 <b>Режимы работы</b>\n\n"
        "Выбери режим, в котором я буду отвечать на твои запросы.",
        reply_markup=modes_keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == "mode:universal")
async def mode_universal(callback: CallbackQuery) -> None:
    user_row = await ensure_user(callback.from_user)
    await _set_mode(user_row["id"], Mode.UNIVERSAL)

    await callback.message.edit_text(
        "✅ <b>Универсальный режим активирован.</b>\n\n"
        "Теперь просто напиши мне запрос — я отвечу в нейтральном, "
        "универсальном стиле, без web-поиска.",
        reply_markup=modes_keyboard,
    )
    await callback.answer("Универсальный режим включен")


@router.callback_query(F.data == "mode:professional")
async def mode_professional(callback: CallbackQuery) -> None:
    user_row = await ensure_user(callback.from_user)
    await _set_mode(user_row["id"], Mode.PROFESSIONAL)

    await callback.message.edit_text(
        "💼 <b>Профессиональный режим активирован.</b>\n\n"
        "В этом режиме я подстраиваюсь под твои задачи: "
        "могу быть наставником, экспертом, а при необходимости "
        "подключаю web-поиск через Perplexity.\n\n"
        "Просто напиши свой запрос — я сам решу, когда достаточно "
        "мозгов, а когда нужен интернет.",
        reply_markup=modes_keyboard,
    )
    await callback.answer("Профессиональный режим включен")

