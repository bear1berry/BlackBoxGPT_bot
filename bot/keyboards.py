from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🧠 Режимы", callback_data="menu:modes"),
                InlineKeyboardButton(text="👤 Профиль", callback_data="menu:profile"),
            ],
            [
                InlineKeyboardButton(text="💎 Подписка", callback_data="menu:subscription"),
                InlineKeyboardButton(text="👥 Рефералы", callback_data="menu:referrals"),
            ],
        ]
    )


def modes_kb(current: str) -> InlineKeyboardMarkup:
    buttons = [
        ("🧠 Универсальный", "universal"),
        ("🩺 Медицина", "medicine"),
        ("🔥 Наставник", "mentor"),
        ("💼 Бизнес", "business"),
        ("🎨 Креатив", "creative"),
    ]

    rows: list[list[InlineKeyboardButton]] = []
    for text, mode in buttons:
        label = text
        if mode == current:
            label = f"✅ {text}"
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"mode:{mode}")]
        )

    rows.append(
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def subscription_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💎 1 месяц", callback_data="sub:plan:pro_1"),
                InlineKeyboardButton(text="💎 3 месяца", callback_data="sub:plan:pro_3"),
            ],
            [
                InlineKeyboardButton(
                    text="💎 12 месяцев (VIP)",
                    callback_data="sub:plan:vip_12",
                ),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main"),
            ],
        ]
    )


def referrals_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")]
        ]
    )


def profile_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")]
        ]
    )
