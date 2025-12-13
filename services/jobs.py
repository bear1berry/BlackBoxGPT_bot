from __future__ import annotations

import time
from datetime import datetime
from zoneinfo import ZoneInfo

import aiosqlite
from aiogram import Bot

from services.crypto_pay import CryptoPayClient
from services import invoices as invoices_repo
from services import subscriptions as subs_repo
from services import users as users_repo
from bot import texts


REF_REWARD_DAYS = 7  # бонус за оплатившего реферала


async def _notify(bot: Bot, user_id: int, text: str) -> None:
    try:
        await bot.send_message(user_id, text)
    except Exception:
        return


async def handle_invoice_status(bot: Bot, db: aiosqlite.Connection, invoice_id: int, status: str, raw: dict) -> None:
    row = await invoices_repo.get_by_id(db, invoice_id)
    if not row:
        return

    if status == "paid" and row.status != "paid":
        paid_at = int(time.time())
        await invoices_repo.update_status(db, invoice_id, "paid", paid_at=paid_at, raw=raw)

        new_until = await subs_repo.activate_premium(db, row.user_id, row.months)
        dt = datetime.fromtimestamp(new_until, tz=ZoneInfo("UTC")).strftime("%Y-%m-%d")
        await _notify(bot, row.user_id, texts.PAYMENT_SUCCESS + f"\n\n📅 До: <b>{dt}</b>")

        # referral reward (one-time per invoice)
        if row.rewarded == 0:
            payer = await users_repo.get_user(db, row.user_id)
            if payer and payer.referrer_id:
                reward_seconds = REF_REWARD_DAYS * 24 * 3600
                ref_until = await users_repo.add_premium(db, payer.referrer_id, reward_seconds)
                ref_dt = datetime.fromtimestamp(ref_until, tz=ZoneInfo("UTC")).strftime("%Y-%m-%d")
                await invoices_repo.mark_rewarded(db, invoice_id)
                await _notify(
                    bot,
                    payer.referrer_id,
                    f"🎁 <b>Бонус за реферала</b>\n\nТвой друг оплатил Premium — тебе начислено <b>+{REF_REWARD_DAYS} дней</b>.\n📅 Теперь до: <b>{ref_dt}</b>",
                )

    elif status == "expired" and row.status != "expired":
        await invoices_repo.update_status(db, invoice_id, "expired", raw=raw)
        await _notify(bot, row.user_id, texts.PAYMENT_EXPIRED)


async def sync_active_invoices(bot: Bot, db: aiosqlite.Connection, cryptopay: CryptoPayClient) -> None:
    pending = await invoices_repo.get_pending(db, limit=50)
    if not pending:
        return
    ids = [p.invoice_id for p in pending]
    try:
        items = await cryptopay.get_invoices(invoice_ids=ids)
    except Exception:
        return

    for inv in items:
        await handle_invoice_status(bot, db, inv.invoice_id, inv.status, inv.raw)


async def downgrade_expired_subscriptions(db: aiosqlite.Connection) -> int:
    return await subs_repo.downgrade_expired(db)


async def send_daily_checkins(bot: Bot, db: aiosqlite.Connection) -> None:
    async with db.execute("SELECT user_id FROM users WHERE checkin_enabled = 1") as cur:
        rows = await cur.fetchall()
    for r in rows:
        await _notify(bot, int(r["user_id"]), texts.CHECKIN_PROMPT)
