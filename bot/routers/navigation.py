from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.config import Settings
from bot.keyboards import main_menu_kb, modes_kb
from bot.texts import PROFILE_TEMPLATE, SUBSCRIPTION_TEXT, REFERRALS_TEXT
from db import (
    get_session_factory,
    get_daily_limit,
    User,
)

router = Router(name="navigation")


@router.callback_query(F.data == "nav:modes")
async def nav_modes(callback: CallbackQuery) -> None:
    session_factory = get_session_factory()

    async with session_factory() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

    current_mode = user.current_mode if user else "universal"

    await callback.message.edit_text(
        "<b>Выбор режима</b>\n\n"
        "Выбери, как я буду думать и отвечать. "
        "Можно переключать режимы в любой момент.",
        reply_markup=modes_kb(current_mode),
    )
    await callback.answer()


@router.callback_query(F.data == "nav:profile")
async def nav_profile(callback: CallbackQuery) -> None:
    settings = Settings()
    session_factory = get_session_factory()

    async with session_factory() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

    if user is None:
        await callback.answer("Профиль не найден. Напиши /start", show_alert=True)
        return

    limit = get_daily_limit(user.subscription_tier)
    used = user.daily_message_count or 0
    username = user.username or callback.from_user.username or "—"

    ref_link = f"{settings.bot_link}?start={user.ref_code}"

    text = PROFILE_TEMPLATE.format(
        telegram_id=user.telegram_id,
        username=username,
        tier=user.subscription_tier.upper(),
        mode=user.current_mode,
        used=used,
        limit=limit,
        referrals=user.referrals_count,
        ref_link=ref_link,
    )

    await callback.message.edit_text(text, reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "nav:subscription")
async def nav_subscription(callback: CallbackQuery) -> None:
    await callback.message.edit_text(SUBSCRIPTION_TEXT, reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "nav:referrals")
async def nav_referrals(callback: CallbackQuery) -> None:
    settings = Settings()
    session_factory = get_session_factory()

    async with session_factory() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

    if user is None:
        await callback.answer("Профиль не найден. Напиши /start", show_alert=True)
        return

    ref_link = f"{settings.bot_link}?start={user.ref_code}"
    text = REFERRALS_TEXT.format(
        referrals=user.referrals_count,
        ref_link=ref_link,
    )
    await callback.message.edit_text(text, reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "nav:back_to_main")
async def nav_back_to_main(callback: CallbackQuery) -> None:
    # Просто возвращаем нижнее меню, текст оставляем
    await callback.message.edit_reply_markup(reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("mode:"))
async def choose_mode(callback: CallbackQuery) -> None:
    mode = callback.data.split(":", 1)[1].strip()
    if mode not in {"universal", "medicine", "mentor", "business", "creative"}:
        await callback.answer("Неизвестный режим.", show_alert=True)
        return

    session_factory = get_session_factory()
    async with session_factory() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            await callback.answer("Профиль не найден. Напиши /start", show_alert=True)
            return

        user.current_mode = mode
        await session.commit()

    await callback.message.edit_text(
        f"Режим обновлён: <b>{mode}</b>.\n\n"
        "Можешь продолжать писать сообщения.",
        reply_markup=main_menu_kb(),
    )
    await callback.answer("Режим установлен")
