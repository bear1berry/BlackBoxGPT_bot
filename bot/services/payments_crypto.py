from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import httpx

from ..config import settings

API_BASE_URL = "https://pay.crypt.bot/api"


@dataclass
class Invoice:
    invoice_id: int
    status: str
    pay_url: str
    asset: str
    amount: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Invoice":
        return cls(
            invoice_id=data["invoice_id"],
            status=data["status"],
            pay_url=data["pay_url"],
            asset=data["asset"],
            amount=str(data["amount"]),
        )


class CryptoPayClient:
    def __init__(self, token: str) -> None:
        self._token = token
        self._client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=15.0)

    async def _request(self, method: str, payload: Dict[str, Any]) -> Any:
        resp = await self._client.post(
            method,
            json=payload,
            headers={"Crypto-Pay-API-Token": self._token},
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Crypto Pay API error: {data}")
        return data["result"]

    async def create_invoice(
        self,
        *,
        amount: str,
        asset: str = "USDT",
        description: str | None = None,
        payload: str | None = None,
    ) -> Invoice:
        body: Dict[str, Any] = {"asset": asset, "amount": amount}
        if description:
            body["description"] = description
        if payload:
            body["payload"] = payload

        result = await self._request("createInvoice", body)
        return Invoice.from_dict(result)

    async def get_invoices(self, invoice_ids: List[int]) -> List[Invoice]:
        if not invoice_ids:
            return []
        result = await self._request("getInvoices", {"invoice_ids": invoice_ids})
        return [Invoice.from_dict(item) for item in result]


crypto_pay = CryptoPayClient(settings.cryptopay_token)
