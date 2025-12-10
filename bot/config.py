from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Глобальные настройки бота.
    Все значения читаются из переменных окружения (.env) и валидируются pydantic.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # игнорируем неизвестные ключи в .env
    )

    # --- Telegram / Bot ---
    bot_token: str = Field(alias="BOT_TOKEN")
    admin_ids: list[int] = Field(default_factory=list, alias="ADMIN_IDS")

    # --- LLM providers ---
    llm_provider: Literal["deepseek", "perplexity"] = Field(
        default="deepseek",
        alias="LLM_PROVIDER",
    )

    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_api_base: str = Field(
        default="https://api.deepseek.com",
        alias="DEEPSEEK_API_BASE",
    )
    deepseek_model: str = Field(
        default="deepseek-chat",
        alias="DEEPSEEK_MODEL",
    )

    perplexity_api_key: str | None = Field(default=None, alias="PERPLEXITY_API_KEY")
    perplexity_api_base: str = Field(
        default="https://api.perplexity.ai",
        alias="PERPLEXITY_API_BASE",
    )
    perplexity_model: str = Field(
        default="sonar-reasoning",
        alias="PERPLEXITY_MODEL",
    )

    # --- Yandex Cloud (SpeechKit) ---
    yandex_iam_token: str | None = Field(default=None, alias="YANDEX_IAM_TOKEN")
    yandex_folder_id: str | None = Field(default=None, alias="YANDEX_FOLDER_ID")
    yandex_tts_voice: str = Field(default="filipp", alias="YANDEX_TTS_VOICE")
    yandex_tts_lang: str = Field(default="ru-RU", alias="YANDEX_TTS_LANG")

    # --- Crypto Pay / монетизация ---
    cryptopay_api_token: str | None = Field(default=None, alias="CRYPTOPAY_API_TOKEN")

    price_1m: float = Field(default=7.99, alias="PRICE_1M")
    price_3m: float = Field(default=25.99, alias="PRICE_3M")
    price_12m: float = Field(default=89.99, alias="PRICE_12M")

    # --- DB ---
    postgres_dsn: str = Field(alias="POSTGRES_DSN")

    # --- Misc ---
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    llm_timeout_sec: int = Field(default=120, alias="LLM_TIMEOUT_SEC")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
