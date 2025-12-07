from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Telegram
    bot_token: str = Field(..., alias="BOT_TOKEN")

    # LLM / DeepSeek
    deepseek_api_key: str = Field(..., alias="DEEPSEEK_API_KEY")
    deepseek_model: str = Field("deepseek-chat", alias="DEEPSEEK_MODEL")

    # Database
    # В .env можно использовать строку вида:
    # PLANNER_DATABASE_URL=postgresql://user:pass@host:5432/dbname
    database_url: str = Field(..., alias="PLANNER_DATABASE_URL")

    # Env
    environment: str = Field("development", alias="ENVIRONMENT")

    # Limits
    free_daily_requests: int = Field(50, alias="FREE_DAILY_REQUESTS")
    pro_daily_requests: int = Field(500, alias="PRO_DAILY_REQUESTS")
    vip_daily_requests: int = Field(2000, alias="VIP_DAILY_REQUESTS")

    admin_chat_id: int | None = Field(None, alias="ADMIN_CHAT_ID")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
