from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧠 Режимы")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="💎 Подписка")],
            [KeyboardButton(text="👥 Рефералы")]
        ],
        resize_keyboard=True
    )

def get_modes_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Универсальный")],
            [KeyboardButton(text="Профессиональный")],
            [KeyboardButton(text="Наставник")],
            [KeyboardButton(text="Медицина")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True
    )
