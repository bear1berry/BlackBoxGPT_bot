    from __future__ import annotations

    from aiogram import Router, F
    from aiogram.filters import CommandStart
    from aiogram.types import Message

    from ..keyboards import main_menu_keyboard, modes_keyboard, subscription_keyboard
    from ..services.storage import get_or_create_user, sync_user_premium_flag

    router = Router()


    @router.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        user_row = await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )

        await sync_user_premium_flag(user_row["id"])

        text = (
            "👋 <b>BlackBox GPT — Universal AI Assistant</b>

"
            "Два режима работы:
"
            "• <b>Универсальный</b> — быстрые ответы на базе DeepSeek.
"
            "• <b>Профессиональный</b> — для сложных задач, с web-поиском через Perplexity.

"
            "Также есть <b>Premium-подписка</b>: больше запросов, приоритетные лимиты.

"
            "Выбери пункт меню ниже, чтобы продолжить ↓"
        )

        await message.answer(text, reply_markup=main_menu_keyboard())


    @router.message(F.text == "🧠 Режимы")
    async def on_modes(message: Message) -> None:
        await message.answer(
            "Выбери режим работы ассистента ↓",
            reply_markup=modes_keyboard(),
        )


    @router.message(F.text == "💎 Подписка")
    async def on_subscription_menu(message: Message) -> None:
        await message.answer(
            (
                "💎 <b>Premium-подписка</b>

"
                "Тарифы:
"
                "• 1 месяц — <b>6.99 USDT</b>
"
                "• 3 месяца — <b>20.99 USDT</b>
"
                "• 12 месяцев — <b>59.99 USDT</b>

"
                "Лимиты:
"
                "• Базовый (бесплатный) — 10 запросов в день.
"
                "• Premium — 100 запросов в день.

"
                "Оплата через Crypto Bot в USDT.
"
                "Выбери срок подписки ↓"
            ),
            reply_markup=subscription_keyboard(),
        )
