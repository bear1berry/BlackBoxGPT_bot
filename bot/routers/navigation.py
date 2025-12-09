from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import settings
from bot.texts import build_main_menu_text


router = Router(name="navigation")


@dataclass
class UserState:
    tg_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None

    mode: str = "universal"
    is_premium: bool = False
    referral_code: Optional[str] = None
    referred_by: Optional[str] = None
    about: Optional[str] = None


_USERS: Dict[int, UserState] = {}


def _get_full_name(cb_from) -> str:
    parts = [cb_from.first_name, cb_from.last_name]
    name = " ".join(p for p in parts if p)
    return name or cb_from.full_name or cb_from.username or "Гость"


def get_or_create_user_state(cb_from) -> UserState:
    tg_id = cb_from.id
    if tg_id in _USERS:
        user = _USERS[tg_id]
    else:
        user = UserState(
            tg_id=tg_id,
            username=cb_from.username,
            full_name=_get_full_name(cb_from),
        )
        _USERS[tg_id] = user

    user.username = cb_from.username
    user.full_name = _get_full_name(cb_from)
    return user


MODE_LABELS = {
    "universal": "🧠 Универсальный",
    "medicine": "🩺 Медицина",
    "mentor": "🔥 Наставник",
    "business": "💼 Бизнес",
    "creative": "🎨 Креатив",
}


def build_main_menu_kb() -> InlineKeyboardMarkup:
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


def build_modes_kb(current_mode: str) -> InlineKeyboardMarkup:
    rows = []
    for key, label in MODE_LABELS.items():
        prefix = "✅ " if key == current_mode else ""
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{prefix}{label}",
                    callback_data=f"mode:{key}",
                )
            ]
        )

    rows.append(
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:back_main")]
    )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_profile_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:back_main")]
        ]
    )


def build_subscription_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💎 1 месяц — 7.99 $",
                    callback_data="sub:1m",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 3 месяца — 25.99 $",
                    callback_data="sub:3m",
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 12 месяцев — 89.99 $",
                    callback_data="sub:12m",
                )
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:back_main")],
        ]
    )


def build_referrals_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:back_main")]
        ]
    )


@router.callback_query(F.data == "nav:modes")
async def open_modes(callback: CallbackQuery) -> None:
    user = get_or_create_user_state(callback.from_user)

    modes_lines = []
    for key, label in MODE_LABELS.items():
        prefix = "✅" if key == user.mode else "•"
        modes_lines.append(f"{prefix} {label} — {key}")

    text = (
        "🧠 <b>Режимы работы BlackBox GPT</b>\n\n"
        "Выбери, как я буду думать и отвечать для тебя прямо сейчас:\n\n"
        + "\n".join(modes_lines)
        + "\n\n"
        "Нажми на режим ниже, чтобы мгновенно переключиться."
    )

    await callback.message.edit_text(
        text,
        reply_markup=build_modes_kb(user.mode),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mode:"))
async def switch_mode(callback: CallbackQuery) -> None:
    mode = callback.data.split(":", 1)[1]

    if mode not in MODE_LABELS:
        mode = "universal"

    user = get_or_create_user_state(callback.from_user)
    user.mode = mode

    await callback.message.edit_text(
        build_main_menu_text(user),
        reply_markup=build_main_menu_kb(),
    )
    await callback.answer(
        text=f"✅ Режим обновлён: {MODE_LABELS.get(mode, mode)}.",
        show_alert=False,
    )


@router.callback_query(F.data == "nav:profile")
async def open_profile(callback: CallbackQuery) -> None:
    user = get_or_create_user_state(callback.from_user)
    tg = callback.from_user

    if tg.username:
        tme_link = f"https://t.me/{tg.username}"
    else:
        tme_link = "—"

    if user.referral_code:
        ref_link = f"https://t.me/{settings.bot_username}?start={user.referral_code}"
    else:
        ref_link = "Реферальный код появится после первого запуска из бота."

    text_lines = [
        "👤 <b>Твой профиль</b>\n",
        f"🆔 <b>ID:</b> <code>{tg.id}</code>",
        f"🙋‍♂️ <b>Имя:</b> {user.full_name}",
        f"🔗 <b>t.me:</b> {tme_link}",
        "",
        f"🧠 <b>Текущий режим:</b> {MODE_LABELS.get(user.mode, user.mode)}",
        f"💎 <b>Премиум:</b> {'активен' if user.is_premium else 'нет'}",
        "",
        "<b>Реферальная ссылка:</b>",
        f"<code>{ref_link}</code>",
    ]

    if user.about:
        text_lines.append("")
        text_lines.append("📝 <b>О себе:</b>")
        text_lines.append(user.about)

    text = "\n".join(text_lines)

    await callback.message.edit_text(
        text,
        reply_markup=build_profile_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "nav:subscription")
async def open_subscription(callback: CallbackQuery) -> None:
    text = (
        "💎 <b>Подписка BlackBox GPT Premium</b>\n\n"
        "✅ Доступ к мощным моделям Perplexity + DeepSeek\n"
        "✅ Приоритетная очередь и быстрый стриминг ответов\n"
        "✅ Увеличенные лимиты и продвинутая память\n\n"
        "Выбери срок подписки, оплата проходит через Crypto Bot в USDT.\n"
        "После успешной оплаты подписка активируется автоматически."
    )

    await callback.message.edit_text(
        text,
        reply_markup=build_subscription_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "nav:referrals")
async def open_referrals(callback: CallbackQuery) -> None:
    user = get_or_create_user_state(callback.from_user)

    if not user.referral_code:
        user.referral_code = f"ref{user.tg_id}"

    ref_link = f"https://t.me/{settings.bot_username}?start={user.referral_code}"

    text = (
        "👥 <b>Реферальная программа</b>\n\n"
        "Приглашай друзей в BlackBox GPT и получай бонусы.\n"
        "За каждого оплаченного друга начисляются дополнительные дни Premium.\n\n"
        "Твоя персональная ссылка:\n"
        f"<code>{ref_link}</code>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=build_referrals_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "nav:back_main")
async def back_to_main(callback: CallbackQuery) -> None:
    user = get_or_create_user_state(callback.from_user)

    await callback.message.edit_text(
        build_main_menu_text(user),
        reply_markup=build_main_menu_kb(),
    )
    await callback.answer()
