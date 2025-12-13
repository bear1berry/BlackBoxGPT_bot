from __future__ import annotations

import json
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Telegram / core
    bot_token: str = Field(..., alias="BOT_TOKEN")
    admin_user_ids: List[int] = Field(default_factory=list, alias="ADMIN_USER_IDS")
    timezone: str = Field("Europe/Moscow", alias="TIMEZONE")

    # LLM routing (OpenAI-compatible)
    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field("https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_model: str = Field("gpt-4o-mini", alias="OPENAI_MODEL")

    # DeepSeek
    deepseek_api_key: Optional[str] = Field(None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field("https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field("deepseek-chat", alias="DEEPSEEK_MODEL")
    deepseek_temperature: float = Field(0.6, alias="DEEPSEEK_TEMPERATURE")

    # Perplexity
    perplexity_api_key: Optional[str] = Field(None, alias="PERPLEXITY_API_KEY")
    perplexity_base_url: str = Field("https://api.perplexity.ai", alias="PERPLEXITY_BASE_URL")
    perplexity_model: str = Field("sonar-pro", alias="PERPLEXITY_MODEL")
    perplexity_temperature: float = Field(0.4, alias="PERPLEXITY_TEMPERATURE")

    # Groq
    groq_api_key: Optional[str] = Field(None, alias="GROQ_API_KEY")
    groq_base_url: str = Field("https://api.groq.com/openai/v1", alias="GROQ_BASE_URL")
    groq_model: str = Field("llama-3.1-70b-versatile", alias="GROQ_MODEL")
    groq_temperature: float = Field(0.4, alias="GROQ_TEMPERATURE")

    # Post-processing
    enable_formatter_pass: bool = Field(True, alias="ENABLE_FORMATTER_PASS")

    # Storage
    data_dir: str = Field("data", alias="DATA_DIR")
    db_path: str = Field("data/bot.sqlite3", alias="DB_PATH")

    # Web server
    web_server_host: str = Field("0.0.0.0", alias="WEB_SERVER_HOST")
    web_server_port: int = Field(8080, alias="WEB_SERVER_PORT")

    # Daily check-ins
    checkin_hour: int = Field(22, alias="CHECKIN_HOUR")
    checkin_minute: int = Field(0, alias="CHECKIN_MINUTE")

    # CryptoPay
    cryptopay_api_token: Optional[str] = Field(None, alias="CRYPTOPAY_API_TOKEN")
    cryptopay_api_base: str = Field("https://pay.crypt.bot/api", alias="CRYPTOPAY_API_BASE")
    cryptopay_webhook_secret: Optional[str] = Field(None, alias="CRYPTOPAY_WEBHOOK_SECRET")

    # Limits / pricing
    basic_trial_limit: int = Field(30, alias="BASIC_TRIAL_LIMIT")
    premium_daily_limit: int = Field(300, alias="PREMIUM_DAILY_LIMIT")
    price_1m: int = Field(990, alias="PRICE_1M")
    price_3m: int = Field(2490, alias="PRICE_3M")
    price_12m: int = Field(7990, alias="PRICE_12M")

    # Voice (SpeechKit)
    enable_voice: bool = Field(False, alias="ENABLE_VOICE")
    speechkit_api_key: Optional[str] = Field(None, alias="SPEECHKIT_API_KEY")
    speechkit_folder_id: Optional[str] = Field(None, alias="SPEECHKIT_FOLDER_ID")
    speechkit_lang: str = Field("ru-RU", alias="SPEECHKIT_LANG")
    speechkit_topic: str = Field("general", alias="SPEECHKIT_TOPIC")
    speechkit_timeout_sec: int = Field(20, alias="SPEECHKIT_TIMEOUT_SEC")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("admin_user_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return [int(x) for x in v]
        if isinstance(v, str):
            # supports: "1,2,3" or json "[1,2,3]"
            s = v.strip()
            if s.startswith("["):
                try:
                    return [int(x) for x in json.loads(s)]
                except Exception:
                    pass
            return [int(x.strip()) for x in s.split(",") if x.strip()]
        return []

