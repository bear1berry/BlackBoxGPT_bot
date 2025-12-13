from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class Limits:
    """
    Unified limits model for the bot.

    - trial_total: total messages allowed in trial (lifetime)
    - premium_daily: daily messages allowed for premium users
    """
    trial_total: int
    premium_daily: int


def utc_day_key(ts: Optional[int] = None) -> str:
    """
    Returns YYYY-MM-DD (UTC) key for daily counters.
    """
    dt = datetime.fromtimestamp(ts or datetime.now(tz=timezone.utc).timestamp(), tz=timezone.utc)
    return dt.strftime("%Y-%m-%d")


def get_user_daily_bucket(user: dict, *, now_ts: Optional[int] = None) -> dict:
    """
    Ensures user has daily usage bucket for current UTC day.
    """
    key = utc_day_key(now_ts)
    daily = user.setdefault("daily_usage", {})
    bucket = daily.setdefault(key, {"count": 0})
    # Optional cleanup: keep only last 14 days
    if len(daily) > 20:
        keys = sorted(daily.keys())
        for k in keys[:-14]:
            daily.pop(k, None)
    return bucket


def is_premium(user: dict, *, now_ts: Optional[int] = None) -> bool:
    """
    Premium if premium_until_ts exists and is in the future.
    """
    now = int(now_ts or datetime.now(tz=timezone.utc).timestamp())
    until = int(user.get("premium_until_ts") or 0)
    return until > now


def remaining_trial(user: dict, limits: Limits) -> int:
    used = int(user.get("trial_used") or 0)
    return max(0, limits.trial_total - used)


def remaining_premium_today(user: dict, limits: Limits, *, now_ts: Optional[int] = None) -> int:
    bucket = get_user_daily_bucket(user, now_ts=now_ts)
    used = int(bucket.get("count") or 0)
    return max(0, limits.premium_daily - used)


def check_and_consume(user: dict, limits: Limits, *, now_ts: Optional[int] = None) -> tuple[bool, str]:
    """
    Returns (ok, reason). If ok=True, increments counters.
    """
    if is_premium(user, now_ts=now_ts):
        left = remaining_premium_today(user, limits, now_ts=now_ts)
        if left <= 0:
            return False, "premium_daily_exhausted"
        bucket = get_user_daily_bucket(user, now_ts=now_ts)
        bucket["count"] = int(bucket.get("count") or 0) + 1
        return True, "ok"

    left = remaining_trial(user, limits)
    if left <= 0:
        return False, "trial_exhausted"
    user["trial_used"] = int(user.get("trial_used") or 0) + 1
    return True, "ok"
