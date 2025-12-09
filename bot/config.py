from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    bot_token: str = Field(alias="BOT_TOKEN")
    bot_username: str = Field(alias="BOT_USERNAME")

    database_url: str = Field(alias="DATABASE_URL")

    # LLM providers
    llm_provider: str = Field(default="perplexity", alias="LLM_PROVIDER")

    perplexity_api_key: str | None = Field(default=None, alias="PERPLEXITY_API_KEY")
    perplexity_model_universal: str = Field(default="sonar-pro", alias="PERPLEXITY_MODEL_UNIVERSAL")
    perplexity_model_mentor: str = Field(default="sonar-reasoning", alias="PERPLEXITY_MODEL_MENTOR")
    perplexity_model_medicine: str = Field(default="sonar-pro", alias="PERPLEXITY_MODEL_MEDICINE")
    perplexity_model_business: str = Field(default="sonar-pro", alias="PERPLEXITY_MODEL_BUSINESS")
    perplexity_model_creative: str = Field(default="sonar", alias="PERPLEXITY_MODEL_CREATIVE")

    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")

    # Crypto Pay / Crypto Bot
    cryptopay_api_token: str | None = Field(default=None, alias="CRYPTOPAY_API_TOKEN")
    cryptopay_asset: str = Field(default="USDT", alias="CRYPTOPAY_ASSET")

    subscription_price_1m: float = Field(default=7.99, alias="SUBSCRIPTION_PRICE_1M")
    subscription_price_3m: float = Field(default=25.99, alias="SUBSCRIPTION_PRICE_3M")
    subscription_price_12m: float = Field(default=89.99, alias="SUBSCRIPTION_PRICE_12M")

    referral_reward_days: int = Field(default=7, alias="REFERRAL_REWARD_DAYS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def bot_link(self) -> str:
        username = self.bot_username.lstrip("@")
        return f"https://t.me/{username}"


settings = Settings()
