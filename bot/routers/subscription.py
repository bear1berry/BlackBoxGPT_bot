from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from ..config import settings
from ..keyboards.main_menu import (
    subscription_keyboard,
    main_menu_keyboard,
)
from ..services.storage import ensure_user

logger = logging.getLogger(__name__)

router = Router()


@dataclass(frozen=True)
class Plan:
    button_text: str
    code: str
    months: int
    price_usdt: float
    title: str


PLANS: dict[str, Plan] = {
    "💎 1 месяц": Plan(
        button_text="💎 1 месяц",
        code="sub_1m",
        months=1,
        price_usdt=6.99,
        title="Подписка на 1 месяц",
    ),
    "💎 3 месяца": Plan(
        button_text="💎 3 месяца",
        code="sub_3m",
        months=3,
        price_usdt=20.99,
        title="Подписка на 3 месяца",
    ),
    "💎 12 месяцев": Plan(
        button_text="💎 12 месяцев",
        code="sub_12m",
        months=12,
        price_usdt=59.99,
        title="Подписка на 12 месяцев",
    ),
}


def _invoice_keyboard(pay_url: str) -> InlineKeyboardMarkup:
    """
    Инлайн-клавиатура под сообщением с оплатой.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить через Crypto Bot", url=pay_url)],
        ]
    )


@router.message(F.text == "💎 Подписка")
async def subscription_entry(message: Message) -> None:
    """
    Вход в раздел подписки.
    """
    text = (
        "💎 <b>Подписка</b>\n\n"
        "Выбери срок подписки, чтобы получить повышенные лимиты и приоритет.\n\n"
        "<b>Тарифы:</b>\n"
        "• <b>Базовый</b> — бесплатно, до 10 запросов, затем бот предложит оформить Premium.\n"
        "• <b>Premium</b> — до 100 запросов в день, приоритетные ответы, доступ к профессиональному режиму.\n"
    )

    await message.answer(
        text,
        reply_markup=subscription_keyboard(),
    )


async def _create_cryptobot_invoice(
    user_tg_id: int,
    plan: Plan,
) -> str:
    """
    Минимальный клиент для CryptoBot (Crypto Pay API).

    Возвращает URL для оплаты.
    """
    if not settings.cryptopay_api_token:
        raise RuntimeError("CRYPTOPAY_API_TOKEN is not configured")

    # Документация: https://help.crypt.bot/crypto-pay-api
    base_url = "https://pay.crypt.bot/api"
    headers = {
        "Crypto-Pay-API-Token": settings.cryptopay_api_token,
        "Content-Type": "application/json",
    }

    payload = {
        "asset": "USDT",
        "amount": str(plan.price_usdt),
        "currency_type": "crypto",  # платёж именно в USDT
        "description": plan.title,
        # Полезно закодировать пользователя и план в payload
        "payload": f"user:{user_tg_id}|plan:{plan.code}",
        # Чтобы инвойс не висел вечно
        "expires_in": 3600,  # 1 час
        "allow_anonymous": True,
        "allow_comments": False,
    }

    async with httpx.AsyncClient(base_url=base_url, timeout=15.0) as client:
        resp = await client.post("/createInvoice", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    if not data.get("ok"):
        logger.error("CryptoBot createInvoice error: %s", data)
        raise RuntimeError("CryptoBot returned error")

    result = data["result"]
    pay_url = result["pay_url"]
    invoice_id = result["invoice_id"]

    logger.info(
        "Created CryptoBot invoice: invoice_id=%s user_tg_id=%s plan=%s amount=%s",
        invoice_id,
        user_tg_id,
        plan.code,
        plan.price_usdt,
    )

    # ⚠️ Здесь мы пока НЕ пишем ничего в БД.
    # На следующем шаге можно:
    # - сохранить invoice_id в_
