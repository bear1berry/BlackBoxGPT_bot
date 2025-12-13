from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


BTN_MODES = "🧠 Режимы"
BTN_PROFILE = "👤 Профиль"
BTN_SUBSCRIPTION = "💎 Подписка"
BTN_REFERRALS = "👥 Рефералы"
BTN_BACK = "⬅️ Назад"

BTN_MODE_UNIVERSAL = "🧠 Универсальный"
BTN_MODE_PRO = "🧠 Профессиональный"

BTN_SUB_1M = "💎 1 месяц"
BTN_SUB_3M = "💎 3 месяца"
BTN_SUB_12M = "💎 12 месяцев"

BTN_RENEW = "Продлить подписку"
BTN_INVITE = "👥 Пригласить друзей"
BTN_CHECKIN_TOGGLE = "🫂 Чек-ин (вкл/выкл)"


def kb_main() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(
        KeyboardButton(text=BTN_MODES),
        KeyboardButton(text=BTN_PROFILE),
    )
    b.row(
        KeyboardButton(text=BTN_SUBSCRIPTION),
        KeyboardButton(text=BTN_REFERRALS),
    )
    return b.as_markup(resize_keyboard=True, input_field_placeholder="Напиши запрос…")


def kb_modes() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text=BTN_MODE_UNIVERSAL), KeyboardButton(text=BTN_MODE_PRO))
    b.row(KeyboardButton(text=BTN_BACK))
    return b.as_markup(resize_keyboard=True)


def kb_subscription() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text=BTN_SUB_1M), KeyboardButton(text=BTN_SUB_3M))
    b.row(KeyboardButton(text=BTN_SUB_12M))
    b.row(KeyboardButton(text=BTN_BACK))
    return b.as_markup(resize_keyboard=True)


def kb_profile() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text=BTN_RENEW), KeyboardButton(text=BTN_INVITE))
    b.row(KeyboardButton(text=BTN_CHECKIN_TOGGLE))
    b.row(KeyboardButton(text=BTN_BACK))
    return b.as_markup(resize_keyboard=True)


def kb_back_only() -> ReplyKeyboardMarkup:
    b = ReplyKeyboardBuilder()
    b.row(KeyboardButton(text=BTN_BACK))
    return b.as_markup(resize_keyboard=True)


def ikb_continue(token: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="➡️ Продолжить", callback_data=f"cont:{token}")
    return b.as_markup()
