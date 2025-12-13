from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Контрактный Settings (Pydantic v2):
    - исключаем AttributeError в рантайме (menu/chat/main)
    - сохраняем совместимость с .env/.env.example (алиасы)
    - ничего не вырезаем: только добавляем недостающие поля/методы и дефолты
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Telegram ---
    bot_token: str = Field(alias="BOT_TOKEN")
    bot_username: str = Field(alias="BOT_USERNAME")

    # --- Timezone ---
    timezone: str = Field(default="Europe/Moscow", alias="TIMEZONE")

    # --- Logging ---
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # --- Admins ---
    # ADMIN_USER_IDS поддерживает:
    # - JSON: [1,2,3]
    # - CSV:  1,2,3
    admin_user_ids: list[int] = Field(default_factory=list, alias="ADMIN_USER_IDS")

    @field_validator("admin_user_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, v: Any) -> list[int]:
        if v is None or v == "":
            return []
        if isinstance(v, (list, tuple, set)):
            out: list[int] = []
            for x in v:
                try:
                    out.append(int(x))
                except Exception:
                    continue
            return out
        if isinstance(v, str):
            s = v.strip()
            # JSON list
            if s.startswith("[") and s.endswith("]"):
                try:
                    arr = json.loads(s)
                    if isinstance(arr, list):
                        return [int(x) for x in arr]
                except Exception:
                    pass
            # CSV list
            s = s.strip("[](){} ")
            out: list[int] = []
            for part in s.split(","):
                part = part.strip().strip('"').strip("'")
                if not part:
                    continue
                try:
                    out.append(int(part))
                except Exception:
                    continue
            return out
        try:
            return [int(v)]
        except Exception:
            return []

    def is_admin(self, user_id: int) -> bool:
        try:
            return int(user_id) in set(int(x) for x in (self.admin_user_ids or []))
        except Exception:
            return False

    # --- Storage ---
    data_dir: str = Field(default="data", alias="DATA_DIR")
    db_path: str = Field(default="data/bot.sqlite3", alias="DB_PATH")

    # --- Web server (health/webhook) ---
    web_server_host: str = Field(default="0.0.0.0", alias="WEB_SERVER_HOST")
    web_server_port: int = Field(default=8080, alias="WEB_SERVER_PORT")

    @property
    def web_host(self) -> str:  # compat
        return self.web_server_host

    @property
    def web_port(self) -> int:  # compat
        return self.web_server_port

    # --- Limits ---
    basic_trial_limit: int = Field(default=10, alias="BASIC_TRIAL_LIMIT")
    pro_daily_limit: int = Field(default=120, alias="PRO_DAILY_LIMIT")
    premium_daily_limit: int = Field(default=500, alias="PREMIUM_DAILY_LIMIT")

    # --- Prices (USDT) ---
    # дефолты под твою текущую задачу
    price_1m: float = Field(default=8.0, alias="PRICE_1M")
    price_3m: float = Field(default=20.0, alias="PRICE_3M")
    price_12m: float = Field(default=60.0, alias="PRICE_12M")

    # --- CryptoPay ---
    cryptopay_api_token: str = Field(default="", alias="CRYPTOPAY_API_TOKEN")
    cryptopay_base_url: str = Field(default="https://pay.crypt.bot/api", alias="CRYPTOPAY_BASE_URL")
    cryptopay_webhook_secret: str = Field(default="", alias="CRYPTOPAY_WEBHOOK_SECRET")
    cryptopay_webhook_url: str = Field(default="", alias="CRYPTOPAY_WEBHOOK_URL")

    # --- LLM ---
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")

    perplexity_api_key: str = Field(default="", alias="PERPLEXITY_API_KEY")
    perplexity_base_url: str = Field(default="https://api.perplexity.ai", alias="PERPLEXITY_BASE_URL")
    perplexity_model: str = Field(default="sonar-pro", alias="PERPLEXITY_MODEL")

    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-70b-versatile", alias="GROQ_MODEL")

    # --- Voice (Yandex SpeechKit) ---
    enable_voice: bool = Field(default=False, alias="ENABLE_VOICE")
    speechkit_api_key: str = Field(default="", alias="SPEECHKIT_API_KEY")
    speechkit_folder_id: str = Field(default="", alias="SPEECHKIT_FOLDER_ID")
    speechkit_lang: str = Field(default="ru-RU", alias="SPEECHKIT_LANG")
    speechkit_topic: str = Field(default="general", alias="SPEECHKIT_TOPIC")
    speechkit_timeout_sec: int = Field(default=25, alias="SPEECHKIT_TIMEOUT_SEC")


def ensure_dirs(settings: Settings) -> None:
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
