from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация бота, считывается из .env и окружения."""

    # Telegram
    bot_token: str

    # LLM: DeepSeek
    deepseek_api_key: str | None = None
    deepseek_api_base: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # LLM: Perplexity
    perplexity_api_key: str | None = None
    perplexity_api_base: str = "https://api.perplexity.ai"
    perplexity_model: str = "llama-3.1-sonar-small-128k-chat"

    # Какого провайдера использовать по умолчанию (universal-режим)
    default_provider: Literal["deepseek", "perplexity"] = "deepseek"

    # Yandex SpeechKit (TTS/STT)
    yandex_iam_token: str | None = None
    yandex_folder_id: str | None = None
    yandex_tts_voice: str = "filipp"
    yandex_tts_lang: str = "ru-RU"

    # Цены подписки (на будущее, используются в интерфейсе)
    price_1m: float = 7.99
    price_3m: float = 25.99
    price_12m: float = 89.99

    # Логирование и тайм-ауты
    log_level: str = "INFO"
    llm_timeout_sec: int = 120

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
