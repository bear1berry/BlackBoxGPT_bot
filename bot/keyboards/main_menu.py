from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# Главный таскбар
main_menu_keyboard = ReplyKeyboardMarkup(
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


# Кнопка "Назад" для вложенных меню
back_button = InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:back")

# Только 2 режима: Универсальный + Профессиональный
modes_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🧠 Универсальный",
                callback_data="mode:universal",
            )
        ],
        [
            InlineKeyboardButton(
                text="💼 Профессиональный",
                callback_data="mode:professional",
            )
        ],
        [ [back_button] ],
    ]
)

# Меню подписки с новыми ценами
subscription_keyboard = InlineKeyboardMarkup(
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
                text="🔁 Проверить оплату",
                callback_data="sub:check",
            )
        ],
        [ [back_button] ],
    ]
)
