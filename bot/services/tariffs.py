from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from bot.config import Settings

settings = Settings()


@dataclass(frozen=True)
class TariffPlan:
    code: str
    title: str
    daily_requests_limit: int


TARIFFS: Dict[str, TariffPlan] = {
    "free": TariffPlan(
        code="free",
        title="Free",
        daily_requests_limit=settings.free_daily_requests,
    ),
    "pro": TariffPlan(
        code="pro",
        title="Pro",
        daily_requests_limit=settings.pro_daily_requests,
    ),
    "vip": TariffPlan(
        code="vip",
        title="VIP",
        daily_requests_limit=settings.vip_daily_requests,
    ),
}


def resolve_user_plan(plan_code: str | None) -> TariffPlan:
    if plan_code is None:
        return TARIFFS["free"]
    return TARIFFS.get(plan_code, TARIFFS["free"])
