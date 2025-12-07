from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery

from sqlalchemy import select, func

from bot.db.base import async_session_factory
from bot.db.models import User, Referral
from bot.keyboards import (
    main_menu_kb,
    modes_kb,
    subscription_kb,
    referrals_kb,
    profile_back_kb,
)
from services.user_service import get_referral_link, SUBSCRIPTION_LIMITS, set_mode


router = Router()


MODE_LABELS: dict[str, str] = {
    "universal": "Универсальный",
    "medicine": "Медицина",
    "mentor": "Наставник",
    "business": "Бизнес",
    "creative": "Креатив",
}


@router.callback_query(F.data == "menu:main")
async def menu_main(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "Главное меню. Выбирай раздел снизу:",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:modes")
async def menu_modes(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.id == callback.from_user.id)
        )
        user = result.scalar_one()
        kb = modes_kb(user.mode)
    await callback.message.edit_text(
        "🧠 <b>Режимы работы</b>\n\n"
        "Выбери, как я буду мыслить и отвечать.",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mode:"))
async def set_mode_handler(callback: CallbackQuery) -> None:
    mode = callback.data.split(":", 1)[1]
    if mode not in MODE_LABELS:
        await callback.answer("Неизвестный режим", show_alert=True)
        return

    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.id == callback.from_user.id)
        )
        user = result.scalar_one()
        await set_mode(session, user, mode)
        await session.commit()
        kb = modes_kb(mode)

    await callback.message.edit_text(
        f"Режим изменён на <b>{MODE_LABELS[mode]}</b>.",
        reply_markup=kb,
    )
    await callback.answer("Режим обновлён")


@router.callback_query(F.data == "menu:profile")
async def menu_profile(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.id == callback.from_user.id)
        )
        user = result.scalar_one()
        result_ref = await session.execute(
            select(func.count()).select_from(Referral).where(
                Referral.referrer_id == user.id
            )
        )
        refs_count = result_ref.scalar_one()
        limit = SUBSCRIPTION_LIMITS.get(
            user.subscription_tier, SUBSCRIPTION_LIMITS["free"]
        )
        text = (
            "👤 <b>Профиль</b>\n\n"
            f"ID: <code>{user.id}</code>\n"
            f"Режим: <b>{user.mode}</b>\n"
            f"Тариф: <b>{user.subscription_tier.upper()}</b>\n"
            f"Лимит сообщений в день: <b>{limit}</b>\n"
            f"Использовано сегодня: <b>{user.daily_usage}</b>\n"
            f"Рефералов: <b>{refs_count}</b>\n\n"
            f"Твоя реферальная ссылка:\n{get_referral_link(user)}"
        )

    await callback.message.edit_text(text, reply_markup=profile_back_kb())
    await callback.answer()


@router.callback_query(F.data == "menu:subscription")
async def menu_subscription(callback: CallbackQuery) -> None:
    text = (
        "💎 <b>Подписка</b>\n\n"
        "Free — базовый доступ с ограниченным числом сообщений.\n"
        "Pro — повышенные лимиты и приоритетная очередь.\n"
        "VIP — максимальные лимиты и максимум скорости.\n\n"
        "Выбери вариант подписки:"
    )
    await callback.message.edit_text(text, reply_markup=subscription_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("sub:plan:"))
async def subscription_plan(callback: CallbackQuery) -> None:
    plan_code = callback.data.split(":", 2)[2]  # e.g. "pro_1", "pro_3", "vip_12"
    text = (
        "💎 <b>Оформление подписки</b>\n\n"
        f"Ты выбрал план: <code>{plan_code}</code>.\n\n"
        "Здесь можно интегрировать Telegram Payments / CryptoBot / карту.\n"
        "Сейчас тариф можно поменять вручную командой /set_tier (для админа)."
    )
    await callback.message.edit_text(text, reply_markup=subscription_kb())
    await callback.answer()


@router.callback_query(F.data == "menu:referrals")
async def menu_referrals(callback: CallbackQuery) -> None:
    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.id == callback.from_user.id)
        )
        user = result.scalar_one()
        link = get_referral_link(user)

        result_ref = await session.execute(
            select(func.count()).select_from(Referral).where(
                Referral.referrer_id == user.id
            )
        )
        refs_count = result_ref.scalar_one()

    text = (
        "👥 <b>Реферальная программа</b>\n\n"
        "Приглашай друзей по ссылке и получай бонусы (например, "
        "увеличенные лимиты или дни подписки — логику бонусов ты можешь "
        "доработать в коде).\n\n"
        f"Твоя ссылка:\n{link}\n\n"
        f"Всего рефералов: <b>{refs_count}</b>"
    )
    await callback.message.edit_text(text, reply_markup=referrals_kb())
    await callback.answer()
