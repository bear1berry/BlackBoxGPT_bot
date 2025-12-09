from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from bot.config import Settings
from bot.keyboards import (
    main_menu_kb,
    modes_menu_kb,
    MAIN_BUTTON_MODES,
    MAIN_BUTTON_PROFILE,
    MAIN_BUTTON_SUBSCRIPTION,
    MAIN_BUTTON_REFERRALS,
    MODE_LABELS,
    MODE_BUTTON_TEXTS_WITH_CHECK,
    BACK_BUTTON_TEXT,
)
from bot.texts import (
    PROFILE_TEMPLATE,
    SUBSCRIPTION_TEXT,
    REFERRALS_TEXT,
    build_welcome_text,
)
from db import (
    get_session_factory,
    get_daily_limit,
    User,
)

router = Router(name="navigation")


# --- 1-й уровень таскбара ---


@router.message(F.text == MAIN_BUTTON_MODES)
async def nav_modes(message: Message) -> None:
    """Переход в выбор режимов (2-й уровень таскбара)."""
    session_factory = get_session_factory()

    async with session_factory() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

    current_mode = user.current_mode if user else "universal"

    await message.answer(
        "<b>Выбор режима</b>\n\n"
        "Выбери, как я буду думать и отвечать. "
        "Можно переключать режимы в любой момент.",
        reply_markup=modes_menu_kb(current_mode),
    )


@router.message(F.text == MAIN_BUTTON_PROFILE)
async def nav_profile(message: Message) -> None:
    settings = Settings()
    session_factory = get_session_factory()

    async with session_factory() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

    if user is None:
        await message.answer("Профиль не найден. Напиши /start")
        return

    limit = get_daily_limit(user.subscription_tier)
    used = user.daily_message_count or 0
    username = user.username or message.from_user.username or "—"

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

    await message.answer(text, reply_markup=main_menu_kb())


@router.message(F.text == MAIN_BUTTON_SUBSCRIPTION)
async def nav_subscription(message: Message) -> None:
    await message.answer(SUBSCRIPTION_TEXT, reply_markup=main_menu_kb())


@router.message(F.text == MAIN_BUTTON_REFERRALS)
async def nav_referrals(message: Message) -> None:
    settings = Settings()
    session_factory = get_session_factory()

    async with session_factory() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

    if user is None:
        await message.answer("Профиль не найден. Напиши /start")
        return

    ref_link = f"{settings.bot_link}?start={user.ref_code}"
    text = REFERRALS_TEXT.format(
        referrals=user.referrals_count,
        ref_link=ref_link,
    )
    await message.answer(text, reply_markup=main_menu_kb())


# --- Кнопка «Назад» ---


@router.message(F.text == BACK_BUTTON_TEXT)
async def nav_back_to_main(message: Message) -> None:
    """Вернуться на главный экран (онбординг + главный таскбар)."""
    settings = Settings()
    text = build_welcome_text(settings)
    await message.answer(text, reply_markup=main_menu_kb())


# --- Выбор режима (2-й уровень) ---


@router.message(F.text.in_(MODE_BUTTON_TEXTS_WITH_CHECK))
async def choose_mode(message: Message) -> None:
    """Переключение режима через кнопки в таскбаре 2-го уровня."""
    raw = message.text.replace("✅", "").strip()

    mode_key = None
    for key, label in MODE_LABELS.items():
        if raw == label:
            mode_key = key
            break

    if mode_key is None:
        return

    session_factory = get_session_factory()
    async with session_factory() as session:
        from sqlalchemy import select

        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            await message.answer("Профиль не найден. Напиши /start")
            return

        user.current_mode = mode_key
        await session.commit()

    await message.answer(
        f"Режим переключён на <b>{raw}</b>.",
        reply_markup=modes_menu_kb(mode_key),
    )
