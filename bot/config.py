from __future__ import annotations

from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Центральная конфигурация бота.
    Все значения берутся из .env / переменных окружения.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # 🔥 Главное: не падать от лишних ключей в .env
    )

    # =========================
    # Telegram / Bot
    # =========================
    bot_token: str = Field(..., alias="BOT_TOKEN")
    database_url: str = Field(..., alias="DATABASE_URL")

    admin_ids: List[int] = Field(default_factory=list, alias="ADMIN_IDS")

    # =========================
    # LLM: Perplexity
    # =========================
    # Ключ API
    perplexity_api_key: Optional[str] = Field(
        default=None,
        alias="PERPLEXITY_API_KEY",
    )
    # Базовый URL
    perplexity_api_base: Optional[str] = Field(
        default="https://api.perplexity.ai",
        alias="PERPLEXITY_API_BASE",
    )

    # Модели по режимам
    perplexity_model_universal: str = Field(
        default="sonar-reasoning-pro",
        alias="PERPLEXITY_MODEL_UNIVERSAL",
    )
    perplexity_model_medicine: str = Field(
        default="sonar-reasoning-pro",
        alias="PERPLEXITY_MODEL_MEDICINE",
    )
    perplexity_model_mentor: str = Field(
        default="sonar-reasoning-pro",
        alias="PERPLEXITY_MODEL_MENTOR",
    )
    perplexity_model_business: str = Field(
        default="sonar-reasoning-pro",
        alias="PERPLEXITY_MODEL_BUSINESS",
    )
    perplexity_model_creative: str = Field(
        default="sonar-reasoning-pro",
        alias="PERPLEXITY_MODEL_CREATIVE",
    )

    # =========================
    # LLM: DeepSeek
    # =========================
    deepseek_api_key: Optional[str] = Field(
        default=None,
        alias="DEEPSEEK_API_KEY",
    )
    deepseek_api_base: Optional[str] = Field(
        default="https://api.deepseek.com",
        alias="DEEPSEEK_API_BASE",
    )
    deepseek_model_default: str = Field(
        default="deepseek-chat",
        alias="DEEPSEEK_MODEL_DEFAULT",
    )

    # =========================
    # Payments / CryptoBot
    # =========================
    # токен Crypto Pay (API)
    crypto_pay_api_key: Optional[str] = Field(
        default=None,
        alias="CRYPTO_PAY_API_KEY",
    )
    # username CryptoBot, обычно CryptoBot
    crypto_bot_username: str = Field(
        default="CryptoBot",
        alias="CRYPTO_BOT_USERNAME",
    )
    # Валюта (USDT, TON и т.д.)
    crypto_currency: str = Field(
        default="USDT",
        alias="CRYPTO_CURRENCY",
    )

    # Цены подписки (в валюте, указанной выше)
    price_1m: float = Field(default=7.99, alias="PRICE_1M")
    price_3m: float = Field(default=25.99, alias="PRICE_3M")
    price_12m: float = Field(default=89.99, alias="PRICE_12M")

    # =========================
    # Referrals
    # =========================
    referral_bonus_days_for_inviter: int = Field(
        default=7,
        alias="REFERRAL_BONUS_DAYS_INVITER",
    )
    referral_bonus_days_for_invited: int = Field(
        default=7,
        alias="REFERRAL_BONUS_DAYS_INVITED",
    )

    # =========================
    # Yandex SpeechKit / Audio
    # =========================
    # Всё ниже мы как раз и добавили, чтобы не было
    # ValidationError по yandex_* и чтобы аудио работало.
    yandex_iam_token: Optional[str] = Field(
        default=None,
        alias="YANDEX_IAM_TOKEN",
    )
    yandex_folder_id: Optional[str] = Field(
        default=None,
        alias="YANDEX_FOLDER_ID",
    )
    yandex_tts_voice: str = Field(
        default="filipp",
        alias="YANDEX_TTS_VOICE",
    )
    yandex_tts_lang: str = Field(
        default="ru-RU",
        alias="YANDEX_TTS_LANG",
    )

    # =========================
    # Misc / Логика
    # =========================
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    llm_timeout_sec: int = Field(default=120, alias="LLM_TIMEOUT_SEC")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        """
        ADMIN_IDS в .env можно задать так:
        ADMIN_IDS=123456789,987654321
        """
        if not v:
            return []
        if isinstance(v, list):
            return [int(x) for x in v]
        # строка вида "123,456"
        text = str(v).replace(" ", "")
        if not text:
            return []
        return [int(x) for x in text.split(",") if x]


settings = Settings()
