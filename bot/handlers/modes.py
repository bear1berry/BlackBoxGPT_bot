from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards.main import main_menu_keyboard, modes_keyboard
from bot.storage.models import UserMode
from bot.storage.repo import UserRepository
from bot.texts import build_mode_updated_text

router = Router(name="modes")


@router.message(F.text == "🧠 Режимы")
async def modes_menu(message: Message) -> None:
    await message.answer(
        "Выбери режим работы ассистента:",
        reply_markup=modes_keyboard(),
    )


@router.callback_query(F.data.startswith("mode:"))
async def set_mode(callback: CallbackQuery) -> None:
    mode_code = callback.data.split(":", maxsplit=1)[1]
    if mode_code not in UserMode.__members__:
        await callback.answer("Неизвестный режим", show_alert=True)
        return

    repo = UserRepository()
    await repo.set_mode(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        mode=UserMode[mode_code],
    )

    await callback.message.edit_text(
        build_mode_updated_text(mode_code.lower()),
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer("Режим обновлён")
