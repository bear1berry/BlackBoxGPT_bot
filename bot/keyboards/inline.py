from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def modes_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧠 Универсальный", callback_data="mode:universal")],
            [InlineKeyboardButton(text="🩺 Медицина", callback_data="mode:medicine")],
            [InlineKeyboardButton(text="🔥 Наставник", callback_data="mode:mentor")],
            [InlineKeyboardButton(text="💼 Бизнес", callback_data="mode:business")],
            [InlineKeyboardButton(text="🎨 Креатив", callback_data="mode:creative")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:back_main")],
        ]
    )


def profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ℹ️ О боте", callback_data="profile:about")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:back_main")],
        ]
    )


def subscription_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💎 1 месяц", callback_data="sub:1m")],
            [InlineKeyboardButton(text="💎 3 месяца", callback_data="sub:3m")],
            [InlineKeyboardButton(text="💎 12 месяцев", callback_data="sub:12m")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:back_main")],
        ]
    )


def referrals_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Получить реф. ссылку", callback_data="ref:get_link")],
            [InlineKeyboardButton(text="📊 Моя статистика", callback_data="ref:stats")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:back_main")],
        ]
    )
