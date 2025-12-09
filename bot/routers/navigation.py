# bot/routers/navigation.py
from __future__ import annotations
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from sqlalchemy import select

from ..db import get_session
from ..keyboards import (
    main_menu_keyboard,
    modes_keyboard,
    subscription_keyboard,
    referral_keyboard,
    subscription_invoice_keyboard,
)
from ..models import User
from ..texts import (
    build_main_menu_text,
    build_profile_text,
    build_subscription_text,
    build_referrals_text,
    MODE_TITLES,
)
from ..config import settings
from ..services.referrals import build_referral_link, get_or_create_user
from ..services.payments_crypto import create_invoice, check_invoice_and_activate

router = Router(name="navigation")
logger = logging.getLogger(__name__)


# ---------- Режимы ----------


@router.message(F.text == "🧠 Режимы")
async def show_modes(message: Message) -> None:
    async with (await get_session()) as session:
        user = await get_or_create_user(session, message.from_user)

    await message.answer(
        "🧠 <b>Режимы мышления</b>\n\n"
        "Выбери, как я буду думать для тебя.\n"
        "Режим можно менять в любой момент.",
        reply_markup=modes_keyboard(),
    )


@router.message(
    F.text.in_(
        [
            "🧠 Универсальный",
            "🩺 Медицина",
            "🔥 Наставник",
            "💼 Бизнес",
            "🎨 Креатив",
        ]
    )
)
async def change_mode(message: Message) -> None:
    text = message.text or ""
    mode_map = {
        "🧠 Универсальный": "universal",
        "🩺 Медицина": "medicine",
        "🔥 Наставник": "mentor",
        "💼 Бизнес": "business",
        "🎨 Креатив": "creative",
    }
    new_mode = mode_map.get(text, "universal")

    async with (await get_session()) as session:
        user = await get_or_create_user(session, message.from_user)
        user.current_mode = new_mode
        await session.commit()

        mode_title = MODE_TITLES.get(new_mode, "Универсальный")
        await callback.message.edit_text(
        f"✅ Режим обновлён: <b>{mode.capitalize()}</b>.\n\n"
        "Можешь написать новый запрос ниже 👇",
        reply_markup=build_main_menu_kb(),
    )


@router.message(F.text == "⬅️ Назад в меню")
async def back_to_menu(message: Message) -> None:
    async with (await get_session()) as session:
        user = await get_or_create_user(session, message.from_user)
        text = build_main_menu_text(user)
    await message.answer(text, reply_markup=main_menu_keyboard())


# ---------- Профиль ----------


@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message) -> None:
    async with (await get_session()) as session:
        user = await get_or_create_user(session, message.from_user)

        bot = message.bot
        me = await bot.get_me()
        referral_link = build_referral_link(me.username, user.ref_code)

        text = build_profile_text(user, referral_link)

    await message.answer_photo(
        photo=message.from_user.photo.big_file_id if getattr(message.from_user, "photo", None) else None,
        caption=text,
        reply_markup=main_menu_keyboard(),
    ) if False else await message.answer(
        text,
        reply_markup=main_menu_keyboard(),
    )
    # 👆 Фото через Telegram API с аватаркой пользователя достать напрямую нельзя.
    # Поэтому пока оставляем текстовый профиль. Логика с "обезличенной аватаркой"
    # может быть реализована через отправку своего стокового изображения.


# ---------- Подписка ----------


@router.message(F.text == "💎 Подписка")
async def subscription_menu(message: Message) -> None:
    text = build_subscription_text()
    await message.answer(text, reply_markup=subscription_keyboard())


@router.message(
    F.text.in_(
        [
            "💎 1 месяц — 7.99$",
            "💎 3 месяца — 25.99$",
            "💎 12 месяцев — 89.99$",
        ]
    )
)
async def subscription_plan_selected(message: Message) -> None:
    plan_map = {
        "💎 1 месяц — 7.99$": "1m",
        "💎 3 месяца — 25.99$": "3m",
        "💎 12 месяцев — 89.99$": "12m",
    }
    plan = plan_map[message.text]

    async with (await get_session()) as session:
        user = await get_or_create_user(session, message.from_user)
        try:
            invoice_url, invoice_id = await create_invoice(session, user, plan)
        except Exception as e:
            logger.exception("Failed to create invoice")
            await message.answer(
                "❌ Не удалось создать ссылку на оплату. Попробуй позже.",
                reply_markup=main_menu_keyboard(),
            )
            return

    await message.answer(
        "💳 <b>Ссылка на оплату готова</b>\n\n"
        "Нажми кнопку ниже, оплати подписку и вернись в чат — "
        "бот автоматически проверит статус и активирует Premium.",
        reply_markup=subscription_invoice_keyboard(invoice_url),
    )


@router.callback_query(F.data == "sub_check_payment")
async def callback_check_payment(callback: CallbackQuery) -> None:
    await callback.answer("Проверяю оплату…", show_alert=False)

    async with (await get_session()) as session:
        user = await get_or_create_user(session, callback.from_user)
        ok = await check_invoice_and_activate(session, user)

        if ok:
            text = (
                "✅ <b>Оплата получена</b>\n\n"
                "Premium-режим активирован. Теперь я работаю на полную мощность."
            )
        else:
            text = (
                "⏳ Оплата ещё не найдена.\n\n"
                "Убедись, что перевод завершён, и попробуй через минуту."
            )

    await callback.message.answer(text, reply_markup=main_menu_keyboard())


# ---------- Рефералы ----------


@router.message(F.text == "👥 Рефералы")
async def show_referrals(message: Message) -> None:
    async with (await get_session()) as session:
        user = await get_or_create_user(session, message.from_user)
        me = await message.bot.get_me()
        link = build_referral_link(me.username, user.ref_code)
        text = build_referrals_text(link, settings.REF_BONUS_DAYS)

    await message.answer(text, reply_markup=referral_keyboard())


@router.message(F.text == "📎 Моя реферальная ссылка")
async def send_ref_link(message: Message) -> None:
    async with (await get_session()) as session:
        user = await get_or_create_user(session, message.from_user)
        me = await message.bot.get_me()
        link = build_referral_link(me.username, user.ref_code)

    await message.answer(
        f"📎 <b>Твоя ссылка:</b>\n<code>{link}</code>",
        reply_markup=referral_keyboard(),
    )
