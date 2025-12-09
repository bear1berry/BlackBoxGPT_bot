from __future__ import annotations

from typing import Optional

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from sqlalchemy import String, BigInteger, Boolean, DateTime, Text, select, func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from bot.config import settings
from bot.texts import build_main_menu_text


router = Router(name="navigation")


# --- DB setup (локальная лёгкая ORM-обёртка над существующей таблицей users) ---


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # текущий режим
    mode: Mapped[str] = mapped_column(String(32), default="universal")

    # премиум / подписка
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_until: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # рефералка
    referral_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, unique=True)
    referred_by: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # текст «о себе»
    about: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# В реальной базе здесь должен быть твой PostgreSQL DSN.
# Сейчас это in-memory SQLite, чтобы модуль был самодостаточным и не падал.
engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


# --- Константы / хелперы ---


MODE_LABELS = {
    "universal": "🧠 Универсальный",
    "medicine": "🩺 Медицина",
    "mentor": "🔥 Наставник",
    "business": "💼 Бизнес",
    "creative": "🎨 Креатив",
}


def build_main_menu_kb() -> InlineKeyboardMarkup:
    """
    Нижний таскбар с 4 разделами.
    """
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
                    text="💎 1 месяц — 7.99 $", callback_data="sub:1m"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 3 месяца — 25.99 $", callback_data="sub:3m"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💎 12 месяцев — 89.99 $", callback_data="sub:12m"
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


async def get_or_create_user(
    session: AsyncSession,
    tg_id: int,
    username: str | None,
    full_name: str | None,
) -> User:
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            tg_id=tg_id,
            username=username,
            full_name=full_name,
            mode="universal",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return user


# --- Handlers ---


@router.callback_query(F.data == "nav:modes")
async def open_modes(callback: CallbackQuery) -> None:
    async with async_session_maker() as session:
        tg = callback.from_user
        full_name = " ".join(
            part for part in [tg.first_name, tg.last_name] if part
        ) or tg.full_name or tg.username or "Гость"

        user = await get_or_create_user(
            session=session,
            tg_id=tg.id,
            username=tg.username,
            full_name=full_name,
        )

        # Текст со списком режимов
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

    async with async_session_maker() as session:
        tg = callback.from_user
        full_name = " ".join(
            part for part in [tg.first_name, tg.last_name] if part
        ) or tg.full_name or tg.username or "Гость"

        user = await get_or_create_user(
            session=session,
            tg_id=tg.id,
            username=tg.username,
            full_name=full_name,
        )

        user.mode = mode
        await session.commit()
        await session.refresh(user)

        await callback.message.edit_text(
            build_main_menu_text(user),
            reply_markup=build_main_menu_kb(),
        )
        await callback.answer(
            f"✅ Режим обновлён: {MODE_LABELS.get(mode, mode)}.",
            show_alert=False,
        )


@router.callback_query(F.data == "nav:profile")
async def open_profile(callback: CallbackQuery) -> None:
    async with async_session_maker() as session:
        tg = callback.from_user
        full_name = " ".join(
            part for part in [tg.first_name, tg.last_name] if part
        ) or tg.full_name or tg.username or "Гость"

        user = await get_or_create_user(
            session=session,
            tg_id=tg.id,
            username=tg.username,
            full_name=full_name,
        )

        # Публичная t.me ссылка пользователя
        if tg.username:
            tme_link = f"https://t.me/{tg.username}"
        else:
            tme_link = "—"

        # Реферальная ссылка (если есть код)
        if user.referral_code:
            ref_link = f"https://t.me/{settings.bot_username}?start={user.referral_code}"
        else:
            ref_link = "Реферальный код появится после первого запуска из бота."

        text_lines = [
            "👤 <b>Твой профиль</b>\n",
            f"🆔 <b>ID:</b> <code>{tg.id}</code>",
            f"🙋‍♂️ <b>Имя:</b> {full_name}",
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
    async with async_session_maker() as session:
        tg = callback.from_user
        full_name = " ".join(
            part for part in [tg.first_name, tg.last_name] if part
        ) or tg.full_name or tg.username or "Гость"

        user = await get_or_create_user(
            session=session,
            tg_id=tg.id,
            username=tg.username,
            full_name=full_name,
        )

        if not user.referral_code:
            # простой детерминированный код на базе tg_id
            user.referral_code = f"ref{tg.id}"
            await session.commit()
            await session.refresh(user)

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
    async with async_session_maker() as session:
        tg = callback.from_user
        full_name = " ".join(
            part for part in [tg.first_name, tg.last_name] if part
        ) or tg.full_name or tg.username or "Гость"

        user = await get_or_create_user(
            session=session,
            tg_id=tg.id,
            username=tg.username,
            full_name=full_name,
        )

        await callback.message.edit_text(
            build_main_menu_text(user),
            reply_markup=build_main_menu_kb(),
        )
        await callback.answer()
