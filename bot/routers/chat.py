from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from ..config import settings
from ..keyboards.main_menu import subscription_keyboard
from ..services.llm import Mode, ask_llm
from ..services.payments_crypto import refresh_user_payments_and_subscriptions
from ..services.storage import (
    ensure_user,
    get_usage_today,
    increment_usage,
    get_user_mode,
    sync_user_premium_flag,
)

router = Router()


@router.message(F.text & ~F.text.in_(
    {
        "🧠 Режимы",
        "👤 Профиль",
        "💎 Подписка",
        "👥 Рефералы",
        "🧠 Универсальный",
        "💼 Профессиональный",
        "💎 1 месяц",
        "💎 3 месяца",
        "💎 12 месяцев",
        "⬅️ Назад",
        "🔄 Проверить оплату",
    }
))
async def handle_chat(message: Message) -> None:
    # 1. Убедиться, что юзер есть в БД
    user_row = await ensure_user(message.from_user)

    # 2. Проверяем оплаты и подписки
    await refresh_user_payments_and_subscriptions(user_row["id"])
    user_row = await sync_user_premium_flag(user_row["id"])

    # 3. Лимиты
    limit = settings.premium_daily_limit if user_row["is_premium"] else settings.free_daily_limit
    used = await get_usage_today(user_row["id"])

    if used >= limit:
        if user_row["is_premium"]:
            text = (
                "🚫 Ты уже использовал дневной лимит Premium (100 запросов).\n"
                "Вернись завтра — лимит обновится."
            )
            await message.answer(text)
        else:
            text = (
                "🚫 Бесплатный лимит (10 запросов в день) исчерпан.\n\n"
                "Оформи подписку Premium, чтобы получить до 100 запросов в день и приоритетные ответы."
            )
            await message.answer(text, reply_markup=subscription_keyboard())
        return

    # 4. Увеличиваем счётчик
    await increment_usage(user_row["id"])

    # 5. Определяем режим
    mode = await get_user_mode(user_row["id"])

    # 6. Запрос к LLM
    result = await ask_llm(message.text, mode=mode)

    await message.answer(result.text)
