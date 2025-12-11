from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

BACK_BUTTON_TEXT = "⬅️ Назад"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
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
    return main_menu_keyboard()


def referrals_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BACK_BUTTON_TEXT)]],
        resize_keyboard=True,
    )
