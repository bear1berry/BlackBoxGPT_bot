from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any, Optional

import httpx


class CryptoPayError(RuntimeError):
    pass


@dataclass
class Invoice:
    invoice_id: int
    status: str
    amount: str
    asset: str
    bot_invoice_url: str | None
    payload: str | None
    raw: dict[str, Any]


def _secret_from_token(token: str) -> bytes:
    return hashlib.sha256(token.encode("utf-8")).digest()


def verify_signature(api_token: str, raw_body: bytes, signature_hex: str | None) -> bool:
    if not signature_hex:
        return False
    secret = _secret_from_token(api_token)
    calc = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(calc, signature_hex)


class CryptoPayClient:
    def __init__(self, *, api_token: str, base_url: str):
        self.api_token = api_token
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Crypto-Pay-API-Token": api_token},
            timeout=20.0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        resp = await self._client.post(f"/{method}", json=params or {})
        data = resp.json()
        if not data.get("ok", False):
            raise CryptoPayError(data.get("error") or "CryptoPay API error")
        return data["result"]

    async def create_invoice(
        self,
        *,
        amount: str,
        asset: str = "USDT",
        description: str,
        payload: str,
        expires_in: int = 3600,
        allow_comments: bool = False,
        allow_anonymous: bool = True,
    ) -> Invoice:
        result = await self._request(
            "createInvoice",
            {
                "asset": asset,
                "amount": amount,
                "description": description,
                "payload": payload,
                "expires_in": expires_in,
                "allow_comments": allow_comments,
                "allow_anonymous": allow_anonymous,
            },
        )
        return Invoice(
            invoice_id=int(result["invoice_id"]),
            status=result["status"],
            amount=result["amount"],
            asset=result.get("asset") or asset,
            bot_invoice_url=result.get("bot_invoice_url") or result.get("pay_url"),
            payload=result.get("payload"),
            raw=result,
        )

    async def get_invoices(self, invoice_ids: list[int] | None = None, status: str | None = None) -> list[Invoice]:
        params: dict[str, Any] = {}
        if invoice_ids:
            params["invoice_ids"] = ",".join(str(i) for i in invoice_ids)
        if status:
            params["status"] = status

        result = await self._request("getInvoices", params)
        items = result.get("items", [])
        out: list[Invoice] = []
        for it in items:
            out.append(
                Invoice(
                    invoice_id=int(it["invoice_id"]),
                    status=it["status"],
                    amount=it["amount"],
                    asset=it.get("asset") or "USDT",
                    bot_invoice_url=it.get("bot_invoice_url") or it.get("pay_url"),
                    payload=it.get("payload"),
                    raw=it,
                )
            )
        return out
