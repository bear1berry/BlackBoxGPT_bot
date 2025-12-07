from __future__ import annotations

from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.

    Env vars (examples):
        BOT_TOKEN=123:ABC
        BOT_USERNAME=BlackBoxGPT_bot
        DEEPSEEK_API_KEY=...
        DEEPSEEK_MODEL=deepseek-chat
        DEEPSEEK_BASE_URL=https://api.deepseek.com
        DB_URL=sqlite+aiosqlite:///./aimedbot.db
        ADMIN_IDS=123,456
        LOG_LEVEL=INFO
    """

    bot_token: str
    bot_username: str

    deepseek_api_key: str
    deepseek_model: str = "deepseek-chat"
    deepseek_base_url: AnyHttpUrl = "https://api.deepseek.com"

    db_url: str | None = None

    admin_ids: List[int] = []
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )

    @field_validator("admin_ids", mode="before")
    @classmethod
    def split_admin_ids(cls, v: object) -> list[int]:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            parts = [p for p in v.replace(" ", "").split(",") if p]
            return [int(p) for p in parts]
        return v or []

    @field_validator("db_url", mode="before")
    @classmethod
    def default_db_url(cls, v: object) -> str:
        if v is None or (isinstance(v, str) and not v.strip()):
            return "sqlite+aiosqlite:///./aimedbot.db"
        return str(v)


settings = Settings()
