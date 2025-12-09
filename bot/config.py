from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")

    deepseek_api_key: Optional[str] = Field(None, alias="DEEPSEEK_API_KEY")
    deepseek_model: str = Field("deepseek-chat", alias="DEEPSEEK_MODEL")

    perplexity_api_key: Optional[str] = Field(None, alias="PERPLEXITY_API_KEY")
    perplexity_model: str = Field("sonar", alias="PERPLEXITY_MODEL")

    llm_provider: str = Field("auto", alias="LLM_PROVIDER")

    database_url: str = Field(
        "sqlite+aiosqlite:///./blackboxgpt.db",
        alias="DATABASE_URL",
    )

    bot_name: str = Field("BlackBox GPT - Universal AI Assistant", alias="BOT_NAME")
    bot_username: str = Field("BlackBoxGPT_bot", alias="BOT_USERNAME")
    environment: str = Field("prod", alias="ENVIRONMENT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def bot_link(self) -> str:
        return f"https://t.me/{self.bot_username.lstrip('@')}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
