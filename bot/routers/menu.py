from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from ..keyboards.main_menu import main_menu_keyboard, modes_keyboard
from ..services.llm import Mode
from ..services.storage import get_current_mode, set_current_mode

router = Router(name="menu")


@router.message(F.text == "🧠 Режимы")
async def show_modes(message: Message) -> None:
    user = message.from_user
    if not user:
        return

    # Читаем текущий режим из БД
    current_mode = await get_current_mode(user.id)
    kb = modes_keyboard(current=current_mode.value)

    text = (
        "🧠 *Режимы работы бота*\n\n"
        "• *Универсальный* — базовый режим DeepSeek для любых задач.\n"
        "• *Профессиональный* — усиленный режим: наставник + медицина, "
        "умеет подключать WEB-поиск через Perplexity.\n\n"
        "Просто выбери нужный режим ниже."
    )

    await message.answer(text, reply_markup=kb, parse_mode="Markdown")


@router.callback_query(F.data == "menu:back")
async def back_to_main_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Главное меню.",
        reply_markup=None,
    )
    await callback.message.answer(
        "Выбери действие в нижнем меню.",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mode:"))
async def switch_mode(callback: CallbackQuery) -> None:
    user = callback.from_user
    if not user:
        return

    _, mode_code = callback.data.split(":", maxsplit=1)
    if mode_code == "universal":
        mode = Mode.UNIVERSAL
    else:
        mode = Mode.PROFESSIONAL

    await set_current_mode(user.id, mode)

    kb = modes_keyboard(current=mode.value)

    if mode is Mode.UNIVERSAL:
        text = (
            "🧠 *Универсальный режим активирован.*\n\n"
            "DeepSeek без web-поиска. Подходит для большинства запросов."
        )
    else:
        text = (
            "🏆 *Профессиональный режим активирован.*\n\n"
            "Наставник + медицинский помощник. При запросах, где нужен интернет, "
            "бот автоматически подключит Perplexity и web-поиск."
        )

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer("Режим обновлён ✅")
