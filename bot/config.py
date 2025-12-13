# bot/config.py
from __future__ import annotations

import json
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # даже если в .env есть лишние ключи — не падаем
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # важно: не пытаемся JSON-декодить complex-типы из env,
        # иначе ADMIN_USER_IDS=1,2 упадёт до валидатора.
        enable_decoding=False,
        extra="ignore",
    )

    # Telegram
    bot_token: str = Field(alias="BOT_TOKEN")
    bot_username: str = Field(alias="BOT_USERNAME")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Timezone
    timezone: str = Field(default="Europe/Moscow", alias="TIMEZONE")

    # Admins (через .env: ADMIN_USER_IDS=123,456)
    admin_user_ids: list[int] = Field(default_factory=list, alias="ADMIN_USER_IDS")

    @field_validator("admin_user_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, v: Any) -> list[int]:
        if v is None or v == "":
            return []
        if isinstance(v, str):
            s = v.strip()

            # Support JSON-style list: [1,2,3]
            if s.startswith("[") and s.endswith("]"):
                try:
                    arr = json.loads(s)
                    if isinstance(arr, list):
                        return [int(x) for x in arr]
                except Exception:
                    pass

            # Support bracketed strings and comma-separated values
            s = s.strip("[](){} ")
            out: list[int] = []
            for chunk in s.split(","):
                chunk = chunk.strip()
                if not chunk:
                    continue
                # tolerate accidental quotes
                chunk = chunk.strip("\"' ")
                try:
                    out.append(int(chunk))
                except Exception:
                    continue
            return out
        if isinstance(v, (list, tuple, set)):
            return [int(x) for x in v]
        return []

    def is_admin(self, user_id: int) -> bool:
        return user_id in set(self.admin_user_ids)

    # --- Legacy keys (из старого .env) ---
    llm_provider: str | None = None
    perplexity_api_base: str | None = None
    perplexity_model_universal: str | None = None
    cryptopay_asset: str | None = None

    # Feature flags
    enable_pro_research: bool = Field(default=True, alias="ENABLE_PRO_RESEARCH")
    enable_formatter_pass: bool = Field(default=True, alias="ENABLE_FORMATTER_PASS")
    max_context_messages: int = Field(default=18, alias="MAX_CONTEXT_MESSAGES")

    # DeepSeek (OpenAI-compatible)
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")

    # Perplexity (OpenAI-compatible)
    perplexity_api_key: str = Field(default="", alias="PERPLEXITY_API_KEY")
    perplexity_base_url: str = Field(default="https://api.perplexity.ai", alias="PERPLEXITY_BASE_URL")
    perplexity_model: str = Field(default="sonar-pro", alias="PERPLEXITY_MODEL")

    # Crypto Pay (CryptoBot)
    cryptopay_api_token: str = Field(default="", alias="CRYPTOPAY_API_TOKEN")
    cryptopay_base_url: str = Field(default="https://pay.crypt.bot/api", alias="CRYPTOPAY_BASE_URL")
    cryptopay_webhook_secret: str = Field(default="change-me", alias="CRYPTOPAY_WEBHOOK_SECRET")
    cryptopay_webhook_url: str = Field(default="", alias="CRYPTOPAY_WEBHOOK_URL")

    # Storage
    data_dir: str = Field(default="data", alias="DATA_DIR")
    db_path: str = Field(default="data/bot.db", alias="DB_PATH")

    # Web server (webhooks)
    web_server_host: str = Field(default="0.0.0.0", alias="WEB_SERVER_HOST")
    web_server_port: int = Field(default=8080, alias="WEB_SERVER_PORT")

    # Schedulers
    checkin_hour: int = Field(default=22, alias="CHECKIN_HOUR")
    checkin_minute: int = Field(default=0, alias="CHECKIN_MINUTE")
    fact_hour: int = Field(default=10, alias="FACT_HOUR")
    fact_minute: int = Field(default=0, alias="FACT_MINUTE")

    # Limits / Plans
    basic_trial_limit: int = Field(default=10, alias="BASIC_TRIAL_LIMIT")
    premium_daily_limit: int = Field(default=100, alias="PREMIUM_DAILY_LIMIT")

    # Prices
    price_1m: float = Field(default=6.99, alias="PRICE_1M")
    price_3m: float = Field(default=20.99, alias="PRICE_3M")
    price_12m: float = Field(default=59.99, alias="PRICE_12M")

    # Voice (Yandex SpeechKit)
    enable_voice: bool = Field(default=False, alias="ENABLE_VOICE")
    speechkit_api_key: str = Field(default="", alias="SPEECHKIT_API_KEY")
    speechkit_folder_id: str = Field(default="", alias="SPEECHKIT_FOLDER_ID")
    speechkit_lang: str = Field(default="ru-RU", alias="SPEECHKIT_LANG")
    speechkit_topic: str = Field(default="general", alias="SPEECHKIT_TOPIC")
    speechkit_timeout_sec: int = Field(default=25, alias="SPEECHKIT_TIMEOUT_SEC")
