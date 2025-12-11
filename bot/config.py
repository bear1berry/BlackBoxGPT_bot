from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List


@dataclass
class Settings:
    bot_token: str
    bot_username: str

    db_dsn: str

    deepseek_api_key: str
    deepseek_model: str

    perplexity_api_key: str
    perplexity_model: str

    cryptopay_api_token: str | None

    free_daily_limit: int
    premium_daily_limit: int

    admin_ids: List[int]


def _parse_admin_ids(raw: str | None) -> List[int]:
    if not raw:
        return []
    result: List[int] = []
    for part in raw.replace(" ", "").split(","):
        if not part:
            continue
        try:
            result.append(int(part))
        except ValueError:
            continue
    return result


def load_settings() -> Settings:
    return Settings(
        bot_token=os.getenv("BOT_TOKEN", "").strip(),
        bot_username=os.getenv("BOT_USERNAME", "BlackBoxAssistant_bot").strip(),
        db_dsn=os.getenv(
            "DB_DSN",
            "postgresql://blackbox_user:SuperStrongPass123@127.0.0.1:5432/blackboxgpt",
        ),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "").strip(),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip(),
        perplexity_api_key=os.getenv("PERPLEXITY_API_KEY", "").strip(),
        perplexity_model=os.getenv("PERPLEXITY_MODEL", "sonar-pro").strip(),
        cryptopay_api_token=os.getenv("CRYPTOPAY_API_TOKEN", "").strip() or None,
        free_daily_limit=int(os.getenv("FREE_DAILY_LIMIT", "10")),
        premium_daily_limit=int(os.getenv("PREMIUM_DAILY_LIMIT", "100")),
        admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS")),
    )


settings = load_settings()
