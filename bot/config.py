from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_int_list(value: Any) -> List[int]:
    """Accepts list[int] / json string / comma-separated string."""
    if value is None:
        return []
    if isinstance(value, list):
        out: List[int] = []
        for x in value:
            try:
                out.append(int(x))
            except Exception:
                continue
        return out
    if isinstance(value, (int, float)):
        return [int(value)]
    s = str(value).strip()
    if not s:
        return []

    # JSON array
    if s.startswith("["):
        try:
            arr = json.loads(s)
            return _parse_int_list(arr)
        except Exception:
            return []

    # comma-separated
    parts = [p.strip() for p in s.split(",") if p.strip()]
    out: List[int] = []
    for p in parts:
        try:
            out.append(int(p))
        except Exception:
            continue
    return out


class Settings(BaseSettings):
    """Single source of truth for configuration.

    Important: keep this class in sync with code that uses Settings.
    Routers/services are allowed to call:
      - settings.is_admin(user_id)
      - settings.admin_user_ids (property)
      - settings.price_1m/price_3m/price_12m
      - settings.checkin_hour/checkin_minute, fact_hour/fact_minute
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Telegram ---
    bot_token: str = Field(..., alias="BOT_TOKEN")
    bot_username: str = Field("BlackBoxAssistant_bot", alias="BOT_USERNAME")

    # --- Runtime / logs ---
    timezone: str = Field("Europe/Moscow", alias="TIMEZONE")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    # --- Storage ---
    data_dir: str = Field("data", alias="DATA_DIR")
    db_path: str = Field("data/bot.db", alias="DB_PATH")

    # --- Admins ---
    _admin_user_ids_raw: Any = Field("[]", alias="ADMIN_USER_IDS")

    @property
    def admin_user_ids(self) -> List[int]:
        return _parse_int_list(self._admin_user_ids_raw)

    def is_admin(self, user_id: int) -> bool:
        try:
            return int(user_id) in self.admin_user_ids
        except Exception:
            return False

    # --- Web server (health + CryptoPay webhook) ---
    web_server_host: str = Field("0.0.0.0", alias="WEB_SERVER_HOST")
    web_server_port: int = Field(8080, alias="WEB_SERVER_PORT")

    # --- Schedulers ---
    checkin_hour: int = Field(22, alias="CHECKIN_HOUR")
    checkin_minute: int = Field(0, alias="CHECKIN_MINUTE")
    fact_hour: int = Field(10, alias="FACT_HOUR")
    fact_minute: int = Field(0, alias="FACT_MINUTE")

    # --- LLM keys / models ---
    deepseek_api_key: str | None = Field(None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field("https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")
    deepseek_model: str = Field("deepseek-chat", alias="DEEPSEEK_MODEL")

    groq_api_key: str | None = Field(None, alias="GROQ_API_KEY")
    groq_base_url: str = Field("https://api.groq.com/openai/v1", alias="GROQ_BASE_URL")
    groq_model: str = Field("llama-3.3-70b-versatile", alias="GROQ_MODEL")

    perplexity_api_key: str | None = Field(None, alias="PERPLEXITY_API_KEY")
    perplexity_base_url: str = Field("https://api.perplexity.ai", alias="PERPLEXITY_BASE_URL")
    perplexity_model: str = Field("sonar-pro", alias="PERPLEXITY_MODEL")

    # --- CryptoPay ---
    cryptopay_api_token: str | None = Field(None, alias="CRYPTOPAY_API_TOKEN")
    cryptopay_base_url: str = Field("https://pay.crypt.bot/api", alias="CRYPTOPAY_BASE_URL")
    cryptopay_webhook_secret: str | None = Field(None, alias="CRYPTOPAY_WEBHOOK_SECRET")
    cryptopay_webhook_url: str | None = Field(None, alias="CRYPTOPAY_WEBHOOK_URL")

    # --- Limits / plans ---
    basic_trial_limit: int = Field(10, alias="BASIC_TRIAL_LIMIT")
    premium_daily_limit: int = Field(100, alias="PREMIUM_DAILY_LIMIT")

    # Backward/forward compatibility (some older code used PRO_*)
    pro_daily_limit: int = Field(100, alias="PRO_DAILY_LIMIT")

    # --- Prices (USDT) ---
    price_1m: float = Field(8.0, alias="PRICE_1M")
    price_3m: float = Field(20.0, alias="PRICE_3M")
    price_12m: float = Field(60.0, alias="PRICE_12M")

    # --- Voice (Yandex SpeechKit) ---
    enable_voice: bool = Field(False, alias="ENABLE_VOICE")
    speechkit_api_key: str | None = Field(None, alias="SPEECHKIT_API_KEY")
    speechkit_folder_id: str | None = Field(None, alias="SPEECHKIT_FOLDER_ID")
    speechkit_lang: str = Field("ru-RU", alias="SPEECHKIT_LANG")
    speechkit_topic: str = Field("general", alias="SPEECHKIT_TOPIC")
    speechkit_timeout_sec: int = Field(25, alias="SPEECHKIT_TIMEOUT_SEC")

    # --- Referral salt ---
    # Used to generate stable referral codes. If unset, falls back to BOT_TOKEN prefix.
    ref_salt: str | None = Field(None, alias="REF_SALT")

    @property
    def ref_salt_effective(self) -> str:
        return (self.ref_salt or self.bot_token[:16]).strip()

    # Convenience
    @property
    def data_dir_path(self) -> Path:
        return Path(self.data_dir)

    @property
    def db_path_path(self) -> Path:
        return Path(self.db_path)
