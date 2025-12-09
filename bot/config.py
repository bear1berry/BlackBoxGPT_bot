from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str
    BOT_USERNAME: str  # например: BlackBoxGPT_bot

    PERPLEXITY_API_KEY: str
    PERPLEXITY_API_URL: str = "https://api.perplexity.ai"

    # Пример для PostgreSQL через asyncpg
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/blackboxgpt"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
