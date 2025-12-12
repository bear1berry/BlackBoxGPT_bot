import os
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import asyncpg
import httpx

CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN", "")
API_URL = "https://pay.crypt.bot/api"
DB_DSN = os.getenv("DB_DSN", "")


class CryptoPayError(Exception):
    """Base error for Crypto Bot API."""


class CryptoPayClient:
    """
    Лёгкий клиент для Crypto Bot API.
    Возвращает уже распакованный `result` из JSON-ответа.
    """

    def __init__(self, token: Optional[str] = None, api_url: str = API_URL) -> None:
        self.token = token or CRYPTO_BOT_TOKEN
        if not self.token:
            # Не падаем сразу, но дадим понять при первом вызове.
            print("[CryptoPayClient] WARNING: CRYPTO_BOT_TOKEN is not set")
        self.api_url = api_url
        self._client = httpx.AsyncClient(
            base_url=self.api_url,
            headers={"Crypto-Pay-API-Token": self.token},
            timeout=20.0,
        )

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        resp = await self._client.request(
            method=method,
            url=path,
            params=params,
            json=json_data,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise CryptoPayError(f"Crypto Bot API error: {data}")
        # API возвращает полезную нагрузку в поле `result`
        return data["result"]

    async def create_invoice(self, **payload: Any) -> Dict[str, Any]:
        """
        Обертка над /createInvoice.
        См. доку: https://help.crypt.bot/crypto-pay-api#createinvoice
        """
        return await self._request(
            "POST",
            "/createInvoice",
            json_data=payload,
        )

    async def get_invoices(self, **payload: Any) -> Dict[str, Any]:
        """
        Обертка над /getInvoices.
        См. доку: https://help.crypt.bot/crypto-pay-api#getinvoices
        """
        return await self._request(
            "GET",
            "/getInvoices",
            params=payload,
        )


_crypto_client = CryptoPayClient()


@dataclass(frozen=True)
class SubscriptionPlan:
    """
    Описание подписки, завязанной на CryptoBot-инвойс.
    key  – текст кнопки (то, что приходит в message.text).
    tier – уровень подписки в нашей системе (например, 'premium').
    months – длительность подписки в месяцах.
    price_usdt – стоимость в USDT.
    """
    key: str
    tier: str
    months: int
    price_usdt: float
    description: str


# Три тарифа, которые отображаются в меню "Подписка"
PLANS: Dict[str, SubscriptionPlan] = {
    "💎 1 месяц": SubscriptionPlan(
        key="💎 1 месяц",
        tier="premium",
        months=1,
        price_usdt=6.99,
        description="BlackBox GPT — Premium на 1 месяц",
    ),
    "💎 3 месяца": SubscriptionPlan(
        key="💎 3 месяца",
        tier="premium",
        months=3,
        price_usdt=20.99,
        description="BlackBox GPT — Premium на 3 месяца",
    ),
    "💎 12 месяцев": SubscriptionPlan(
        key="💎 12 месяцев",
        tier="premium",
        months=12,
        price_usdt=59.99,
        description="BlackBox GPT — Premium на 12 месяцев",
    ),
}


def _detect_plan_by_amount(amount: float) -> Optional[SubscriptionPlan]:
    """
    Подбор плана по сумме платежа.
    Небольшой допуск на плавающую точку.
    """
    for plan in PLANS.values():
        if abs(plan.price_usdt - float(amount)) < 0.01:
            return plan
    return None


async def _get_pool(external_pool: Optional[asyncpg.Pool] = None) -> Tuple[Optional[asyncpg.Pool], bool]:
    """
    Вспомогательная функция:
    - если передали pool извне — используем его (is_temp=False);
    - если не передали, но есть DB_DSN — создаем свой pool (is_temp=True).
    """
    if external_pool is not None:
        return external_pool, False

    if not DB_DSN:
        print("[payments_crypto] WARNING: DB_DSN is not set, DB operations will be skipped")
        return None, False

    pool = await asyncpg.create_pool(DB_DSN, min_size=1, max_size=2)
    return pool, True


async def create_invoice_usdt(
    user_id: int,
    amount: float,
    description: str,
    payload: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Низкоуровневая функция:
    - создает инвойс в Crypto Bot;
    - пишет запись в таблицу payments;
    - возвращает (invoice_id, pay_url).
    """
    if not CRYPTO_BOT_TOKEN:
        raise RuntimeError("CRYPTO_BOT_TOKEN is not set")

    invoice = await _crypto_client.create_invoice(
        asset="USDT",
        amount=amount,
        description=description,
        payload=payload,
    )

    # `invoice` — это уже result из Crypto Bot
    invoice_id = str(invoice["invoice_id"])
    pay_url = invoice["pay_url"]
    status = invoice["status"]

    if DB_DSN:
        pool = await asyncpg.create_pool(DB_DSN, min_size=1, max_size=2)
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO payments (user_id, provider, external_id, amount, currency, status)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    user_id,
                    "CryptoBot",
                    invoice_id,
                    amount,
                    "USDT",
                    status,
                )
        finally:
            await pool.close()

    return invoice_id, pay_url


async def get_invoice_status(invoice_id: str) -> Optional[str]:
    """
    Получить текущий статус инвойса по его ID.
    Возвращает строку-статус ('active', 'paid', 'expired', ...) или None.
    """
    if not CRYPTO_BOT_TOKEN:
        raise RuntimeError("CRYPTO_BOT_TOKEN is not set")

    invoices = await _crypto_client.get_invoices(invoice_ids=[invoice_id])
    # Документация Crypto Bot: result -> items: [invoice, ...]
    items = invoices.get("items") if isinstance(invoices, dict) else None
    if not items:
        return None

    return items[0].get("status")


async def create_invoice_for_user(
    *args: Any,
    **kwargs: Any,
) -> Tuple[str, str]:
    """
    Совместимая обертка, чтобы не зависеть от точного порядка аргументов.

    Поддерживаем варианты:
    - create_invoice_for_user(pool, user_id, plan_key)
    - create_invoice_for_user(user_id, plan_key)
    - create_invoice_for_user(user_id=user_id, plan_key=plan_key, pool=pool)

    Параметр `pool` игнорируется для платежей (мы создаем свой pool),
    но оставлен для совместимости с остальным кодом.
    """
    # pool можем игнорировать, он нужен только для совместимости
    pool = kwargs.get("pool")
    user_id = kwargs.get("user_id")
    plan_key = kwargs.get("plan_key")

    # Попробуем распарсить позиционные аргументы
    if user_id is None or plan_key is None:
        if len(args) == 3:
            # (pool, user_id, plan_key)
            pool, user_id, plan_key = args
        elif len(args) == 2:
            # (user_id, plan_key)
            user_id, plan_key = args
        else:
            raise TypeError(
                "create_invoice_for_user expected (pool, user_id, plan_key) "
                "or (user_id, plan_key) or keyword args."
            )

    if plan_key not in PLANS:
        raise ValueError(f"Unknown plan_key: {plan_key}")

    plan = PLANS[plan_key]

    payload = json.dumps(
        {
            "tier": plan.tier,
            "months": plan.months,
            "plan_key": plan.key,
        }
    )

    invoice_id, pay_url = await create_invoice_usdt(
        user_id=int(user_id),
        amount=plan.price_usdt,
        description=plan.description,
        payload=payload,
    )
    return invoice_id, pay_url


async def refresh_user_payments_and_subscriptions(
    *args: Any,
    **kwargs: Any,
) -> Tuple[Optional[str], Optional[datetime]]:
    """
    Проверяет последние платежи пользователя в Crypto Bot,
    обновляет статусы в таблице payments и, при необходимости,
    активирует/деактивирует подписку в таблицах subscriptions и users.

    Возвращает кортеж:
    (current_tier, expires_at)
    - current_tier: уровень подписки ('premium', 'basic', None)
    - expires_at: дата окончания активной подписки или None
    """
    external_pool = kwargs.get("pool")
    user_id = kwargs.get("user_id")

    if user_id is None:
        if len(args) == 2:
            external_pool, user_id = args
        elif len(args) == 1:
            (user_id,) = args
        else:
            raise TypeError(
                "refresh_user_payments_and_subscriptions expected (pool, user_id) "
                "or (user_id,) or keyword args."
            )

    pool, is_temp = await _get_pool(external_pool)
    if pool is None:
        # Нет подключения к БД — просто ничего не делаем.
        return None, None

    now_utc = datetime.now(timezone.utc)

    try:
        async with pool.acquire() as conn:
            # 1. Берём последний платеж CryptoBot для пользователя
            payment_row = await conn.fetchrow(
                """
                SELECT id, external_id, amount, status, created_at
                FROM payments
                WHERE user_id = $1
                  AND provider = 'CryptoBot'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                int(user_id),
            )

            if payment_row:
                invoice_id = payment_row["external_id"]
                current_status = payment_row["status"]

                # Если платёж ещё не оплачен/не завершен — обновим статус из Crypto Bot
                if current_status not in ("paid", "completed"):
                    new_status = await get_invoice_status(invoice_id)
                    if new_status and new_status != current_status:
                        await conn.execute(
                            """
                            UPDATE payments
                            SET status = $1,
                                updated_at = NOW()
                            WHERE id = $2
                            """,
                            new_status,
                            payment_row["id"],
                        )
                        current_status = new_status

                        # Только при успешной оплате — создаём/обновляем подписку
                        if current_status == "paid":
                            plan = _detect_plan_by_amount(float(payment_row["amount"]))
                            if plan:
                                expires_at = now_utc + timedelta(days=30 * plan.months)

                                # Создаём новую подписку
                                await conn.execute(
                                    """
                                    INSERT INTO subscriptions (user_id, tier, status, expires_at)
                                    VALUES ($1, $2, 'active', $3)
                                    """,
                                    int(user_id),
                                    plan.tier,
                                    expires_at,
                                )

                                # Обновляем флаги в users
                                await conn.execute(
                                    """
                                    UPDATE users
                                    SET is_premium = TRUE,
                                        subscription_expires_at = $1,
                                        updated_at = NOW()
                                    WHERE id = $2
                                    """,
                                    expires_at,
                                    int(user_id),
                                )

            # 2. Проверяем, есть ли вообще активная подписка
            sub_row = await conn.fetchrow(
                """
                SELECT id, tier, status, expires_at
                FROM subscriptions
                WHERE user_id = $1
                  AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                int(user_id),
            )

            if not sub_row:
                return None, None

            tier = sub_row["tier"]
            expires_at = sub_row["expires_at"]

            # Если подписка уже истекла — деактивируем
            if expires_at and expires_at < now_utc:
                await conn.execute(
                    """
                    UPDATE subscriptions
                    SET status = 'expired'
                    WHERE id = $1
                    """,
                    sub_row["id"],
                )
                await conn.execute(
                    """
                    UPDATE users
                    SET is_premium = FALSE,
                        subscription_expires_at = NULL,
                        updated_at = NOW()
                    WHERE id = $1
                    """,
                    int(user_id),
                )
                return None, None

            return tier, expires_at
    finally:
        if is_temp and pool is not None:
            await pool.close()


__all__ = [
    "SubscriptionPlan",
    "PLANS",
    "create_invoice_usdt",
    "get_invoice_status",
    "create_invoice_for_user",
    "refresh_user_payments_and_subscriptions",
]
