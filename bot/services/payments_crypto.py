from __future__ import annotations

import logging
from typing import Optional

import httpx

from ..config import get_settings


logger = logging.getLogger(__name__)


async def create_invoice(
    amount_usdt: float,
    description: str,
    payload: str,
) -> Optional[str]:
    """
    Создаёт инвойс через Crypto Bot и возвращает ссылку на оплату.
    """
    settings = get_settings()
    if not settings.crypto_bot_token:
        logger.warning("[CryptoPayClient] CRYPTO_BOT_TOKEN is not set")
        return None

    url = "https://pay.crypt.bot/api/createInvoice"
    headers = {
        "Crypto-Pay-API-Token": settings.crypto_bot_token,
        "Content-Type": "application/json",
    }
    json_body = {
        "asset": "USDT",
        "amount": str(amount_usdt),
        "description": description,
        "payload": payload,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=json_body, headers=headers)
        data = resp.json()

    if not data.get("ok"):
        logger.error("CryptoBot error: %s", data)
        return None

    result = data.get("result") or {}
    return result.get("pay_url")
