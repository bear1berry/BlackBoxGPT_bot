from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from bot.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://pay.crypt.bot/api"


class CryptoPayError(Exception):
    pass


def _get_headers() -> dict[str, str]:
    if not settings.cryptopay_api_token:
        raise CryptoPayError("CRYPTOPAY_API_TOKEN не задан")
    return {
        "Crypto-Pay-API-Token": settings.cryptopay_api_token,
        "Content-Type": "application/json",
    }


async def create_invoice(
    amount: float,
    description: str,
    payload: str,
    asset: Optional[str] = None,
) -> Dict[str, Any]:
    """Создаёт инвойс через Crypto Bot.

    amount — в единицах выбранного актива (обычно USDT).
    """
    headers = _get_headers()
    data = {
        "asset": asset or settings.cryptopay_asset,
        "amount": float(f"{amount:.2f}"),
        "description": description[:1024],
        "payload": payload[:4096],
        "allow_comments": False,
        "allow_anonymous": True,
    }

    async with httpx.AsyncClient(timeout=30.0, base_url=BASE_URL) as client:
        resp = await client.post("/createInvoice", json=data, headers=headers)
        resp.raise_for_status()
        raw = resp.json()
        if not raw.get("ok"):
            logger.error("CryptoPay createInvoice error: %s", raw)
            raise CryptoPayError(str(raw))
        return raw["result"]


async def get_invoice(invoice_id: int) -> Dict[str, Any]:
    headers = _get_headers()
    params = {"invoice_ids": str(invoice_id)}

    async with httpx.AsyncClient(timeout=30.0, base_url=BASE_URL) as client:
        resp = await client.get("/getInvoices", params=params, headers=headers)
        resp.raise_for_status()
        raw = resp.json()
        if not raw.get("ok"):
            logger.error("CryptoPay getInvoices error: %s", raw)
            raise CryptoPayError(str(raw))

        invoices = raw.get("result", [])
        if not invoices:
            raise CryptoPayError(f"Invoice {invoice_id} not found")

        return invoices[0]
