from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

MAIN_BUTTON_MODES = "🧠 Режимы"
MAIN_BUTTON_PROFILE = "👤 Профиль"
MAIN_BUTTON_SUBSCRIPTION = "💎 Подписка"
MAIN_BUTTON_REFERRALS = "👥 Рефералы"

MODE_LABELS = {
    "universal": "🧠 Универсальный",
    "medicine": "🩺 Медицина",
    "mentor": "🔥 Наставник",
    "business": "💼 Бизнес",
    "creative": "🎨 Креатив",
}

BACK_BUTTON_TEXT = "⬅️ Назад"

MODE_BUTTON_TEXTS = list(MODE_LABELS.values())
MODE_BUTTON_TEXTS_WITH_CHECK = MODE_BUTTON_TEXTS + [
    f"✅ {label}" for label in MODE_LABELS.values()
]


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MAIN_BUTTON_MODES),
                KeyboardButton(text=MAIN_BUTTON_PROFILE),
            ],
            [
                KeyboardButton(text=MAIN_BUTTON_SUBSCRIPTION),
                KeyboardButton(text=MAIN_BUTTON_REFERRALS),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def modes_menu_kb(current_mode: str) -> ReplyKeyboardMarkup:
    rows = []
    for mode_key, base_label in MODE_LABELS.items():
        text = f"✅ {base_label}" if mode_key == current_mode else base_label
        rows.append([KeyboardButton(text=text)])

    rows.append([KeyboardButton(text=BACK_BUTTON_TEXT)])

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        is_persistent=True,
    )
