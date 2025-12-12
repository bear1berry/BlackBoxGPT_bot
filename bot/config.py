from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    bot_token: str

    deepseek_api_key: str
    deepseek_model: str = "deepseek-chat"

    perplexity_api_key: str
    perplexity_model: str = "sonar-reasoning"

    crypto_bot_token: str | None = None

    db_dsn: str = "postgresql://blackbox_user:SuperStrongPass123@127.0.0.1:5432/blackboxgpt"

    free_daily_limit: int = 10
    premium_daily_limit: int = 100

    @property
    def has_crypto(self) -> bool:
        return bool(self.crypto_bot_token)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        bot_token=os.environ.get("BOT_TOKEN", ""),
        deepseek_api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
        deepseek_model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        perplexity_api_key=os.environ.get("PERPLEXITY_API_KEY", ""),
        perplexity_model=os.environ.get("PERPLEXITY_MODEL", "sonar-reasoning"),
        crypto_bot_token=os.environ.get("CRYPTO_BOT_TOKEN"),
        db_dsn=os.environ.get(
            "DB_DSN",
            "postgresql://blackbox_user:SuperStrongPass123@127.0.0.1:5432/blackboxgpt",
        ),
        free_daily_limit=int(os.environ.get("FREE_DAILY_LIMIT", "10")),
        premium_daily_limit=int(os.environ.get("PREMIUM_DAILY_LIMIT", "100")),
    )
