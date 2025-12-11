from aiogram import Router, F
from aiogram.types import Message

from ..keyboards import (
    main_menu_keyboard,
    modes_keyboard,
    subscription_keyboard,
    BACK_BUTTON_TEXT,
)
from ..services.storage import get_user_by_telegram_id, set_current_mode
from ..services.llm import Mode

router = Router(name="menu")


@router.message(F.text == "🧠 Режимы")
async def open_modes(message: Message) -> None:
    await message.answer(
        "🧠 **Режимы работы**\n\n"
        "Выбери режим, в котором я буду отвечать на твои запросы.",
        reply_markup=modes_keyboard(),
    )


@router.message(F.text == "💎 Подписка")
async def open_subscription(message: Message) -> None:
    await message.answer(
        "💎 **Подписка**\n\n"
        "Выбери срок подписки, чтобы получить повышенные лимиты и приоритет.",
        reply_markup=subscription_keyboard(),
    )


@router.message(F.text == BACK_BUTTON_TEXT)
async def back_to_main(message: Message) -> None:
    await message.answer(
        "⬅️ Возвращаю тебя в главное меню.",
        reply_markup=main_menu_keyboard(),
    )


async def _set_mode(message: Message, mode: Mode) -> None:
    user = await get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Не нашёл твой профиль, отправь /start.", reply_markup=main_menu_keyboard())
        return

    await set_current_mode(user["id"], mode)
    human = {
        Mode.UNIVERSAL: "🧠 Универсальный",
        Mode.PROFESSIONAL: "💼 Профессиональный",
        Mode.MENTOR: "🔥 Наставник",
        Mode.MEDICINE: "🩺 Медицина",
    }[mode]
    await message.answer(
        f"{human} режим активирован.\n\n"
        "Теперь просто напиши запрос — я буду отвечать в выбранном стиле.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(F.text == "🧠 Универсальный")
async def set_mode_universal(message: Message) -> None:
    await _set_mode(message, Mode.UNIVERSAL)


@router.message(F.text == "💼 Профессиональный")
async def set_mode_professional(message: Message) -> None:
    await _set_mode(message, Mode.PROFESSIONAL)


@router.message(F.text == "🔥 Наставник")
async def set_mode_mentor(message: Message) -> None:
    await _set_mode(message, Mode.MENTOR)


@router.message(F.text == "🩺 Медицина")
async def set_mode_medicine(message: Message) -> None:
    await _set_mode(message, Mode.MEDICINE)
