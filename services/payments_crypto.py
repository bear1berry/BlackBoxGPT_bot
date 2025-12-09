from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from bot.config import get_settings
from storage.repositories import PaymentsRepository
from storage.models import PaymentProviderEnum, PaymentStatusEnum

logger = logging.getLogger(__name__)

settings = get_settings()


class CryptoPaymentsService:
    """
    Интеграция с CryptoBot (https://t.me/CryptoBot).
    API может эволюционировать, эндпоинты и параметры вынесены в конфиг.
    """

    def __init__(self) -> None:
        if not settings.cryptobot_api_token:
            logger.warning("CryptoBot API token is not configured")
        self._repo = PaymentsRepository()

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.cryptobot_api_token}",
        }

    async def create_invoice(
        self,
        user_id: int,
        plan: str,
        amount: str,
        currency: str = "USDT",
    ) -> Optional[str]:
        """
        Создаёт инвойс в CryptoBot и сохраняет данные в БД.
        Возвращает ссылку на оплату или None.
        """
        if not settings.cryptobot_api_token:
            logger.error("CryptoBot token is missing")
            return None

        payload: Dict[str, Any] = {
            "asset": currency,
            "amount": amount,
            "description": f"BlackBox GPT Premium — план {plan}",
        }

        async with httpx.AsyncClient(
            base_url=str(settings.cryptobot_api_base),
            timeout=30.0,
        ) as client:
            resp = await client.post("/api/createInvoice", json=payload, headers=self._headers)
            if resp.status_code != 200:
                logger.error("CryptoBot createInvoice failed: %s", resp.text)
                return None
            data = resp.json()
            result = data.get("result") or {}
            invoice_id = str(result.get("invoice_id"))
            pay_url = result.get("pay_url")
            if not invoice_id or not pay_url:
                logger.error("CryptoBot createInvoice invalid response: %s", data)
                return None

        await self._repo.create_payment(
            user_id=user_id,
            provider=PaymentProviderEnum.CRYPTO,
            plan=plan,
            amount=amount,
            currency=currency,
            invoice_id=invoice_id,
        )

        return pay_url

    async def check_and_update_status(self, payment) -> None:
        """
        Проверка статуса конкретного платежа.
        """
        if not settings.cryptobot_api_token:
            return

        async with httpx.AsyncClient(
            base_url=str(settings.cryptobot_api_base),
            timeout=30.0,
        ) as client:
            resp = await client.get(
                "/api/getInvoices",
                params={"invoice_ids": payment.invoice_id},
                headers=self._headers,
            )
            if resp.status_code != 200:
                logger.error("CryptoBot getInvoices failed: %s", resp.text)
                return
            data = resp.json()
            result = (data.get("result") or {}).get("items") or []
            if not result:
                return
            status = result[0].get("status")
            if status == "paid":
                await self._repo.update_status(
                    payment.invoice_id,
                    PaymentStatusEnum.PAID,
                )
            elif status in {"expired", "canceled"}:
                await self._repo.update_status(
                    payment.invoice_id,
                    PaymentStatusEnum.CANCELED,
                )
