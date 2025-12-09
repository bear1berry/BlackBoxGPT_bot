# bot/services/payments_crypto.py
from __future__ import annotations
import logging
from datetime import datetime
from typing import Literal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import Subscription, User, calculate_expiry

logger = logging.getLogger(__name__)

PlanCode = Literal["1m", "3m", "12m"]

PLAN_TO_AMOUNT_USD: dict[PlanCode, float] = {
    "1m": 7.99,
    "3m": 25.99,
    "12m": 89.99,
}


async def create_invoice(
    session: AsyncSession,
    user: User,
    plan: PlanCode,
) -> tuple[str, int]:
    """
    Создаёт инвойс через Crypto Pay API и запись в базе.
    Возвращает (invoice_url, invoice_id).
    """
    if not settings.CRYPTO_PAY_API_TOKEN:
        raise RuntimeError("CRYPTO_PAY_API_TOKEN не задан")

    amount = PLAN_TO_AMOUNT_USD[plan]

    headers = {
        "Content-Type": "application/json",
        "Crypto-Pay-API-Token": settings.CRYPTO_PAY_API_TOKEN,
    }
    payload = {
        "asset": settings.CRYPTO_PAY_CURRENCY,
        "amount": str(amount),
        "currency_type": "fiat",  # USD
        "fiat": "USD",
        "description": f"BlackBox GPT Premium ({plan})",
    }

    async with httpx.AsyncClient(base_url="https://pay.crypt.bot/api", timeout=30) as client:
        resp = await client.post("/createInvoice", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    if not data.get("ok"):
        raise RuntimeError(f"Crypto Pay error: {data}")

    invoice = data["result"]
    invoice_id = invoice["invoice_id"]
    url = invoice.get("mini_app_invoice_url") or invoice.get("bot_invoice_url")

    sub = Subscription(
        user_id=user.id,
        plan_code=plan,
        invoice_id=invoice_id,
        status="pending",
    )
    session.add(sub)
    await session.commit()

    return url, invoice_id


async def check_invoice_and_activate(
    session: AsyncSession,
    user: User,
) -> bool:
    """
    Проверяет последний pending инвойс пользователя.
    Если оплачен — активирует Premium и выставляет premium_until.
    Возвращает True, если статус изменился на paid.
    """
    if not settings.CRYPTO_PAY_API_TOKEN:
        return False

    stmt = (
        select(Subscription)
        .where(Subscription.user_id == user.id, Subscription.status == "pending")
        .order_by(Subscription.id.desc())
        .limit(1)
    )
    res = await session.execute(stmt)
    sub = res.scalar_one_or_none()
    if sub is None:
        return False

    headers = {
        "Content-Type": "application/json",
        "Crypto-Pay-API-Token": settings.CRYPTO_PAY_API_TOKEN,
    }
    payload = {
        "invoice_ids": [sub.invoice_id],
    }

    async with httpx.AsyncClient(base_url="https://pay.crypt.bot/api", timeout=30) as client:
        resp = await client.post("/getInvoices", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    if not data.get("ok"):
        logger.error("Crypto Pay getInvoices error: %s", data)
        return False

    invoices = data["result"]["items"]
    if not invoices:
        return False

    invoice = invoices[0]
    status = invoice["status"]  # e.g. "paid", "active", "expired"

    if status != "paid":
        return False

    # Активируем Premium
    months = {"1m": 1, "3m": 3, "12m": 12}[sub.plan_code]
    user.is_premium = True
    user.premium_until = calculate_expiry(months)
    sub.status = "paid"
    sub.expires_at = user.premium_until

    await session.commit()
    return True
