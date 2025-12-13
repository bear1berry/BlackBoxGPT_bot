from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram
    bot_token: str = Field(alias="BOT_TOKEN")
    bot_username: str = Field(alias="BOT_USERNAME")

    # Admins: строка вида "123,456 789"
    admin_ids: list[int] = Field(default_factory=list, alias="ADMIN_IDS")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, v):
        if v is None:
            return []
        if isinstance(v, (list, tuple, set)):
            return [int(x) for x in v]
        s = str(v).strip()
        if not s:
            return []
        # принимаем "1,2 3;4"
        s = s.replace(";", ",").replace(" ", ",")
        parts = [p.strip() for p in s.split(",") if p.strip()]
        out: list[int] = []
        for p in parts:
            if p.lstrip("-").isdigit():
                out.append(int(p))
        return out

    @property
    def admin_id_set(self) -> set[int]:
        return set(self.admin_ids)

    # --- Legacy keys (из старого .env) ---
    llm_provider: str | None = None
    perplexity_api_base: str | None = None
    perplexity_model_universal: str | None = None
    cryptopay_asset: str | None = None

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

    # Storage
    data_dir: str = Field(default="./data", alias="DATA_DIR")
    db_path: str = Field(default="./data/blackbox.db", alias="DB_PATH")

    # Web server (webhooks)
    web_server_host: str = Field(default="0.0.0.0", alias="WEB_SERVER_HOST")
    web_server_port: int = Field(default=8080, alias="WEB_SERVER_PORT")

    # Limits / Plans
    basic_trial_limit: int = Field(default=10, alias="BASIC_TRIAL_LIMIT")
    premium_daily_limit: int = Field(default=100, alias="PREMIUM_DAILY_LIMIT")

    # Prices
    price_1m: float = Field(default=6.99, alias="PRICE_1M")
    price_3m: float = Field(default=20.99, alias="PRICE_3M")
    price_12m: float = Field(default=59.99, alias="PRICE_12M")

    # Features
    enable_pro_research: bool = Field(default=True, alias="ENABLE_PRO_RESEARCH")
    enable_formatter_pass: bool = Field(default=True, alias="ENABLE_FORMATTER_PASS")
    enable_auto_summary: bool = Field(default=False, alias="ENABLE_AUTO_SUMMARY")
    max_context_messages: int = Field(default=12, alias="MAX_CONTEXT_MESSAGES")

    # Scheduler / time
    timezone: str = Field(default="Europe/Moscow", alias="TIMEZONE")
    checkin_hour: int = Field(default=22, alias="CHECKIN_HOUR")
    checkin_minute: int = Field(default=0, alias="CHECKIN_MINUTE")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Optional: LanguageTool server for spellcheck
    language_tool_url: str | None = Field(default=None, alias="LANGUAGE_TOOL_URL")
