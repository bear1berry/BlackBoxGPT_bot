from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.services.modes import list_modes


def main_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🧠 Режимы", callback_data="menu:modes")
    kb.button(text="👤 Профиль", callback_data="menu:profile")
    kb.button(text="💎 Подписка", callback_data="menu:subscription")
    kb.button(text="👥 Рефералы", callback_data="menu:referrals")
    kb.adjust(4)
    return kb.as_markup()


def modes_menu_kb(current_mode: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for mode in list_modes():
        label = f"{mode.emoji} {mode.title}"
        if mode.key == current_mode:
            label += " · выбрано"
        kb.button(text=label, callback_data=f"mode:{mode.key}")
    kb.button(text="⬅️ Назад", callback_data="menu:back")
    kb.adjust(1)
    return kb.as_markup()


def back_to_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="menu:root")]
        ]
    )


def subscription_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💎 1 месяц", callback_data="sub:plan:1m")
    kb.button(text="💎 3 месяца", callback_data="sub:plan:3m")
    kb.button(text="💎 12 месяцев", callback_data="sub:plan:12m")
    kb.button(text="⬅️ Назад", callback_data="menu:back")
    kb.adjust(1)
    return kb.as_markup()


def referrals_menu_kb(ref_link: str | None = None) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if ref_link:
        kb.button(text="Скопировать реферальную ссылку", callback_data="ref:copy")
    kb.button(text="⬅️ Назад", callback_data="menu:back")
    kb.adjust(1)
    return kb.as_markup()
