from __future__ import annotations
import logging
import httpx
from .config import CRYPTO_PAY_API_URL, CRYPTO_PAY_API_TOKEN, SUBSCRIPTION_TARIFFS

log = logging.getLogger(__name__)

async def create_cryptobot_invoice(tariff_key: str):
    if not CRYPTO_PAY_API_TOKEN: raise ValueError("No Token")
    
    # Mapping fix
    key_map = {"1m": "month_1", "3m": "month_3", "12m": "month_12"}
    norm_key = key_map.get(tariff_key, tariff_key)
    tariff = SUBSCRIPTION_TARIFFS.get(norm_key)
    
    if not tariff: raise ValueError("Invalid tariff")
    
    async with httpx.AsyncClient(base_url=CRYPTO_PAY_API_URL, headers={"Crypto-Pay-API-Token": CRYPTO_PAY_API_TOKEN}) as client:
        resp = await client.post("createInvoice", json={
            "asset": "USDT", "amount": tariff["price_usdt"], "description": tariff["title"], "payload": f"sub:{norm_key}"
        })
        return resp.json().get("result")

async def is_invoice_paid(invoice_id: int) -> bool:
    if not CRYPTO_PAY_API_TOKEN: return False
    async with httpx.AsyncClient(base_url=CRYPTO_PAY_API_URL, headers={"Crypto-Pay-API-Token": CRYPTO_PAY_API_TOKEN}) as client:
        resp = await client.get("getInvoices", params={"invoice_ids": str(invoice_id)})
        items = resp.json().get("result", {}).get("items", [])
        if items and items[0]["status"] == "paid":
            return True
    return False
