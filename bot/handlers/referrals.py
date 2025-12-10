from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

router = Router(name="referrals")


@router.message(F.text == "👥 Рефералы")
async def referrals_menu(message: Message) -> None:
    text = (
        "<b>Реферальная система</b>\n\n"
        "🔗 Скоро здесь появится твоя реферальная ссылка:\n"
        "— приглашай друзей;\n"
        "— получай бонусы и продления подписки.\n\n"
        "Следи за обновлениями — функция уже в разработке."
    )
    await message.answer(text)
