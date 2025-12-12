from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Text

from bot.keyboards.common import get_back_keyboard

router = Router()

@router.message(Text("👤 Профиль"))
async def show_profile(message: Message):
    # Здесь должна быть логика получения данных пользователя из БД
    # Временно заглушка
    profile_text = (
        "👤 *Твой профиль*\n\n"
        "ID: 12345\n"
        "Режим: Универсальный\n"
        "Подписка: Нет\n"
        "Рефералов: 0\n"
        "Запросов сегодня: 0/50\n"
        "Токенов израсходовано: 0"
    )
    await message.answer(profile_text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
