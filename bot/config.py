from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Единая конфигурация бота.

    ВАЖНО:
    - Имена полей == именам переменных в .env (регистр не важен, case_sensitive=False).
    - Любые лишние ключи в .env будут проигнорированы (extra='ignore'),
      поэтому больше не будет ошибок `extra_forbidden`.
    """

    # ---- Pydantic Settings config ----
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,   # BOT_TOKEN и bot_token — одно и то же
        extra="ignore",         # игнорировать неизвестные ключи в .env
    )

    # ---- Core / Telegram / DB ----
    bot_token: str = Field(..., description="Telegram Bot API token")
    database_url: str = Field(..., description="SQLAlchemy Database URL, например postgresql+asyncpg://")

    # список админов строкой: '123,456'
    admin_ids_raw: Optional[str] = Field(
        default=None,
        description="Список tg_id админов через запятую, например '123,456'",
    )

    # ---- LLM / Perplexity / DeepSeek ----
    perplexity_api_key: Optional[str] = Field(
        default=None,
        description="API ключ Perplexity (если не задан, будет использоваться только DeepSeek)",
    )
    perplexity_api_base: str = Field(
        default="https://api.perplexity.ai",
        description="Базовый URL Perplexity API",
    )

    # Модели Perplexity по режимам
    perplexity_model_universal: str = Field(
        default="sonar-reasoning-pro",
        description="Модель для универсального режима",
    )
    perplexity_model_medicine: str = Field(
        default="sonar-reasoning-pro",
        description="Модель для медицинского режима",
    )
    perplexity_model_mentor: str = Field(
        default="sonar-reasoning",
        description="Модель для режима Наставник",
    )
    perplexity_model_business: str = Field(
        default="sonar-reasoning-pro",
        description="Модель для бизнес-режима",
    )
    perplexity_model_creative: str = Field(
        default="sonar-reasoning-pro",
        description="Модель для креативного режима",
    )

    # DeepSeek
    deepseek_api_key: Optional[str] = Field(
        default=None,
        description="API ключ DeepSeek",
    )
    deepseek_api_base: str = Field(
        default="https://api.deepseek.com",
        description="Базовый URL DeepSeek API",
    )
    deepseek_model_fast: str = Field(
        default="deepseek-chat",
        description="Быстрая модель DeepSeek",
    )
    deepseek_model_slow: str = Field(
        default="deepseek-reasoner",
        description="Продвинутая медленная модель DeepSeek",
    )

    # ---- Audio / Yandex (STT/TTS) ----
    yandex_iam_token: Optional[str] = Field(
        default=None,
        description="IAM-токен Яндекс Облака для SpeechKit",
    )
    yandex_folder_id: Optional[str] = Field(
        default=None,
        description="ID каталога Яндекс Облака",
    )
    yandex_tts_voice: str = Field(
        default="filipp",
        description="Голос TTS, например 'filipp'",
    )
    yandex_tts_lang: str = Field(
        default="ru-RU",
        description="Язык TTS, например 'ru-RU'",
    )

    # ---- Crypto Pay / Подписки ----
    crypto_pay_token: Optional[str] = Field(
        default=None,
        description="Токен для Crypto Pay Bot",
    )

    # Цены в USD — используются в логике подписки
    price_1m: float = Field(
        default=7.99,
        description="Цена за 1 месяц подписки",
    )
    price_3m: float = Field(
        default=25.99,
        description="Цена за 3 месяца подписки",
    )
    price_12m: float = Field(
        default=89.99,
        description="Цена за 12 месяцев подписки",
    )

    # ---- Логирование / таймауты ----
    log_level: str = Field(
        default="INFO",
        description="Уровень логирования (DEBUG / INFO / WARNING / ERROR)",
    )
    llm_timeout_sec: int = Field(
        default=120,
        description="Таймаут запросов к LLM в секундах",
    )

    # ---- Вычисляемые поля / совместимость ----
    @computed_field
    @property
    def admin_ids(self) -> List[int]:
        """
        Возвращает список админов как int-ы.
        """
        if not self.admin_ids_raw:
            return []
        result: List[int] = []
        for part in self.admin_ids_raw.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                result.append(int(part))
            except ValueError:
                # Просто игнорируем мусор
                continue
        return result

    # Свойства для обратной совместимости с кодом, где могли использовать старые имена
    @property
    def BOT_TOKEN(self) -> str:
        return self.bot_token

    @property
    def DATABASE_URL(self) -> str:
        return self.database_url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# главный объект настроек, который импортируется по всему проекту
settings: Settings = get_settings()
