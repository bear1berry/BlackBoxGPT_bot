from __future__ import annotations

from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Главное: не падать от лишних переменных в .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram
    bot_token: str = Field(validation_alias=AliasChoices("BOT_TOKEN", "bot_token"))
    bot_username: str = Field(validation_alias=AliasChoices("BOT_USERNAME", "bot_username"))

    # DeepSeek (OpenAI-compatible)
    deepseek_api_key: str = Field(default="", validation_alias=AliasChoices("DEEPSEEK_API_KEY", "deepseek_api_key"))
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        validation_alias=AliasChoices("DEEPSEEK_BASE_URL", "deepseek_base_url"),
    )
    deepseek_model: str = Field(default="deepseek-chat", validation_alias=AliasChoices("DEEPSEEK_MODEL", "deepseek_model"))

    # Perplexity (OpenAI-compatible) + поддержка старых имен
    perplexity_api_key: str = Field(default="", validation_alias=AliasChoices("PERPLEXITY_API_KEY", "perplexity_api_key"))
    perplexity_base_url: str = Field(
        default="https://api.perplexity.ai",
        validation_alias=AliasChoices("PERPLEXITY_BASE_URL", "perplexity_base_url", "perplexity_api_base"),
    )
    perplexity_model: str = Field(
        default="sonar-pro",
        validation_alias=AliasChoices("PERPLEXITY_MODEL", "perplexity_model", "perplexity_model_universal"),
    )

    # Старый/лишний ключ — оставляем, чтобы не было ValidationError
    llm_provider: str | None = Field(default=None, validation_alias=AliasChoices("LLM_PROVIDER", "llm_provider"))

    # Crypto Pay (CryptoBot)
    cryptopay_api_token: str = Field(default="", validation_alias=AliasChoices("CRYPTOPAY_API_TOKEN", "cryptopay_api_token"))
    cryptopay_base_url: str = Field(
        default="https://pay.crypt.bot/api",
        validation_alias=AliasChoices("CRYPTOPAY_BASE_URL", "cryptopay_base_url"),
    )
    cryptopay_webhook_secret: str = Field(
        default="change-me",
        validation_alias=AliasChoices("CRYPTOPAY_WEBHOOK_SECRET", "cryptopay_webhook_secret"),
    )

    # Старый/лишний ключ — чтобы не падало
    cryptopay_asset: str | None = Field(default=None, validation_alias=AliasChoices("CRYPTOPAY_ASSET", "cryptopay_asset"))

    # Storage
    data_dir: str = Field(default="./data", validation_alias=AliasChoices("DATA_DIR", "data_dir"))
    db_path: str = Field(default="./data/blackbox.db", validation_alias=AliasChoices("DB_PATH", "db_path"))

    # Web server (webhooks)
    web_server_host: str = Field(default="0.0.0.0", validation_alias=AliasChoices("WEB_SERVER_HOST", "web_server_host"))
    web_server_port: int = Field(default=8080, validation_alias=AliasChoices("WEB_SERVER_PORT", "web_server_port"))

    # Limits / Plans
    basic_trial_limit: int = Field(default=10, validation_alias=AliasChoices("BASIC_TRIAL_LIMIT", "basic_trial_limit"))
    premium_daily_limit: int = Field(default=100, validation_alias=AliasChoices("PREMIUM_DAILY_LIMIT", "premium_daily_limit"))

    # Prices
    price_1m: float = Field(default=6.99, validation_alias=AliasChoices("PRICE_1M", "price_1m"))
    price_3m: float = Field(default=20.99, validation_alias=AliasChoices("PRICE_3M", "price_3m"))
    price_12m: float = Field(default=59.99, validation_alias=AliasChoices("PRICE_12M", "price_12m"))

    # Features
    enable_pro_research: bool = Field(default=True, validation_alias=AliasChoices("ENABLE_PRO_RESEARCH", "enable_pro_research"))
    enable_formatter_pass: bool = Field(default=True, validation_alias=AliasChoices("ENABLE_FORMATTER_PASS", "enable_formatter_pass"))
    enable_auto_summary: bool = Field(default=False, validation_alias=AliasChoices("ENABLE_AUTO_SUMMARY", "enable_auto_summary"))
    max_context_messages: int = Field(default=12, validation_alias=AliasChoices("MAX_CONTEXT_MESSAGES", "max_context_messages"))

    # Scheduler / time
    timezone: str = Field(default="Europe/Moscow", validation_alias=AliasChoices("TIMEZONE", "timezone"))
    checkin_hour: int = Field(default=22, validation_alias=AliasChoices("CHECKIN_HOUR", "checkin_hour"))
    checkin_minute: int = Field(default=0, validation_alias=AliasChoices("CHECKIN_MINUTE", "checkin_minute"))

    # Logging
    log_level: str = Field(default="INFO", validation_alias=AliasChoices("LOG_LEVEL", "log_level"))

    # Optional: LanguageTool server for spellcheck
    language_tool_url: str | None = Field(default=None, validation_alias=AliasChoices("LANGUAGE_TOOL_URL", "language_tool_url"))
