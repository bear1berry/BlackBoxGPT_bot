from __future__ import annotations

from typing import Optional, Dict, List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Глобальные настройки бота.
    Все значения подтягиваются из .env.
    """

    # Общая конфигурация Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",          # имена переменных берём как есть
        case_sensitive=False,   # BOT_TOKEN == bot_token
        extra="ignore",         # лишние ключи в .env просто игнорируем
    )

    # === Telegram / Core ===
    bot_token: str = Field(..., alias="BOT_TOKEN")
    database_url: str = Field(..., alias="DATABASE_URL")

    # Админы (строка "1,2,3" -> парсим в список)
    admin_ids_raw: Optional[str] = Field(default=None, alias="ADMIN_IDS")

    # === Perplexity ===
    perplexity_api_key: Optional[str] = Field(default=None, alias="PERPLEXITY_API_KEY")
    perplexity_api_base: str = Field(
        default="https://api.perplexity.ai", alias="PERPLEXITY_API_BASE"
    )

    # Модели по режимам
    perplexity_model_universal: str = Field(
        default="sonar-reasoning-pro", alias="PERPLEXITY_MODEL_UNIVERSAL"
    )
    perplexity_model_medicine: str = Field(
        default="sonar-reasoning-pro", alias="PERPLEXITY_MODEL_MEDICINE"
    )
    perplexity_model_mentor: str = Field(
        default="sonar-reasoning-pro", alias="PERPLEXITY_MODEL_MENTOR"
    )
    perplexity_model_business: str = Field(
        default="sonar-reasoning-pro", alias="PERPLEXITY_MODEL_BUSINESS"
    )
    perplexity_model_creative: str = Field(
        default="sonar-reasoning-pro", alias="PERPLEXITY_MODEL_CREATIVE"
    )

    # === DeepSeek ===
    deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_api_base: str = Field(
        default="https://api.deepseek.com", alias="DEEPSEEK_API_BASE"
    )
    deepseek_model_default: str = Field(
        default="deepseek-chat", alias="DEEPSEEK_MODEL_DEFAULT"
    )

    # === Crypto Bot / Подписки ===
    crypto_pay_api_key: Optional[str] = Field(default=None, alias="CRYPTO_PAY_API_KEY")
    crypto_bot_username: str = Field(default="CryptoBot", alias="CRYPTO_BOT_USERNAME")
    crypto_currency: str = Field(default="USDT", alias="CRYPTO_CURRENCY")

    price_1m: float = Field(default=7.99, alias="PRICE_1M")
    price_3m: float = Field(default=25.99, alias="PRICE_3M")
    price_12m: float = Field(default=89.99, alias="PRICE_12M")

    # === Рефералка ===
    referral_bonus_days_inviter: int = Field(
        default=7, alias="REFERRAL_BONUS_DAYS_INVITER"
    )
    referral_bonus_days_invited: int = Field(
        default=7, alias="REFERRAL_BONUS_DAYS_INVITED"
    )

    # === Yandex SpeechKit (аудио) ===
    yandex_iam_token: Optional[str] = Field(default=None, alias="YANDEX_IAM_TOKEN")
    yandex_folder_id: Optional[str] = Field(default=None, alias="YANDEX_FOLDER_ID")
    yandex_tts_voice: str = Field(default="filipp", alias="YANDEX_TTS_VOICE")
    yandex_tts_lang: str = Field(default="ru-RU", alias="YANDEX_TTS_LANG")

    # === Логи / таймауты ===
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    llm_timeout_sec: int = Field(default=120, alias="LLM_TIMEOUT_SEC")

    # ========= Хелперы / алиасы =========

    @property
    def admin_ids(self) -> List[int]:
        """Парсим ADMIN_IDS в список int."""
        if not self.admin_ids_raw:
            return []
        parts = [p.strip() for p in str(self.admin_ids_raw).split(",") if p.strip()]
        out: List[int] = []
        for p in parts:
            try:
                out.append(int(p))
            except ValueError:
                # если вдруг мусор — просто пропускаем
                continue
        return out

    # Uppercase-алиасы для обратной совместимости
    @property
    def BOT_TOKEN(self) -> str:
        return self.bot_token

    @property
    def DATABASE_URL(self) -> str:
        return self.database_url

    @property
    def ADMIN_IDS(self) -> List[int]:
        return self.admin_ids

    @property
    def PERPLEXITY_API_KEY(self) -> Optional[str]:
        return self.perplexity_api_key

    @property
    def PERPLEXITY_API_BASE(self) -> str:
        return self.perplexity_api_base

    @property
    def DEEPSEEK_API_KEY(self) -> Optional[str]:
        return self.deepseek_api_key

    @property
    def DEEPSEEK_API_BASE(self) -> str:
        return self.deepseek_api_base

    @property
    def LOG_LEVEL(self) -> str:
        return self.log_level

    @property
    def LLM_TIMEOUT_SEC(self) -> int:
        return self.llm_timeout_sec

    @property
    def perplexity_model_map(self) -> Dict[str, str]:
        """
        Карта режимов -> моделей Perplexity.
        Используется, чтобы по текущему режиму доставать нужную модель.
        """
        return {
            "universal": self.perplexity_model_universal,
            "medicine": self.perplexity_model_medicine,
            "mentor": self.perplexity_model_mentor,
            "business": self.perplexity_model_business,
            "creative": self.perplexity_model_creative,
        }


settings = Settings()
