from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from aiohttp import web
from aiogram import Bot
import aiosqlite

from services.crypto_pay import CryptoPayClient, verify_signature
from services import invoices as invoices_repo
from services.jobs import handle_invoice_status


def _parse_iso(dt_str: str) -> datetime | None:
    try:
        # CryptoPay uses ISO 8601
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None


def create_app(
    *,
    bot: Bot,
    db: aiosqlite.Connection,
    cryptopay: CryptoPayClient,
    webhook_secret: str,
) -> web.Application:
    app = web.Application()

    async def health(_: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    async def cryptopay_webhook(request: web.Request) -> web.Response:
        # secret in path
        if request.match_info.get("secret") != webhook_secret:
            return web.Response(status=404, text="not found")

        raw = await request.read()
        sig = request.headers.get("crypto-pay-api-signature")
        if not verify_signature(cryptopay.api_token, raw, sig):
            return web.Response(status=401, text="bad signature")

        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            return web.Response(status=400, text="bad json")

        # optional freshness check
        req_date = payload.get("request_date")
        if isinstance(req_date, str):
            dt = _parse_iso(req_date)
            if dt:
                age = abs((datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds())
                if age > 60 * 60:  # 1 hour
                    return web.Response(status=400, text="stale")

        update_type = payload.get("update_type")
        if update_type == "invoice_paid":
            inv = payload.get("payload") or {}
            invoice_id = int(inv.get("invoice_id", 0) or 0)
            status = str(inv.get("status") or "paid")
            if invoice_id:
                await handle_invoice_status(bot, db, invoice_id, status, inv)

        return web.json_response({"ok": True})

    app.router.add_get("/health", health)
    app.router.add_post("/cryptopay/webhook/{secret}", cryptopay_webhook)
    return app
