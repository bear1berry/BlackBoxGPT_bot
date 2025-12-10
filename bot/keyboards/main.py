from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
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
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Напиши запрос или выбери пункт меню…",
    )


def modes_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [
            KeyboardButton(text="Универсальный"),
            KeyboardButton(text="Медицина"),
        ],
        [
            KeyboardButton(text="Наставник"),
            KeyboardButton(text="Бизнес"),
        ],
        [
            KeyboardButton(text="Креатив"),
            KeyboardButton(text="⬅️ Назад"),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
    )
