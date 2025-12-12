    from __future__ import annotations

    from aiogram import Router, F
    from aiogram.types import Message

    from ..keyboards import main_menu_keyboard, modes_keyboard, subscription_keyboard
    from ..services.llm import Mode, generate_answer
    from ..services.storage import (
        get_or_create_user,
        ensure_daily_limit,
        mark_request_used,
        create_subscription_invoice,
    )

    router = Router()


    @router.message(F.text == "🧠 Универсальный")
    async def set_universal_mode(message: Message) -> None:
        await message.answer(
            "🧠 <b>Универсальный режим</b> активирован.
"
            "Можешь задавать любые вопросы — я отвечаю на базе DeepSeek.",
            reply_markup=main_menu_keyboard(),
        )
        # В минимальной версии режим можно хранить только в памяти клиента,
        # но здесь для простоты считаем, что режим определяется по кнопке
        # перед каждым запросом (можно расширить через FSM/таблицу users).


    @router.message(F.text == "💼 Профессиональный")
    async def set_pro_mode(message: Message) -> None:
        await message.answer(
            "💼 <b>Профессиональный режим</b> активирован.
"
            "Для сложных запросов, экспертизы, разбора кейсов и web-поиска.",
            reply_markup=main_menu_keyboard(),
        )


    @router.message(F.text.startswith("💎 "))
    async def on_subscription_plan(message: Message) -> None:
        user_row = await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )

        text = message.text or ""

        if "1 месяц" in text:
            months = 1
        elif "3 месяца" in text:
            months = 3
        elif "12 месяцев" in text:
            months = 12
        else:
            await message.answer("Не удалось определить срок подписки. Попробуй ещё раз.")
            return

        invoice_link = await create_subscription_invoice(user_row["id"], months=months)

        if not invoice_link:
            await message.answer(
                "Платёжный провайдер временно недоступен или не настроен.
"
                "Свяжись с поддержкой."
            )
            return

        await message.answer(
            (
                "💎 Готово!

"
                "Перейди по ссылке для оплаты подписки:
"
                f"{invoice_link}

"
                "После оплаты бот автоматически активирует Premium."
            ),
            reply_markup=subscription_keyboard(),
        )


    @router.message()
    async def on_message(message: Message) -> None:
        user_row = await get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )

        # Проверяем лимиты
        ok, reason = await ensure_daily_limit(user_row["id"])
        if not ok:
            await message.answer(reason or "Лимит исчерпан.")
            return

        text = message.text or ""

        # Простейшая эвристика: если пользователь явно просит web/интернет —
        # включаем professional+web. Иначе — Universal.
        lowered = text.lower()
        if any(word in lowered for word in ("найди в интернете", "посмотри в веб", "поиск в web", "гуглни", "web ")):
            mode = Mode.PROFESSIONAL
            use_web = True
        else:
            mode = Mode.UNIVERSAL
            use_web = False

        await mark_request_used(user_row["id"])

        reply_text = await generate_answer(
            user_message=text,
            mode=mode,
            use_web=use_web,
        )

        await message.answer(reply_text)
