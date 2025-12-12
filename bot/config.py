from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    BOT_TOKEN: SecretStr
    DB_DSN: str
    DEEPSEEK_API_KEY: SecretStr | None = None
    PERPLEXITY_API_KEY: SecretStr | None = None
    CRYPTO_BOT_TOKEN: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )

settings = Settings()
