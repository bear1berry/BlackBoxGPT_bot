from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    """Bottom taskbar with main sections."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🧠 Режимы", callback_data="nav:modes"),
                InlineKeyboardButton(text="👤 Профиль", callback_data="nav:profile"),
            ],
            [
                InlineKeyboardButton(text="💎 Подписка", callback_data="nav:subscription"),
                InlineKeyboardButton(text="👥 Рефералы", callback_data="nav:referrals"),
            ],
        ]
    )


def modes_kb(current_mode: str) -> InlineKeyboardMarkup:
    buttons = [
        ("🧠 Универсальный", "universal"),
        ("🩺 Медицина", "medicine"),
        ("🔥 Наставник", "mentor"),
        ("💼 Бизнес", "business"),
        ("🎨 Креатив", "creative"),
    ]

    rows = [
        [
            InlineKeyboardButton(
                text=(f"✅ {text}" if mode == current_mode else text),
                callback_data=f"mode:{mode}",
            )
        ]
        for text, mode in buttons
    ]

    rows.append(
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:back_to_main")]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)
