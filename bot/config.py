from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Централизованный конфиг для BlackBox GPT.

    Все переменные берутся из .env. Название переменной = имя поля в UPPER_CASE:
    - bot_token -> BOT_TOKEN
    - database_url -> DATABASE_URL
    - perplexity_api_base -> PERPLEXITY_API_BASE
    и т.д.
    """

    # Общая конфигурация pydantic-settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # не ругаемся на лишние переменные в .env
    )

    # ───────────────────────────
    # Telegram / базовые настройки
    # ───────────────────────────
    bot_token: str = Field(..., description="Токен Telegram-бота (BOT_TOKEN)")
    admin_ids: List[int] = Field(
        default_factory=list,
        description="Список ID админов, например: 123,456 (ADMIN_IDS)",
    )

    # ───────────────────────────
    # База данных
    # ───────────────────────────
    database_url: str = Field(
        ...,
        description="DSN для PostgreSQL, например: postgresql+asyncpg://user:pass@host:5432/dbname (DATABASE_URL)",
    )

    # ───────────────────────────
    # Логирование и таймауты
    # ───────────────────────────
    log_level: str = Field(
        default="INFO",
        description="Уровень логов: DEBUG / INFO / WARNING / ERROR (LOG_LEVEL)",
    )
    llm_timeout_sec: int = Field(
        default=120,
        description="Таймаут запросов к LLM в секундах (LLM_TIMEOUT_SEC)",
    )

    # ───────────────────────────
    # DeepSeek (LLM)
    # ───────────────────────────
    deepseek_api_key: str = Field(
        ...,
        description="API ключ DeepSeek (DEEPSEEK_API_KEY)",
    )
    deepseek_api_base: str = Field(
        default="https://api.deepseek.com",
        description="Базовый URL DeepSeek API (DEEPSEEK_API_BASE)",
    )

    # Базовые модели DeepSeek (можно перегрузить из .env при желании)
    deepseek_default_model: str = Field(
        default="deepseek-chat",
        description="Модель по умолчанию для DeepSeek (DEEPSEEK_DEFAULT_MODEL)",
    )
    deepseek_reasoning_model: str = Field(
        default="deepseek-reasoner",
        description="Reasoning-модель для DeepSeek (DEEPSEEK_REASONING_MODEL)",
    )

    # ───────────────────────────
    # Perplexity (LLM + web search)
    # ───────────────────────────
    perplexity_api_key: str = Field(
        ...,
        description="API ключ Perplexity (PERPLEXITY_API_KEY)",
    )
    perplexity_api_base: str = Field(
        default="https://api.perplexity.ai",
        description="Базовый URL Perplexity API (PERPLEXITY_API_BASE)",
    )

    # Модели Perplexity по режимам (можно переопределить в .env)
    perplexity_universal_model: str = Field(
        default="sonar",
        description="Модель для универсального режима (PERPLEXITY_UNIVERSAL_MODEL)",
    )
    perplexity_mentor_model: str = Field(
        default="sonar-reasoning",
        description="Модель для режима Наставник (PERPLEXITY_MENTOR_MODEL)",
    )
    perplexity_medicine_model: str = Field(
        default="sonar",
        description="Модель для режима Медицина (PERPLEXITY_MEDICINE_MODEL)",
    )
    perplexity_business_model: str = Field(
        default="sonar",
        description="Модель для режима Бизнес (PERPLEXITY_BUSINESS_MODEL)",
    )
    perplexity_creative_model: str = Field(
        default="sonar",
        description="Модель для режима Креатив (PERPLEXITY_CREATIVE_MODEL)",
    )

    # ───────────────────────────
    # Яндекс: аудио (TTS/STT)
    # ───────────────────────────
    yandex_iam_token: Optional[str] = Field(
        default=None,
        description="IAM-токен Яндекса для SpeechKit (YANDEX_IAM_TOKEN)",
    )
    yandex_folder_id: Optional[str] = Field(
        default=None,
        description="ID каталога в Яндекс Cloud (YANDEX_FOLDER_ID)",
    )
    yandex_tts_voice: str = Field(
        default="filipp",
        description="Голос TTS, например filipp, jane, oksana (YANDEX_TTS_VOICE)",
    )
    yandex_tts_lang: str = Field(
        default="ru-RU",
        description="Язык TTS, например ru-RU (YANDEX_TTS_LANG)",
    )

    # ───────────────────────────
    # Crypto Bot / Crypto Pay — подписки
    # ───────────────────────────
    crypto_pay_api_key: Optional[str] = Field(
        default=None,
        description="API ключ Crypto Pay (CRYPTO_PAY_API_KEY)",
    )
    crypto_pay_app_url: Optional[str] = Field(
        default=None,
        description="Ссылка на приложение / магазин в Crypto Bot (CRYPTO_PAY_APP_URL)",
    )
    crypto_pay_currency: str = Field(
        default="USDT",
        description="Валюта платежей: USDT / TON и т.п. (CRYPTO_PAY_CURRENCY)",
    )

    # Стоимость подписок (в USD, но считать можешь как удобно)
    price_1m: Decimal = Field(
        default=Decimal("7.99"),
        description="Цена подписки на 1 месяц (PRICE_1M)",
    )
    price_3m: Decimal = Field(
        default=Decimal("25.99"),
        description="Цена подписки на 3 месяца (PRICE_3M)",
    )
    price_12m: Decimal = Field(
        default=Decimal("89.99"),
        description="Цена подписки на 12 месяцев (PRICE_12M)",
    )

    # ───────────────────────────
    # Подписки / рефералка / бонусы
    # ───────────────────────────
    free_trial_days: int = Field(
        default=0,
        description="Дни бесплатного пробного периода (FREE_TRIAL_DAYS)",
    )
    referral_bonus_days: int = Field(
        default=3,
        description="Сколько дней подписки даёт один реферал (REFERRAL_BONUS_DAYS)",
    )

    # ───────────────────────────
    # Прочее
    # ───────────────────────────
    project_name: str = Field(
        default="BlackBox GPT",
        description="Имя проекта / бота (PROJECT_NAME)",
    )


# Глобальный объект настроек
settings = Settings()
