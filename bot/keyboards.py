from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def main_menu_kb() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="🧠 Режимы"),
            KeyboardButton(text="👤 Профиль"),
        ],
        [
            KeyboardButton(text="💎 Подписка"),
            KeyboardButton(text="👥 Рефералы"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Напиши свой запрос...",
    )


def modes_menu_kb() -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="🧠 Универсальный"),
            KeyboardButton(text="🩺 Медицина"),
        ],
        [
            KeyboardButton(text="🔥 Наставник"),
            KeyboardButton(text="💼 Бизнес"),
        ],
        [
            KeyboardButton(text="🎨 Креатив"),
            KeyboardButton(text="⬅️ Назад"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выбери режим или вернись назад",
    )


def subscription_menu_kb() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="💎 1 месяц — $7.99")],
        [KeyboardButton(text="💎 3 месяца — $25.99")],
        [KeyboardButton(text="💎 12 месяцев — $89.99")],
        [KeyboardButton(text="⬅️ Назад")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выбери подходящий план или вернись назад",
    )


def back_to_main_kb() -> ReplyKeyboardMarkup:
    return main_menu_kb()


def referral_link_inline_kb(ref_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Открыть реферальную ссылку", url=ref_link)],
        ]
    )


def payment_inline_kb(pay_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 Оплатить через Crypto Bot", url=pay_url)],
        ]
    )
