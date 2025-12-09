from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict

from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from bot.config import settings
from bot.texts import build_main_menu_text


router = Router(name="navigation")


# ===== Простое in-memory состояние пользователя =====

@dataclass
class UserState:
    tg_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None

    mode: str = "universal"        # текущий режим
    is_premium: bool = False       # статус подписки
    referral_code: Optional[str] = None
    referred_by: Optional[str] = None
    about: Optional[str] = None


_USERS: Dict[int, UserState] = {}


def _get_full_name(cb_from) -> str:
    parts = [cb_from.first_name, cb_from.last_name]
    name = " ".join(p for p in parts if p)
    return name or cb_from.full_name or cb_from.username or "Гость"


def get_or_create_user_state(cb_from) -> UserState:
    tg_id = cb_from.id
    if tg_id in _USERS:
        user = _USERS[tg_id]
    else:
        user = UserState(
            tg_id=tg_id,
            username=cb_from.username,
            full_name=_get_full_name(cb_from),
        )
        _USERS[tg_id] = user

    # обновляем базовые данные при каждом запросе
    user.username = cb_from.username
    user.full_name = _get_full_name(cb_from)
    return user


# ===== Витрины текста и клавиатур =====

MODE_LABELS = {
    "universal": "🧠 Универсальный",
    "medicine": "🩺 Медицина",
    "mentor": "🔥 Наставник",
    "business": "💼 Бизнес",
    "creative": "🎨 Креатив",
}


def build_main_menu_kb() -> InlineKeyboardMarkup:
    """
    Главный таскбар с 4 разделами.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🧠 Режимы", callback_data="nav:modes"),
                InlineKeyboardButton(text="👤 Профиль", callback_data="nav:profile"),
            ],
            [
                InlineKeyboardButton(text="💎 Подписка", callback_data="nav:subscription"),
                InlineKeyboardButton(text="👥 Рефералы", callback_data="nav:referrals"),
            ],
        ]
    )


def build_modes_kb(current_mode: str) -> InlineKeyboardMarkup:
    rows = []
    for key, label in MODE_LABELS.items():
        prefix = "✅ " if key == current_mode else ""
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{prefix}{label}",
                    callback_data=f"mode:{key}",
                )
            ]
        )

    rows.append(
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:back_main")]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:back_main")]
        ]
    )


def build_subscription_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💎 1 месяц — 7.99 $",
                    callback_data="sub:1m",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 3 месяца — 25.99 $",
                    callback_data="sub:3m",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 12 месяцев — 89.99 $",
                    callback_data="sub:12m",
                )
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:back_main")],
        ]
    )


def build_referrals_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:back_main")]
        ]
    )


# ===== Handlers =====

@router.c
