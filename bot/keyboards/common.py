from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

BACK_BUTTON_TEXT = "⬅️ Назад"


def back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BACK_BUTTON_TEXT)]],
        resize_keyboard=True,
    )
