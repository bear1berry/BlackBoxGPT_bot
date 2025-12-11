from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from ..db.db import db
from ..services.storage import ensure_user
from ..services.payments_crypto import crypto_pay
from ..keyboards.main_menu import subscription_keyboard

router = Router()

# Планы подписки
SUBSCRIPTION_PLANS = {
    "1m": {
        "months": 1,
        "price": Decimal("6.99"),
        "title": "1 месяц",
    },
    "3m": {
        "months": 3,
        "price": Decimal("20.99"),
        "title": "3 месяца",
    },
    "12m": {
        "months": 12,
        "price": Decimal("59.99"),
        "title": "12 месяцев",
    },
}


async def _activate_premium(user_id: int, plan_code: str) -> datetime:
    """
    Создаём запись в subscriptions + обновляем users.is_premium.
    """
    plan = SUBSCRIPTION_PLANS[plan_code]
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=30 * plan["months"])

    # Закроем старые активные подписки, если есть
    await db.execute(
        """
        UPDATE subscriptions
        SET status = 'expired', updated_at = NOW()
        WHERE user_id = $1 AND status = 'active' AND expires_at <= NOW()
        """,
        user_id,
    )

    await db.execute(
        """
        INSERT INTO subscriptions (user_id, tier, status, started_at, expires_at)
        VALUES ($1, $2, 'active', $3, $4)
        """,
        user_id,
        f"premium_{plan_code}",
        now,
        expires_at,
    )

    await db.execute(
        """
        UPDATE users
        SET is_premium = TRUE,
            subscription_expires_at = $2
        WHERE id = $1
        """,
        user_id,
        expires_at,
    )

    return expires_at


@router.message(F.text == "💎 Подписка")
async def open_subscription_menu(message: Message) -> None:
    await message.answer(
        "💎 <b>Подписка BlackBox GPT</b>\n\n"
        "• Базовый план (бесплатно): 10 запросов навсегда.\n"
        "• Premium — до 100 запросов в день, доступ к профессиональному "
        "режиму и web-поиску.\n\n"
        "Выбери срок подписки:",
        reply_markup=subscription_keyboard,
    )


@router.callback_query(F.data.startswith("sub:plan:"))
async def handle_subscription_plan(callback: CallbackQuery) -> None:
    _, _, plan_code = callback.data.split(":")
    plan = SUBSCRIPTION_PLANS.get(plan_code)
    if not plan:
        await callback.answer("Неизвестный план.", show_alert=True)
        return

    user_row = await ensure_user(callback.from_user)

    amount_str = f"{plan['price']:.2f}"
    description = f"BlackBox GPT Premium — {plan['title']}"

    invoice = await crypto_pay.create_invoice(
        amount=amount_str,
        asset="USDT",
        description=description,
        payload=f"user={user_row['id']};plan={plan_code}",
    )

    await db.execute(
        """
        INSERT INTO payments (user_id, amount, currency, status, provider, provider_invoice_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        user_row["id"],
        plan["price"],
        "USDT",
        "pending",
        "cryptopay",
        str(invoice.invoice_id),
    )

    await callback.message.answer(
        "💎 <b>Счёт создан.</b>\n\n"
        f"План: <b>{plan['title']}</b>\n"
        f"Сумма: <b>{amount_str} USDT</b>\n\n"
        "Нажми на ссылку ниже, чтобы оплатить через CryptoBot:",
    )
    await callback.message.answer(
        f"👉 <a href=\"{invoice.pay_url}\">Оплатить в CryptoBot</a>",
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data == "sub:check")
async def check_subscription_payment(callback: CallbackQuery) -> None:
    user_row = await ensure_user(callback.from_user)

    pending_rows = await db.fetch(
        """
        SELECT id, amount, currency, provider_invoice_id
        FROM payments
        WHERE user_id = $1 AND status = 'pending' AND provider = 'cryptopay'
        ORDER BY created_at DESC
        LIMIT 10
        """,
        user_row["id"],
    )

    if not pending_rows:
        await callback.answer("Нет неоплаченных счетов.", show_alert=True)
        return

    invoice_ids = [int(row["provider_invoice_id"]) for row in pending_rows]
    invoices = await crypto_pay.get_invoices(invoice_ids)
    invoices_by_id = {inv.invoice_id: inv for inv in invoices}

    activated = False

    for row in pending_rows:
        inv = invoices_by_id.get(int(row["provider_invoice_id"]))
        if not inv:
            continue

        if inv.status == "paid":
            # Оплата прошла
            await db.execute(
                "UPDATE payments SET status = 'paid', updated_at = NOW() WHERE id = $1",
                row["id"],
            )

            plan_code = None
            for code, plan in SUBSCRIPTION_PLANS.items():
                if float(plan["price"]) == float(row["amount"]):
                    plan_code = code
                    break

            if not plan_code:
                continue

            expires_at = await _activate_premium(user_row["id"], plan_code)
            activated = True

        elif inv.status in {"expired", "cancelled"}:
            await db.execute(
                "UPDATE payments SET status = $2, updated_at = NOW() WHERE id = $1",
                row["id"],
                inv.status,
            )

    if activated:
        await callback.message.answer(
            "✅ Подписка <b>Premium</b> активирована!\n\n"
            "Теперь твой лимит — до 100 запросов в день.\n"
            "Спасибо за поддержку проекта 🔥"
        )
    else:
        await callback.message.answer(
            "Пока не вижу оплаченных счетов.\n\n"
            "Если ты только что оплатил — подожди 10–20 секунд и "
            "нажми «🔁 Проверить оплату» ещё раз."
        )

    await callback.answer()
