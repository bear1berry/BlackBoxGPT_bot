from __future__ import annotations

from aiogram import Router, F
from aiogram.types import Message

from bot.keyboards import (
    main_menu_kb,
    modes_menu_kb,
    profile_menu_kb,
    subscription_menu_kb,
    referrals_menu_kb,
)
from bot import texts
from bot.services import storage


router = Router(name="navigation-router")

MODE_BUTTON_TO_KEY = {
    "🧠 Универсальный": ("universal", "Универсальный"),
    "🩺 Медицина": ("med", "Медицина"),
    "🔥 Наставник": ("mentor", "Наставник"),
    "💼 Бизнес": ("business", "Бизнес"),
    "🎨 Креатив": ("creative", "Креатив"),
}


@router.message(F.text == "🧠 Режимы")
async def open_modes(message: Message) -> None:
    await message.answer(texts.mode_menu_intro(), reply_markup=modes_menu_kb)


@router.message(F.text.in_(MODE_BUTTON_TO_KEY.keys()))
async def change_mode(message: Message) -> None:
    user = message.from_user
    if user is None:
        return

    mode_key, mode_human = MODE_BUTTON_TO_KEY[message.text]
    await storage.set_user_mode(user.id, mode_key)

    await message.answer(
        texts.mode_updated(mode_human),
        reply_markup=main_menu_kb,
    )


@router.message(F.text == "👤 Профиль")
async def open_profile(message: Message) -> None:
    user = message.from_user
    if user is None:
        return

    profile = await storage.get_profile(user.id)
    await message.answer(texts.profile_text(profile), reply_markup=profile_menu_kb)


@router.message(F.text == "💎 Подписка")
async def open_subscription(message: Message) -> None:
    await message.answer(texts.subscription_text(), reply_markup=subscription_menu_kb)


@router.message(F.text == "👥 Рефералы")
async def open_referrals(message: Message) -> None:
    await message.answer(texts.referrals_text(), reply_markup=referrals_menu_kb)


@router.message(F.text == "⬅️ Назад")
async def go_back(message: Message) -> None:
    """
    Кнопка «Назад» из любых подменю возвращает в главный экран.
    """
    user = message.from_user
    await message.answer(
        texts.main_welcome(user.first_name if user else None),
        reply_markup=main_menu_kb,
    )


@router.message(F.text.startswith("Профиль:"))
async def update_profile(message: Message) -> None:
    """
    Пользователь может обновить профиль текстом вида:
    «Профиль: я врач-эпидемиолог, люблю минимализм...»
    """
    user = message.from_user
    if user is None:
        return

    raw = message.text or ""
    description = raw.split(":", 1)[1].strip() if ":" in raw else raw.strip()
    profile = {"Описание": description}

    await storage.set_profile(user.id, profile)

    await message.answer(texts.profile_text(profile), reply_markup=profile_menu_kb)
