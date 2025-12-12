from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Text

from bot.keyboards.common import get_back_keyboard

router = Router()

@router.message(Text("💎 Подписка"))
async def show_subscription(message: Message):
    # Заглушка: список тарифов
    subscription_text = (
        "💎 *Подписка BlackBoxGPT*\n\n"
        "Бесплатный тариф:\n"
        "• 50 запросов в день\n"
        "• Только универсальный режим\n\n"
        "Премиум (1 месяц): 10 USDT\n"
        "• Безлимитные запросы\n"
        "• Все режимы\n"
        "• Приоритетная поддержка\n\n"
        "Выбери тариф для покупки:"
    )
    # В реальности здесь должны быть кнопки с тарифами, но по условиям Roadmap инлайн-кнопки не используются.
    # Можно использовать Reply-кнопки для выбора тарифа, но в данном примере оставим текст.
    await message.answer(subscription_text, reply_markup=get_back_keyboard(), parse_mode="Markdown")
