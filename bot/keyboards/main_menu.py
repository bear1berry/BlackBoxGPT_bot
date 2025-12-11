from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from .common import BACK_BUTTON_TEXT


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Главное меню.

    Структура:
    🧠 Режимы
    👤 Профиль | 💎 Подписка
    👥 Рефералы
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧠 Режимы")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="💎 Подписка")],
            [KeyboardButton(text="👥 Рефералы")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Напиши запрос или выбери пункт меню ↓",
    )


def modes_keyboard() -> ReplyKeyboardMarkup:
    """
    Меню выбора режимов.

    Оставляем только два режима:
    - 🧠 Универсальный — обычный режим на DeepSeek.
    - 💼 Профессиональный — «собирает» в себе наставника + медицину
      и при необходимости включает web-поиск через Perplexity.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧠 Универсальный")],
            [KeyboardButton(text="💼 Профессиональный")],
            [KeyboardButton(text=BACK_BUTTON_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери режим работы ассистента ↓",
    )


def subscription_keyboard() -> ReplyKeyboardMarkup:
    """
    Меню выбора срока подписки.
    """
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💎 1 месяц")],
            [KeyboardButton(text="💎 3 месяца")],
            [KeyboardButton(text="💎 12 месяцев")],
            [KeyboardButton(text=BACK_BUTTON_TEXT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери срок подписки ↓",
    )


def profile_keyboard() -> ReplyKeyboardMarkup:
    """
    Пока отдельного подменю нет — возвращаем главное.
    """
    return main_menu_keyboard()


def referrals_keyboard() -> ReplyKeyboardMarkup:
    """
    Простое меню для реферального раздела.
    Пока только кнопка «Назад».
    """
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BACK_BUTTON_TEXT)]],
        resize_keyboard=True,
    )
