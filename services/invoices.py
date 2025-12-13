from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Optional

import aiosqlite


@dataclass
class InvoiceRow:
    invoice_id: int
    user_id: int
    months: int
    amount: float
    asset: str
    status: str
    pay_url: str | None
    created_at: int
    paid_at: int
    rewarded: int
    raw_json: dict[str, Any]


async def insert(
    db: aiosqlite.Connection,
    *,
    invoice_id: int,
    user_id: int,
    months: int,
    amount: float,
    asset: str,
    status: str,
    pay_url: str | None,
    raw: dict[str, Any],
) -> None:
    # rewarded column may not exist during early migrations; keep resilient
    try:
        await db.execute(
            """
            INSERT OR REPLACE INTO invoices(invoice_id, user_id, months, amount, asset, status, pay_url, created_at, paid_at, rewarded, raw_json)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                invoice_id,
                user_id,
                months,
                amount,
                asset,
                status,
                pay_url,
                int(time.time()),
                0,
                json.dumps(raw, ensure_ascii=False),
            ),
        )
    except aiosqlite.OperationalError:
        await db.execute(
            """
            INSERT OR REPLACE INTO invoices(invoice_id, user_id, months, amount, asset, status, pay_url, created_at, paid_at, raw_json)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invoice_id,
                user_id,
                months,
                amount,
                asset,
                status,
                pay_url,
                int(time.time()),
                0,
                json.dumps(raw, ensure_ascii=False),
            ),
        )
    await db.commit()


async def update_status(
    db: aiosqlite.Connection,
    invoice_id: int,
    status: str,
    *,
    paid_at: int = 0,
    raw: dict[str, Any] | None = None,
) -> None:
    raw_str = json.dumps(raw, ensure_ascii=False) if raw is not None else None
    if raw_str is None:
        await db.execute("UPDATE invoices SET status=?, paid_at=? WHERE invoice_id=?", (status, paid_at, invoice_id))
    else:
        await db.execute(
            "UPDATE invoices SET status=?, paid_at=?, raw_json=? WHERE invoice_id=?",
            (status, paid_at, raw_str, invoice_id),
        )
    await db.commit()


async def mark_rewarded(db: aiosqlite.Connection, invoice_id: int) -> None:
    try:
        await db.execute("UPDATE invoices SET rewarded=1 WHERE invoice_id=?", (invoice_id,))
        await db.commit()
    except aiosqlite.OperationalError:
        return


async def get_pending(db: aiosqlite.Connection, limit: int = 50) -> list[InvoiceRow]:
    async with db.execute(
        "SELECT * FROM invoices WHERE status IN ('active') ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ) as cur:
        rows = await cur.fetchall()

    out: list[InvoiceRow] = []
    for r in rows:
        try:
            raw = json.loads(r["raw_json"] or "{}")
        except Exception:
            raw = {}
        rewarded = int(r["rewarded"]) if "rewarded" in r.keys() else 0
        out.append(
            InvoiceRow(
                invoice_id=r["invoice_id"],
                user_id=r["user_id"],
                months=r["months"],
                amount=float(r["amount"]),
                asset=r["asset"],
                status=r["status"],
                pay_url=r["pay_url"],
                created_at=r["created_at"],
                paid_at=r["paid_at"],
                rewarded=rewarded,
                raw_json=raw,
            )
        )
    return out


async def get_by_id(db: aiosqlite.Connection, invoice_id: int) -> Optional[InvoiceRow]:
    async with db.execute("SELECT * FROM invoices WHERE invoice_id=?", (invoice_id,)) as cur:
        r = await cur.fetchone()
    if not r:
        return None
    try:
        raw = json.loads(r["raw_json"] or "{}")
    except Exception:
        raw = {}
    rewarded = int(r["rewarded"]) if "rewarded" in r.keys() else 0
    return InvoiceRow(
        invoice_id=r["invoice_id"],
        user_id=r["user_id"],
        months=r["months"],
        amount=float(r["amount"]),
        asset=r["asset"],
        status=r["status"],
        pay_url=r["pay_url"],
        created_at=r["created_at"],
        paid_at=r["paid_at"],
        rewarded=rewarded,
        raw_json=raw,
    )
