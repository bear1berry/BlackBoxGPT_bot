from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Global application settings loaded from .env file.
    """

    # Telegram
    bot_token: str = Field(..., description="Telegram bot token")

    # Database (optional, not used in current version but reserved)
    database_url: str | None = Field(
        default=None,
        description="Async database URL (e.g. postgres+asyncpg://user:pass@host/dbname)",
    )

    # LLM providers
    deepseek_api_key: str | None = None
    deepseek_api_base: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    perplexity_api_key: str | None = None
    perplexity_api_base: str = "https://api.perplexity.ai"
    perplexity_model: str = "sonar"

    # Which provider to use by default: 'deepseek' or 'perplexity'
    default_llm_provider: str = "deepseek"

    # Timeouts & logging
    llm_timeout_sec: int = 120
    log_level: str = "INFO"

    # Yandex Cloud (TTS/STT)
    yandex_iam_token: str | None = None
    yandex_folder_id: str | None = None
    yandex_tts_voice: str = "filipp"
    yandex_tts_lang: str = "ru-RU"
    yandex_stt_model: str = "general"

    # Subscription prices (USD-equivalent)
    price_1m: float = 7.99
    price_3m: float = 25.99
    price_12m: float = 89.99

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )


settings = Settings()
