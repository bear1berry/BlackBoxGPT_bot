# bot/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str = Field(..., description="Telegram bot token")

    DATABASE_URL: str = Field(..., description="PostgreSQL async URL (postgresql+asyncpg://...)")

    PERPLEXITY_API_KEY: str
    PERPLEXITY_BASE_URL: str = "https://api.perplexity.ai"

    CRYPTO_PAY_API_TOKEN: str | None = None
    CRYPTO_PAY_CURRENCY: str = "USDT"

    REF_BONUS_DAYS: int = 7

    YANDEX_IAM_TOKEN: str | None = None
    YANDEX_FOLDER_ID: str | None = None
    YANDEX_TTS_VOICE: str = "filipp"
    YANDEX_TTS_LANG: str = "ru-RU"


settings = Settings()
