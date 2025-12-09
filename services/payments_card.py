from __future__ import annotations

from typing import Optional


class CardPaymentsService:
    """
    Заготовка под оплату картой (YooKassa/Stripe/etc.).
    Интерфейс оставлен простым, чтобы позже подключить конкретный провайдер.
    """

    async def create_payment_link(
        self,
        user_id: int,
        plan: str,
        amount: str,
        currency: str = "RUB",
    ) -> Optional[str]:
        """
        Вернуть ссылку на оплату банковской картой.
        Сейчас — заглушка-описание, чтобы было понятно, куда внедрять реальную интеграцию.
        """
        # Здесь позже можно добавить интеграцию с YooKassa/Stripe
        return None
