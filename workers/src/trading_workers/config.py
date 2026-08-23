from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://trading:trading@localhost:5432/trading"
    database_pool_size: int = 5
    database_echo: bool = False

    aws_region: str = "us-east-1"
    trade_ingest_queue_url: str | None = None

    quiver_quant_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
