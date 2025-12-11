from __future__ import annotations

import logging
from typing import Tuple

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

CRYPTO_PAY_API_BASE = "https://pay.crypt.bot/api"


def is_cryptopay_configured() -> bool:
    """
    Проверяем, есть ли токен Crypto Pay в настройках.
    Без него оплачивать подписку нельзя.
    """
    return bool(getattr(settings, "cryptopay_api_token", None))


async def _cryptopay_request(method: str, payload: dict) -> dict:
    """
    Внутренняя функция для запросов к Crypto Pay API.
    """
    token = getattr(settings, "cryptopay_api_token", None)
    if not token:
        raise RuntimeError("CRYPTOPAY_API_TOKEN не задан в .env")

    headers = {
        "Crypto-Pay-API-Token": token,
        "Content-Type": "application/json",
    }

    url = f"{CRYPTO_PAY_API_BASE}{method}"

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    if not data.get("ok"):
        logger.error("Crypto Pay API error: %s", data)
        raise RuntimeError(f"Crypto Pay API error: {data!r}")

    return data["result"]


async def create_invoice_usdt(
    *,
    user_id: int,
    amount_usdt: float,
    period_months: int,
) -> Tuple[str, str]:
    """
    Создаёт инвойс в USDT.

    Возвращает:
        (invoice_id, pay_url)
    """
    desc = f"BlackBox GPT — Premium на {period_months} мес."

    payload = {
        "asset": "USDT",
        "amount": f"{amount_usdt:.2f}",
        "description": desc,
        # payload — произвольная строка, прилетает обратно в getInvoices.
        "payload": f"user:{user_id}:months:{period_months}",
        "expires_in": 3600,  # 1 час на оплату
        "allow_comments": False,
        "allow_anonymous": True,
    }

    result = await _cryptopay_request("/createInvoice", payload)
    invoice_id = str(result["invoice_id"])
    pay_url = result["pay_url"]
    return invoice_id, pay_url


async def get_invoice_status(invoice_id: str) -> str:
    """
    Получаем статус инвойса по его ID.

    Возможные статусы: "active", "paid", "expired".
    """
    payload = {
        "invoice_ids": [int(invoice_id)],
    }

    result = await _cryptopay_request("/getInvoices", payload)
    items = result.get("items") or result

    if not items:
        raise RuntimeError("Инвойс не найден в Crypto Pay")

    invoice = items[0]
    status = invoice["status"]
    return status
