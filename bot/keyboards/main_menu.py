from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Нижний таскбар: только то, что нам нужно.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🧠 Режимы"),
                KeyboardButton(text="👤 Профиль"),
            ],
            [
                KeyboardButton(text="💎 Подписка"),
                KeyboardButton(text="👥 Рефералы"),
            ],
        ],
        resize_keyboard=True,
    )


def modes_keyboard(current: str | None = None) -> InlineKeyboardMarkup:
    """
    Два основных режима: Универсальный и Профессиональный.
    """
    mark_universal = " ✅" if current == "universal" else ""
    mark_prof = " ✅" if current == "professional" else ""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🧠 Универсальный{mark_universal}",
                    callback_data="mode:universal",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"🏆 Профессиональный{mark_prof}",
                    callback_data="mode:professional",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="menu:back",
                )
            ],
        ]
    )


def subscription_keyboard() -> InlineKeyboardMarkup:
    """
    План подписки (Premium). Все тарифы — один и тот же уровень Premium,
    различается только срок.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💎 1 месяц — 6.99 USDT",
                    callback_data="sub:plan:1m",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 3 месяца — 20.99 USDT",
                    callback_data="sub:plan:3m",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 12 месяцев — 59.99 USDT",
                    callback_data="sub:plan:12m",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Проверить оплату",
                    callback_data="sub:check",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="menu:back",
                )
            ],
        ]
    )
