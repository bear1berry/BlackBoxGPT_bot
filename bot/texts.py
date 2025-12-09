from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from bot.config import settings


MODE_LABELS = {
    "universal": "🧠 Универсальный",
    "medicine": "🩺 Медицина",
    "mentor": "🔥 Наставник",
    "business": "💼 Бизнес",
    "creative": "🎨 Креатив",
}


def get_mode_label(mode: str | None) -> str:
    return MODE_LABELS.get((mode or "universal").lower(), MODE_LABELS["universal"])


def build_onboarding_text(first_name: Optional[str]) -> str:
    name = first_name or "друг"
    return (
        f"👋 Привет, <b>{name}</b>!

"
        f"Ты в <b>BlackBox GPT — Universal AI Assistant</b>.

"
        "🧠 Это твой личный умный помощник:
"
        "• понимает свободный текст и контекст
"
        "• ищет информацию в сети через Perplexity
"
        "• помогает в медицине, бизнесе, креативе и развитии

"
        "⬇️ Внизу — панель навигации. Выбери режим или просто напиши свой запрос."
    )


def build_main_menu_text(current_mode: str | None) -> str:
    label = get_mode_label(current_mode)
    return (
        f"💠 <b>BlackBox GPT — Universal AI Assistant</b>

"
        f"Текущий режим: {label}

"
        "Напиши свой запрос — бот ответит как статья: короткий заголовок, структура, выводы.

"
        "Или пользуйся нижним меню:
"
        "🧠 Режимы · 👤 Профиль · 💎 Подписка · 👥 Рефералы"
    )


def build_modes_text() -> str:
    return (
        "🧠 <b>Режимы работы</b>

"
        "🧠 Универсальный — общий интеллект, любые темы.
"
        "🩺 Медицина — аккуратные медицинские объяснения.
"
        "🔥 Наставник — развитие, дисциплина, мотивация.
"
        "💼 Бизнес — стратегии, анализ, идеи.
"
        "🎨 Креатив — тексты, идеи, визуальные концепты.

"
        "Просто выбери режим — и дальше пиши свои запросы."
    )


def build_subscription_text(
    subscription_tier: str,
    subscription_expires_at: Optional[datetime],
) -> str:
    if subscription_tier == "premium" and subscription_expires_at:
        now = datetime.now(timezone.utc)
        left_days = max((subscription_expires_at - now).days, 0)
        expires_str = subscription_expires_at.strftime("%d.%m.%Y %H:%M")
        status_line = (
            f"💎 <b>Premium-статус активен</b>
"
            f"⏳ До отключения: ~{left_days} дн.
"
            f"📅 Дата окончания: {expires_str} (UTC)

"
        )
    else:
        status_line = "💎 <b>Сейчас у тебя Free-доступ</b>.

"

    return (
        "💎 <b>Подписка BlackBox GPT</b>

"
        + status_line +
        "Доступные планы (оплата через Crypto Bot):
"
        f"• 1 месяц — <b>${settings.subscription_price_1m:.2f}</b>
"
        f"• 3 месяца — <b>${settings.subscription_price_3m:.2f}</b>
"
        f"• 12 месяцев — <b>${settings.subscription_price_12m:.2f}</b>

"
        "После оплаты подписка активируется автоматически.
"
        "Рекомендация: начни с 1 месяца, протестируй, а потом бери 3 или 12."
    )


def build_profile_text(
    first_name: Optional[str],
    username: Optional[str],
    current_mode: str,
    subscription_tier: str,
    subscription_expires_at: Optional[datetime],
    ref_link: str,
    referrals_count: int,
) -> str:
    name = first_name or (username and f"@{username}") or "Пользователь"
    mode_label = get_mode_label(current_mode)

    if subscription_tier == "premium" and subscription_expires_at:
        now = datetime.now(timezone.utc)
        left_days = max((subscription_expires_at - now).days, 0)
        sub_line = f"💎 Статус: <b>Premium</b> (~{left_days} дн.)"
    else:
        sub_line = "💎 Статус: <b>Free</b>"

    return (
        f"👤 <b>Твой профиль</b>

"
        f"Имя: <b>{name}</b>
"
        f"Ник: <b>@{username}</b>

"
        f"Режим по умолчанию: {mode_label}
"
        f"{sub_line}
"
        f"👥 Приглашено друзей: <b>{referrals_count}</b>

"
        "🔗 <b>Твоя реферальная ссылка</b>:
"
        f"{ref_link}

"
        "Отправь её друзьям — за каждую оплачиваемую подписку
"
        f"они приносят тебе +{settings.referral_reward_days} дн. Premium."
    )


def build_referrals_text(
    ref_link: str,
    referrals_count: int,
) -> str:
    return (
        "👥 <b>Реферальная программа</b>

"
        "Как это работает:
"
        "1️⃣ Берёшь свою уникальную ссылку.
"
        "2️⃣ Отправляешь друзьям.
"
        "3️⃣ Они заходят в бота и оплачивают подписку.
"
        f"4️⃣ За каждого друга ты получаешь +{settings.referral_reward_days} дн. Premium.

"
        f"Твоя ссылка:
{ref_link}

"
        f"На сегодня у тебя уже: <b>{referrals_count}</b> приглашённых."
    )
