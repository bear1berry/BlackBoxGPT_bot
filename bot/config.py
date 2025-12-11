from __future__ import annotations

from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    bot_token: str

    deepseek_api_key: str
    deepseek_model: str = "deepseek-chat"

    perplexity_api_key: Optional[str] = None
    perplexity_model: str = "llama-3.1-sonar-small-128k-online"

    db_dsn: str

    crypto_pay_token: Optional[str] = None
    crypto_currency: str = "USDT"

    admin_ids: List[int] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("admin_ids", mode="before")
    @classmethod
    def split_admin_ids(cls, v):
        if not v:
            return []
        if isinstance(v, list):
            return [int(x) for x in v]
        return [int(x) for x in str(v).replace(" ", "").split(",") if x]

settings = Settings()
