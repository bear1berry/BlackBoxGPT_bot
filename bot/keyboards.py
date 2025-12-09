# bot/keyboards.py
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
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


def modes_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
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
                KeyboardButton(text="⬅️ Назад в меню"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери режим…",
    )


def subscription_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💎 1 месяц — 7.99$"),
            ],
            [
                KeyboardButton(text="💎 3 месяца — 25.99$"),
            ],
            [
                KeyboardButton(text="💎 12 месяцев — 89.99$"),
            ],
            [
                KeyboardButton(text="⬅️ Назад в меню"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери план…",
    )


def referral_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📎 Моя реферальная ссылка"),
            ],
            [
                KeyboardButton(text="⬅️ Назад в меню"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Реферальная программа",
    )


def subscription_invoice_keyboard(invoice_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💸 Оплатить подписку", url=invoice_url
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Проверить оплату",
                    callback_data="sub_check_payment",
                )
            ],
        ]
    )
