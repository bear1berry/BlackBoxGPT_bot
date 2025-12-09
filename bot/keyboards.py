from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_kb() -> InlineKeyboardMarkup:
    """Bottom taskbar with main sections."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="\U0001f9e0 Режимы", callback_data="nav:modes"),
                InlineKeyboardButton(text="\U0001f464 Профиль", callback_data="nav:profile"),
            ],
            [
                InlineKeyboardButton(text="\U0001f48e Подписка", callback_data="nav:subscription"),
                InlineKeyboardButton(text="\U0001f465 Рефералы", callback_data="nav:referrals"),
            ],
        ]
    )


def modes_kb(current_mode: str) -> InlineKeyboardMarkup:
    buttons = [
        ("\U0001f9e0 Универсальный", "universal"),
        ("\U0001fa7a Медицина", "medicine"),
        ("\U0001f525 Наставник", "mentor"),
        ("\U0001f4bc Бизнес", "business"),
        ("\U0001f3a8 Креатив", "creative"),
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
