from __future__ import annotations

import time
from dataclasses import dataclass

import aiosqlite

from services.crypto_pay import CryptoPayClient, Invoice
from services import invoices as invoices_repo


def invoice_payload(user_id: int, months: int) -> str:
    return f"sub:{user_id}:{months}:{int(time.time())}"


async def create_subscription_invoice(
    db: aiosqlite.Connection,
    cryptopay: CryptoPayClient,
    *,
    user_id: int,
    months: int,
    amount_usdt: float,
) -> Invoice:
    payload = invoice_payload(user_id, months)
    description = f"BlackBoxGPT Premium — {months} мес."
    inv = await cryptopay.create_invoice(
        amount=f"{amount_usdt:.2f}",
        asset="USDT",
        description=description,
        payload=payload,
        expires_in=3600,
        allow_comments=False,
        allow_anonymous=True,
    )
    await invoices_repo.insert(
        db,
        invoice_id=inv.invoice_id,
        user_id=user_id,
        months=months,
        amount=amount_usdt,
        asset="USDT",
        status=inv.status,
        pay_url=inv.bot_invoice_url,
        raw=inv.raw,
    )
    return inv
