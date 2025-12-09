from __future__ import annotations

from datetime import datetime
from typing import Optional


def _format_mode(mode: Optional[str]) -> str:
    mode = (mode or "universal").lower()
    mapping = {
        "universal": "Универсальный",
        "medicine": "Медицина",
        "mentor": "Наставник",
        "business": "Бизнес",
        "creative": "Креатив",
    }
    return mapping.get(mode, "Универсальный")


def _format_subscription(
    tier: Optional[str],
    expires_at: Optional[datetime],
) -> str:
    tier = (tier or "free").lower()
    if tier == "premium":
        if expires_at:
            return (
                "Статус: Premium\n"
                f"Действует до: {expires_at:%d.%m.%Y %H:%M}"
            )
        return "Статус: Premium\nСрок действия: не определён"
    return "Статус: Free\nРасширенные возможности доступны в Premium."


# ---------- ОНБОРДИНГ ----------


def build_onboarding_text(name: Optional[str]) -> str:
    name = name or "друг"
    return (
        f"Привет, {name}!\n\n"
        "Ты в BlackBox GPT — универсальном ИИ-ассистенте.\n"
        "Внизу экрана — меню с режимами и разделами.\n"
        "Можешь сразу написать свой первый запрос."
    )


# ---------- ГЛАВНЫЙ ЭКРАН ----------


def build_main_menu_text(current_mode: Optional[str]) -> str:
    mode_text = _format_mode(current_mode)
    return (
        "BlackBox GPT — Universal AI Assistant\n\n"
        f"Текущий режим: {mode_text}\n\n"
        "Как пользоваться:\n"
        "• Выбери режим в меню «Режимы»\n"
        "• Открой «Профиль», чтобы увидеть статус и реферальную ссылку\n"
        "• В «Подписка» — включи Premium\n"
        "• В «Рефералы» — забирай бонусы за друзей\n\n"
        "Просто напиши запрос, я отвечу развернуто и структурировано."
    )


def build_modes_text() -> str:
    return (
        "Режимы BlackBox GPT\n\n"
        "Универсальный — для любых вопросов.\n"
        "Медицина — аккуратные ответы, справочный режим.\n"
        "Наставник — мышление, дисциплина, развитие.\n"
        "Бизнес — идеи, упаковка, стратегии, тексты.\n"
        "Креатив — концепты, истории, контент.\n\n"
        "Выбери режим в меню ниже."
    )


# ---------- ПРОФИЛЬ ----------


def build_profile_text(
    first_name: Optional[str],
    username: Optional[str],
    current_mode: Optional[str],
    subscription_tier: Optional[str],
    subscription_expires_at: Optional[datetime],
    ref_link: str,
    referrals_count: int,
) -> str:
    name = first_name or "Без имени"
    uname = f"@{username}" if username else "—"
    mode_text = _format_mode(current_mode)
    sub_text = _format_subscription(subscription_tier, subscription_expires_at)

    return (
        "Профиль\n\n"
        f"Имя: {name}\n"
        f"Username: {uname}\n"
        f"Режим: {mode_text}\n\n"
        f"{sub_text}\n\n"
        "Реферальная программа\n"
        f"Привлечено пользователей: {referrals_count}\n\n"
        "Твоя личная ссылка:\n"
        f"{ref_link}\n\n"
        "Отправь её друзьям, за каждого активного — бонусные дни Premium."
    )


# ---------- ПОДПИСКА ----------


def build_subscription_text(
    subscription_tier: Optional[str],
    subscription_expires_at: Optional[datetime],
) -> str:
    sub_text = _format_subscription(subscription_tier, subscription_expires_at)
    return (
        "Подписка BlackBox GPT\n\n"
        f"{sub_text}\n\n"
        "Планы:\n"
        "• 1 месяц — $7.99\n"
        "• 3 месяца — $25.99\n"
        "• 12 месяцев — $89.99\n\n"
        "Оплата идёт через Crypto Bot.\n"
        "После успешной оплаты Premium активируется автоматически."
    )


# ---------- РЕФЕРАЛЫ ----------


def build_referrals_text(ref_link: str, referrals_count: int) -> str:
    return (
        "Реферальная программа\n\n"
        "Делись ссылкой и получай бонусные дни Premium за друзей.\n\n"
        f"Привлечено пользователей: {referrals_count}\n\n"
        "Твоя личная ссылка:\n"
        f"{ref_link}\n\n"
        "Кнопка ниже откроет ссылку сразу в Telegram."
    )
