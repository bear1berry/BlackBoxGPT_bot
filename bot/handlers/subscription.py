from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

router = Router(name="subscription")


@router.message(F.text == "💎 Подписка")
async def subscription_menu(message: Message) -> None:
    text = (
        "<b>Подписка BlackBox GPT</b>\n\n"
        "🚀 Pro-доступ даёт:\n"
        "• Приоритет к мощным моделям;\n"
        "• Повышенные лимиты;\n"
        "• Быстрый отклик.\n\n"
        "Оплата сейчас доступна через Crypto Bot (USDT / TON).\n"
        "Скоро появится удобный личный кабинет прямо в боте."
    )
    await message.answer(text)
