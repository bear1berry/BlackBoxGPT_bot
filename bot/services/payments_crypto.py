from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional, Tuple

import httpx

from ..config import settings
from ..db.db import db
from .storage import create_subscription

log = logging.getLogger(__name__)


CRYPTO_PAY_BASE_URL = "https://pay.crypt.bot/api"


@dataclass(frozen=True)
class Plan:
    code: str
    title: str
    months: int
    amount_usdt: Decimal


PLANS: Dict[str, Plan] = {
    "premium_1m": Plan("premium_1m", "Premium 1 месяц", 1, Decimal("6.99")),
    "premium_3m": Plan("premium_3m", "Premium 3 месяца", 3, Decimal("20.99")),
    "premium_12m": Plan("premium_12m", "Premium 12 месяцев", 12, Decimal("59.99")),
}


async def _api_request(
    method: str,
    payload: Optional[dict] = None,
) -> dict:
    if not settings.cryptopay_api_token:
        raise RuntimeError("CRYPTOPAY_API_TOKEN is not configured in .env")

    headers = {
        "Crypto-Pay-API-Token": settings.cryptopay_api_token,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(base_url=CRYPTO_PAY_BASE_URL, timeout=30) as client:
        resp = await client.post(f"/{method}", headers=headers, json=payload or {})
        resp.raise_for_status()
        data = resp.json()

    if not data.get("ok", False):
        raise RuntimeError(f"CryptoPay API error: {data}")

    return data["result"]


async def create_invoice_for_user(user_id: int, plan_code: str) -> Tuple[int, str]:
    """
    Создать инвойс в Crypto Bot и записать его в таблицу payments.
    Возвращает (payment_id в БД, pay_url).
    """
    if plan_code not in PLANS:
        raise ValueError(f"Unknown plan code: {plan_code}")

    plan = PLANS[plan_code]

    result = await _api_request(
        "createInvoice",
        {
            "asset": "USDT",
            "amount": str(plan.amount_usdt),
            "description": plan.title,
            "currency_type": "crypto",
        },
    )

    invoice_id = int(result["invoice_id"])
    pay_url = result["pay_url"]

    row = await db.fetchrow(
        """
        INSERT INTO payments (user_id, invoice_id, plan_code, amount, asset, status, pay_url, raw)
        VALUES ($1, $2, $3, $4, $5, 'pending', $6, $7)
        RETURNING id
        """,
        user_id,
        invoice_id,
        plan.code,
        plan.amount_usdt,
        "USDT",
        pay_url,
        result,
    )

    payment_id = int(row["id"])
    return payment_id, pay_url


async def _update_payment_status(payment_id: int, status: str) -> None:
    await db.execute(
        "UPDATE payments SET status=$2, paid_at = CASE WHEN $2='paid' THEN NOW() ELSE paid_at END WHERE id=$1",
        payment_id,
        status,
    )


async def refresh_user_payments_and_subscriptions(user_id: int) -> None:
    """
    Проверяем все PENDING-платежи пользователя в Crypto Pay.
    Если какой-то инвойс оплачен — создаём подписку и отмечаем платёж как paid.
    """
    pending = await db.fetch(
        """
        SELECT id, invoice_id, plan_code
        FROM payments
        WHERE user_id=$1 AND status='pending'
        """,
        user_id,
    )

    if not pending:
        return

    invoice_ids = ",".join(str(row["invoice_id"]) for row in pending)

    result = await _api_request(
        "getInvoices",
        {
            "invoice_ids": invoice_ids,
        },
    )

    invoices_by_id = {int(i["invoice_id"]): i for i in result["items"]}

    for row in pending:
        payment_id = int(row["id"])
        invoice_id = int(row["invoice_id"])
        plan_code = row["plan_code"]

        info = invoices_by_id.get(invoice_id)
        if not info:
            continue

        status = info["status"]  # 'active', 'paid', 'expired', ...
        if status == "paid":
            plan = PLANS.get(plan_code)
            if not plan:
                log.warning("Unknown plan_code on payment %s", plan_code)
                continue

            await create_subscription(user_id, plan.code, plan.months, payment_id)
            await _update_payment_status(payment_id, "paid")
            log.info("Activated subscription %s for user %s", plan.code, user_id)
        elif status in {"expired", "canceled"}:
            await _update_payment_status(payment_id, status)
