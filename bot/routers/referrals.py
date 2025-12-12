from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Text

from bot.keyboards.common import get_back_keyboard

router = Router()

@router.message(Text("👥 Рефералы"))
async def show_referrals(message: Message):
    # Заглушка: реферальная информация
    referrals_text = (
        "👥 *Реферальная программа*\n\n"
        "Приглашай друзей и получай бонусы!\n\n"
        "Твоя реферальная ссылка:\n"
        "`https://t.me/BlackBoxGPT_bot?start=ref12345`\n\n"
        "Приглашено пользователей: 0\n"
        "Из них Premium: 0\n"
        "Твой бонус: 0 дней подписки"
    )
    await message.answer(referrals_text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
