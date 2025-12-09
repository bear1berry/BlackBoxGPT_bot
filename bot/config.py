from __future__ import annotations

from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Все настройки бота, читаются из .env и переменных окружения.
    Любые лишние ключи в .env игнорируются (extra='ignore'),
    чтобы не было ошибок вида 'Extra inputs are not permitted'.
    """

    # Базовое
    bot_token: str = Field(..., validation_alias="BOT_TOKEN")
    bot_username: str = Field(..., validation_alias="BOT_USERNAME")

    postgres_dsn: str = Field(..., validation_alias="POSTGRES_DSN")

    # LLM ключи
    perplexity_api_key: str = Field(..., validation_alias="PERPLEXITY_API_KEY")
    deepseek_api_key: str = Field(..., validation_alias="DEEPSEEK_API_KEY")

    # Базовый endpoint Perplexity (если нужен)
    perplexity_api_base: str = Field(
        default="https://api.perplexity.ai",
        validation_alias="PERPLEXITY_API_BASE",
    )

    # Модели по умолчанию Perplexity (разные по режимам)
    perplexity_model_universal: str = Field(
        default="sonar-reasoning",
        validation_alias="PERPLEXITY_MODEL_UNIVERSAL",
    )
    perplexity_model_medicine: str = Field(
        default="sonar-reasoning",
        validation_alias="PERPLEXITY_MODEL_MEDICINE",
    )
    perplexity_model_mentor: str = Field(
        default="sonar-reasoning",
        validation_alias="PERPLEXITY_MODEL_MENTOR",
    )
    perplexity_model_business: str = Field(
        default="sonar-reasoning",
        validation_alias="PERPLEXITY_MODEL_BUSINESS",
    )
    perplexity_model_creative: str = Field(
        default="sonar-reasoning",
        validation_alias="PERPLEXITY_MODEL_CREATIVE",
    )

    # DeepSeek (по режимам)
    deepseek_model_universal: str = Field(
        default="deepseek-chat",
        validation_alias="DEEPSEEK_MODEL_UNIVERSAL",
    )
    deepseek_model_medicine: str = Field(
        default="deepseek-chat",
        validation_alias="DEEPSEEK_MODEL_MEDICINE",
    )
    deepseek_model_mentor: str = Field(
        default="deepseek-chat",
        validation_alias="DEEPSEEK_MODEL_MENTOR",
    )
    deepseek_model_business: str = Field(
        default="deepseek-chat",
        validation_alias="DEEPSEEK_MODEL_BUSINESS",
    )
    deepseek_model_creative: str = Field(
        default="deepseek-chat",
        validation_alias="DEEPSEEK_MODEL_CREATIVE",
    )

    # Настройки Crypto Bot (оплата подписки)
    crypto_bot_token: str = Field(..., validation_alias="CRYPTO_BOT_TOKEN")
    price_1m: float = Field(7.99, validation_alias="PRICE_1M")
    price_3m: float = Field(25.99, validation_alias="PRICE_3M")
    price_12m: float = Field(89.99, validation_alias="PRICE_12M")

    # Yandex SpeechKit (аудио)
    yandex_iam_token: Optional[str] = Field(
        default=None,
        validation_alias="YANDEX_IAM_TOKEN",
    )
    yandex_folder_id: Optional[str] = Field(
        default=None,
        validation_alias="YANDEX_FOLDER_ID",
    )
    yandex_tts_voice: str = Field(
        default="filipp",
        validation_alias="YANDEX_TTS_VOICE",
    )
    yandex_tts_lang: str = Field(
        default="ru-RU",
        validation_alias="YANDEX_TTS_LANG",
    )

    # Логирование и таймауты
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
    )
    llm_timeout_sec: int = Field(
        default=120,
        validation_alias="LLM_TIMEOUT_SEC",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
