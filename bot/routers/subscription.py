from __future__ import annotations

from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from ..db.db import db
from ..keyboards.main_menu import main_menu_keyboard, subscription_keyboard
from ..services.storage import ensure_user
from ..services.payments_crypto import (
    is_cryptopay_configured,
    create_invoice_usdt,
    get_invoice_status,
)

router = Router(name="subscription")


# Цены в USDT
ONE_MONTH_PRICE = 6.99
THREE_MONTH_PRICE = 20.99
TWELVE_MONTH_PRICE = 59.99


async def _get_plan(user_id: int) -> tuple[str, datetime | None]:
    """
    Получаем текущий план и срок действия, при необходимости
    автоматически отключаем просроченный Premium.
    """
    row = await db.fetchrow(
        "SELECT plan, plan_until FROM users WHERE id=$1",
        user_id,
    )
    if not row:
        return "free", None

    plan = row["plan"] or "free"
    plan_until = row["plan_until"]

    if plan == "premium" and plan_until is not None:
        now = datetime.now(timezone.utc)
        if plan_until <= now:
            # Подписка истекла — откатываемся на free
            await db.execute(
                "UPDATE users SET plan='free', plan_until=NULL WHERE id=$1",
                user_id,
            )
            return "free", None

    return plan, plan_until


async def _activate_premium(user_id: int, months: int) -> datetime:
    """
    Включаем / продлеваем Premium-подписку на указанное количество месяцев.
    Месяц считаем условно как 30 дней.
    """
    now = datetime.now(timezone.utc)

    row = await db.fetchrow(
        "SELECT plan_until FROM users WHERE id=$1",
        user_id,
    )
    current_until = row["plan_until"] if row else None

    if current_until and isinstance(current_until, datetime) and current_until > now:
        base = current_until
    else:
        base = now

    new_until = base + timedelta(days=30 * months)

    await db.execute(
        "UPDATE users SET plan='premium', plan_until=$1 WHERE id=$2",
        new_until,
        user_id,
    )

    return new_until


def _payment_keyboard(invoice_id: str, months: int) -> InlineKeyboardMarkup:
    """
    Клавиатура под сообщением с оплатой.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Проверить оплату",
                    callback_data=f"check_invoice:{invoice_id}:{months}",
                )
            ]
        ]
    )


@router.message(F.text == "💎 Подписка")
async def subscription_entry(message: Message) -> None:
    """
    Обработка входа в раздел «Подписка».
    Показываем текущий тариф и предлагаем варианты оплаты.
    """
    user = await ensure_user(message.from_user)
    plan, plan_until = await _get_plan(user["id"])

    if plan == "premium" and plan_until:
        until_str = plan_until.astimezone(timezone.utc).strftime("%d.%m.%Y")
        text = (
            "💎 <b>Подписка</b>\n\n"
            "Сейчас у тебя активен тариф <b>Premium</b>.\n"
            f"Действует до: <b>{until_str}</b> (UTC).\n\n"
            "Ограничения:\n"
            "• Free — 10 запросов всего.\n"
            "• Premium — до 100 запросов в день.\n\n"
            "Хочешь продлить — выбери срок подписки:"
        )
    else:
        text = (
            "💎 <b>Подписка</b>\n\n"
            "Сейчас у тебя тариф <b>Free</b>.\n"
            "Ограничения:\n"
            "• Free — 10 запросов за всё время.\n"
            "• Premium — до 100 запросов в день + приоритет к модели.\n\n"
            "Выбери срок подписки, чтобы перейти на Premium:"
        )

    if not is_cryptopay_configured():
        # Токен не настроен — честно говорим об этом
        text += (
            "\n\n⚠️ Платёж через Crypto Bot пока не настроен.\n"
            "Технически всё готово — добавь токен Crypto Pay в .env "
            "и перезапусти бота."
        )
        await message.answer(text, reply_markup=subscription_keyboard())
        return

    await message.answer(text, reply_markup=subscription_keyboard())


@router.message(F.text == "💎 1 месяц")
async def handle_one_month(message: Message) -> None:
    user = await ensure_user(message.from_user)

    if not is_cryptopay_configured():
        await message.answer(
            "⚠️ Платёж через Crypto Bot пока не настроен.\n"
            "Добавь CRYPTOPAY_API_TOKEN в .env и перезапусти бота.",
            reply_markup=main_menu_keyboard(),
        )
        return

    invoice_id, pay_url = await create_invoice_usdt(
        user_id=user["id"],
        amount_usdt=ONE_MONTH_PRICE,
        period_months=1,
    )

    text = (
        "💎 <b>Подписка на 1 месяц</b>\n\n"
        f"Стоимость: <b>{ONE_MONTH_PRICE} USDT</b>.\n\n"
        "1) Нажми по ссылке ниже и оплати счёт через @CryptoBot.\n"
        "2) Вернись в диалог и нажми кнопку «✅ Проверить оплату».\n\n"
        f"<a href=\"{pay_url}\">👉 Оплатить через Crypto Bot</a>"
    )

    await message.answer(
        text,
        reply_markup=_payment_keyboard(invoice_id, 1),
        disable_web_page_preview=False,
    )


@router.message(F.text == "💎 3 месяца")
async def handle_three_months(message: Message) -> None:
    user = await ensure_user(message.from_user)

    if not is_cryptopay_configured():
        await message.answer(
            "⚠️ Платёж через Crypto Bot пока не настроен.\n"
            "Добавь CRYPTOPAY_API_TOKEN в .env и перезапусти бота.",
            reply_markup=main_menu_keyboard(),
        )
        return

    invoice_id, pay_url = await create_invoice_usdt(
        user_id=user["id"],
        amount_usdt=THREE_MONTH_PRICE,
        period_months=3,
    )

    text = (
        "💎 <b>Подписка на 3 месяца</b>\n\n"
        f"Стоимость: <b>{THREE_MONTH_PRICE} USDT</b>.\n\n"
        "1) Нажми по ссылке ниже и оплати счёт через @CryptoBot.\n"
        "2) Вернись в диалог и нажми кнопку «✅ Проверить оплату».\n\n"
        f"<a href=\"{pay_url}\">👉 Оплатить через Crypto Bot</a>"
    )

    await message.answer(
        text,
        reply_markup=_payment_keyboard(invoice_id, 3),
        disable_web_page_preview=False,
    )


@router.message(F.text == "💎 12 месяцев")
async def handle_twelve_months(message: Message) -> None:
    user = await ensure_user(message.from_user)

    if not is_cryptopay_configured():
        await message.answer(
            "⚠️ Платёж через Crypto Bot пока не настроен.\n"
            "Добавь CRYPTOPAY_API_TOKEN в .env и перезапусти бота.",
            reply_markup=main_menu_keyboard(),
        )
        return

    invoice_id, pay_url = await create_invoice_usdt(
        user_id=user["id"],
        amount_usdt=TWELVE_MONTH_PRICE,
        period_months=12,
    )

    text = (
        "💎 <b>Подписка на 12 месяцев</b>\n\n"
        f"Стоимость: <b>{TWELVE_MONTH_PRICE} USDT</b>.\n\n"
        "1) Нажми по ссылке ниже и оплати счёт через @CryptoBot.\n"
        "2) Вернись в диалог и нажми кнопку «✅ Проверить оплату».\n\n"
        f"<a href=\"{pay_url}\">👉 Оплатить через Crypto Bot</a>"
    )

    await message.answer(
        text,
        reply_markup=_payment_keyboard(invoice_id, 12),
        disable_web_page_preview=False,
    )


@router.callback_query(F.data.startswith("check_invoice:"))
async def check_invoice_callback(callback: CallbackQuery) -> None:
    """
    Обработка кнопки «Проверить оплату».
    Формат callback_data: "check_invoice
