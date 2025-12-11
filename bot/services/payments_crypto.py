from __future__ import annotations

from typing import Optional

import httpx

from ..config import settings
from ..db.db import db

BASE_URL = "https://pay.crypt.bot/api/"


class CryptoPayClient:
    def __init__(self, token: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"Crypto-Pay-API-Token": token},
            timeout=30.0,
        )

    async def create_invoice(self, asset: str, amount: float, description: str, payload: str) -> dict:
        response = await self._client.post(
            "createInvoice",
            json={
                "asset": asset,
                "amount": str(amount),
                "description": description,
                "payload": payload,
            },
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Crypto Pay error: {data}")
        return data["result"]


_crypto_client: Optional[CryptoPayClient] = None
if settings.crypto_pay_token:
    _crypto_client = CryptoPayClient(settings.crypto_pay_token)


async def create_subscription_invoice(user_id: int, months: int, total_price: float) -> Optional[str]:
    """Создаёт инвойс в Crypto Pay. Возвращает ссылку на оплату или None, если токен не настроен."""
    if _crypto_client is None:
        return None

    payload = f"sub:{user_id}:{months}"
    invoice = await _crypto_client.create_invoice(
        asset=settings.crypto_currency,
        amount=total_price,
        description=f"Подписка BlackBoxGPT на {months} мес.",
        payload=payload,
    )
    pay_url = invoice.get("pay_url")
    external_id = invoice.get("invoice_id") or str(invoice.get("id"))

    await db.execute(
        """
        INSERT INTO payments (user_id, provider, external_id, amount, currency, status)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        user_id,
        "cryptopay",
        str(external_id),
        total_price,
        settings.crypto_currency,
        "pending",
    )

    return pay_url
