from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_kb() -> ReplyKeyboardMarkup:
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
        input_field_placeholder="Напиши сообщение…",
    )
