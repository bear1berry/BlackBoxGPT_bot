from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # даже если в .env есть лишние ключи — не падаем
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram
    bot_token: str = Field(alias="BOT_TOKEN")
    bot_username: str = Field(alias="BOT_USERNAME")

    # Admins (через .env: ADMIN_USER_IDS=123,456)
    admin_user_ids: list[int] = Field(default_factory=list, alias="ADMIN_USER_IDS")

    @field_validator("admin_user_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, v: Any) -> list[int]:
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, (list, tuple, set)):
            return [int(x) for x in v]
        return []

    def is_admin(self, user_id: int) -> bool:
        return user_id in set(self.admin_user_ids)

    # --- Legacy keys (из старого .env) ---
    llm_provider: str | None = None
    perplexity_api_base: str | None = None
    perplexity_model_universal: str | None = None
    cryptopay_asset: str | None = None

    # DeepSeek (OpenAI-compatible)
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")

    # Perplexity (OpenAI-compatible)
    perplexity_api_key: str = Field(default="", alias="PERPLEXITY_API_KEY")
    perplexity_base_url: str = Field(default="https://api.perplexity.ai", alias="PERPLEXITY_BASE_URL")
    perplexity_model: str = Field(default="sonar-pro", alias="PERPLEXITY_MODEL")

    # Crypto Pay (CryptoBot)
    cryptopay_api_token: str = Field(default="", alias="CRYPTOPAY_API_TOKEN")
    cryptopay_base_url: str = Field(default="https://pay.crypt.bot/api", alias="CRYPTOPAY_BASE_URL")
    cryptopay_webhook_secret: str = Field(default="change-me", alias="CRYPTOPAY_WEBHOOK_SECRET")

    # Storage
    data_dir: str = Field(default="./data", alias="DATA_DIR")
    db_path: str = Field(default="./data/blackbox.db", alias="DB_PATH")

    # Web server (webhooks)
    web_server_host: str = Field(default="0.0.0.0", alias="WEB_SERVER_HOST")
    web_server_port: int = Field(default=8080, alias="WEB_SERVER_PORT")

    # Limits / Plans
    basic_trial_limit: int = Field(default=10, alias="BASIC_TRIAL_LIMIT")
    premium_daily_limit: int = Field(default=100, alias="PREMIUM_DAILY_LIMIT")

    # Prices
    price_1m: float = Field(default=6.99, alias="PRICE_1M")
    price_3m: float = Field(default=20.99, alias="PRICE_3M")
    price_12m: float = Field(default=59.99, alias="PRICE_12M")
