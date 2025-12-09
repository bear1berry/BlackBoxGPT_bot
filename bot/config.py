from __future__ import annotations

from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    BOT_TOKEN: str
    BOT_USERNAME: str
    DEEPSEEK_API_KEY: str

    # Comma-separated list of Telegram user IDs who can use admin commands
    ADMIN_IDS: str = Field(default="")

    # Default: SQLite DB in ./data directory
    DB_URL: str = Field(default="sqlite+aiosqlite:///./data/bot.db")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def _normalize_admin_ids(cls, v: str) -> str:
        return v or ""

    @property
    def admin_ids_list(self) -> List[int]:
        if not self.ADMIN_IDS:
            return []
        result: List[int] = []
        for part in self.ADMIN_IDS.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                result.append(int(part))
            except ValueError:
                continue
        return result

    @property
    def bot_link(self) -> str:
        # Username is stored without "@"
        return f"https://t.me/{self.BOT_USERNAME}"
