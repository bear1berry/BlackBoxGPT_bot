from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu_kb = ReplyKeyboardMarkup(
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
    input_field_placeholder="Напиши запрос…",
)

modes_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
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
        ],
        [
            KeyboardButton(text="⬅️ Назад"),
        ],
    ],
    resize_keyboard=True,
)

profile_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✏️ Обновить профиль")],
        [KeyboardButton(text="⬅️ Назад")],
    ],
    resize_keyboard=True,
)

subscription_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💎 Тарифы")],
        [KeyboardButton(text="⬅️ Назад")],
    ],
    resize_keyboard=True,
)

referrals_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔗 Моя реферальная ссылка")],
        [KeyboardButton(text="⬅️ Назад")],
    ],
    resize_keyboard=True,
)
