from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from .common import BACK_BUTTON_TEXT


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Главное меню.

    Структура:
    - 🧠 Режимы
    - 👤 Профиль      💎 Подписка
    - 👥 Рефералы
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
    Меню выбора режима работы ассистента.

    Оставляем только два режима:
    - 🧠 Универсальный   — DeepSeek без web-поиска
    - 💼 Профессиональный — умный режим (переключается между DeepSeek и Perplexity)

    Наставник + Медицина теперь живут внутри "Профессионального" режима,
    поэтому отдельные кнопки убираем.
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
    Пока профиль — это заглушка.
