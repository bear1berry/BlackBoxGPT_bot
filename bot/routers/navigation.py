from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.config import settings
from bot.keyboards import (
    back_to_main_kb,
    main_menu_kb,
    modes_menu_kb,
    payment_inline_kb,
    referral_link_inline_kb,
    subscription_menu_kb,
)
from bot.services.cryptopay import CryptoPayError, create_invoice, get_invoice
from bot.texts import (
    build_main_menu_text,
    build_modes_text,
    build_profile_text,
    build_referrals_text,
    build_subscription_text,
)
from db.crud import (
    create_payment,
    get_payment_by_invoice_id,
    get_plan_config,
    get_user_by_tg_id,
    mark_payment_paid_and_extend_subscription,
    update_user_mode,
)

logger = logging.getLogger(__name__)

router = Router(name="navigation")


# ---------- MAIN MENU BUTTONS ----------


@router.message(F.text == "🧠 Режимы")
async def on_modes(message: Message) -> None:
    user = await get_user_by_tg_id(message.from_user.id)
    mode_text = build_modes_text()
    await message.answer(mode_text, reply_markup=modes_menu_kb())


@router.message(F.text == "👤 Профиль")
async def on_profile(message: Message) -> None:
    from_user = message.from_user
    user = await get_user_by_tg_id(from_user.id)
    if not user:
        await message.answer("⚠️ Не удалось найти профиль. Напиши /start.")
        return

    username = from_user.username
    ref_code = user.ref_code or str(from_user.id)
    ref_link = f"{settings.bot_link}?start={ref_code}"

    profile_text = build_profile_text(
        first_name=from_user.first_name,
        username=username,
        current_mode=user.current_mode,
        subscription_tier=user.subscription_tier,
        subscription_expires_at=user.subscription_expires_at,
        ref_link=ref_link,
        referrals_count=user.referrals_count or 0,
    )

    # Пытаемся подтянуть аватар
    photos = await message.bot.get_user_profile_photos(from_user.id, limit=1)
    if photos.total_count > 0 and photos.photos:
        file_id = photos.photos[0][-1].file_id
        await message.answer_photo(
            photo=file_id,
            caption=profile_text,
            reply_markup=referral_link_inline_kb(ref_link),
        )
    else:
        await message.answer(
            profile_text,
            reply_markup=referral_link_inline_kb(ref_link),
        )


@router.message(F.text == "💎 Подписка")
async def on_subscription(message: Message) -> None:
    user = await get_user_by_tg_id(message.from_user.id)
    if not user:
        await message.answer("⚠️ Не удалось найти профиль. Напиши /start.")
        return

    text = build_subscription_text(
        subscription_tier=user.subscription_tier,
        subscription_expires_at=user.subscription_expires_at,
    )
    await message.answer(text, reply_markup=subscription_menu_kb())


@router.message(F.text == "👥 Рефералы")
async def on_referrals(message: Message) -> None:
    user = await get_user_by_tg_id(message.from_user.id)
    if not user:
        await message.answer("⚠️ Не удалось найти профиль. Напиши /start.")
        return

    ref_code = user.ref_code or str(user.tg_id)
    ref_link = f"{settings.bot_link}?start={ref_code}"

    text = build_referrals_text(
        ref_link=ref_link,
        referrals_count=user.referrals_count or 0,
    )
    await message.answer(
        text,
        reply_markup=referral_link_inline_kb(ref_link),
    )


# ---------- MODES ----------


@router.message(F.text == "🧠 Универсальный")
async def mode_universal(message: Message) -> None:
    await _set_mode(message, "universal")


@router.message(F.text == "🩺 Медицина")
async def mode_medicine(message: Message) -> None:
    await _set_mode(message, "medicine")


@router.message(F.text == "🔥 Наставник")
async def mode_mentor(message: Message) -> None:
    await _set_mode(message, "mentor")


@router.message(F.text == "💼 Бизнес")
async def mode_business(message: Message) -> None:
    await _set_mode(message, "business")


@router.message(F.text == "🎨 Креатив")
async def mode_creative(message: Message) -> None:
    await _set_mode(message, "creative")


async def _set_mode(message: Message, mode: str) -> None:
    user = await update_user_mode(message.from_user.id, mode)
    if not user:
        await message.answer("⚠️ Не удалось обновить режим. Напиши /start.")
        return

    text = build_main_menu_text(user.current_mode)
                   await message.answer(
            (
                f"✅ Режим обновлён: {mode.capitalize()}.\n\n"
                "Теперь просто напиши свой запрос — "
                "я буду отвечать уже в этом режиме."
            ),
            reply_markup=main_menu_keyboard(),
        )


@router.message(F.text == "⬅️ Назад")
async def on_back_to_main(message: Message) -> None:
    user = await get_user_by_tg_id(message.from_user.id)
    text = build_main_menu_text(user.current_mode if user else "universal")
    await message.answer(text, reply_markup=main_menu_kb())


# ---------- SUBSCRIPTIONS & CRYPTOPAY ----------


@router.message(F.text == "💎 1 месяц — $7.99")
async def subscribe_1m(message: Message) -> None:
    await _start_subscription_payment(message, "1m")


@router.message(F.text == "💎 3 месяца — $25.99")
async def subscribe_3m(message: Message) -> None:
    await _start_subscription_payment(message, "3m")


@router.message(F.text == "💎 12 месяцев — $89.99")
async def subscribe_12m(message: Message) -> None:
    await _start_subscription_payment(message, "12m")


async def _start_subscription_payment(message: Message, plan_code: str) -> None:
    user = await get_user_by_tg_id(message.from_user.id)
    if not user:
        await message.answer("⚠️ Не удалось найти профиль. Напиши /start.")
        return

    if not settings.cryptopay_api_token:
        await message.answer(
            "⚠️ Crypto Bot пока не настроен.
"
            "Заполни CRYPTOPAY_API_TOKEN на сервере и перезапусти бота."
        )
        return

    cfg = get_plan_config(plan_code)
    price = cfg["price"]

    description = f"Подписка BlackBox GPT: план {plan_code}, {cfg['days']} дней Premium."
    payload = f"user_id={user.id}&plan={plan_code}"

    try:
        invoice = await create_invoice(
            amount=price,
            description=description,
            payload=payload,
        )
    except CryptoPayError as exc:
        logger.exception("CryptoPay error: %s", exc)
        await message.answer("⚠️ Не удалось создать счёт в Crypto Bot. Попробуй позже.")
        return

    invoice_id = int(invoice["invoice_id"])
    pay_url = invoice["pay_url"]

    payment = await create_payment(
        user_id=user.id,
        plan_code=plan_code,
        invoice_id=invoice_id,
        pay_url=pay_url,
    )

    await message.answer(
        (
            "💎 <b>Шаг 1.</b> Оплати подписку по кнопке ниже через Crypto Bot.
"
            "💎 <b>Шаг 2.</b> После оплаты вернись сюда и нажми «✅ Проверить оплату».

"
            "После успешной проверки Premium активируется автоматически."
        ),
        reply_markup=payment_inline_kb(pay_url),
    )

    # Дополнительно отправим кнопку проверки
    await message.answer(
        "Когда оплатишь — нажми кнопку ниже:",
        reply_markup=_check_payment_inline_kb(payment.invoice_id),
    )


from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def _check_payment_inline_kb(invoice_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Проверить оплату",
                    callback_data=f"check_payment:{invoice_id}",
                )
            ]
        ]
    )


@router.callback_query(F.data.startswith("check_payment:"))
async def on_check_payment(callback: CallbackQuery) -> None:
    await callback.answer()  # убираем "часики"
    data = callback.data or ""
    _, invoice_str = data.split(":", maxsplit=1)
    try:
        invoice_id = int(invoice_str)
    except ValueError:
        await callback.message.answer("⚠️ Неверный идентификатор платежа.")
        return

    try:
        invoice = await get_invoice(invoice_id)
    except CryptoPayError as exc:
        logger.exception("CryptoPay get_invoice error: %s", exc)
        await callback.message.answer(
            "⚠️ Не удалось проверить оплату. Попробуй ещё раз через минуту."
        )
        return

    status = invoice.get("status")
    if status != "paid":
        await callback.message.answer(
            "⏳ Оплата пока не зафиксирована.
"
            "Если ты уже оплатил — подожди 10–30 секунд и нажми ещё раз."
        )
        return

    payment = await get_payment_by_invoice_id(invoice_id)
    if not payment:
        await callback.message.answer(
            "⚠️ Платёж найден в Crypto Bot, но не в базе бота. Свяжись с поддержкой."
        )
        return

    if payment.status == "paid":
        await callback.message.answer("✅ Подписка уже активирована ранее.")
        return

    user = await mark_payment_paid_and_extend_subscription(payment.id)

    await callback.message.answer(
        "💎 <b>Premium активирован!</b>
"
        "Спасибо за поддержку проекта 🙌

"
        "Можешь продолжать пользоваться ботом в полную силу.",
        reply_markup=main_menu_kb(),
    )
