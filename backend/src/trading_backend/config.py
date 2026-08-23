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

    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl_seconds: int = 300

    anthropic_api_key: str | None = None
    recommendation_model: str = "claude-sonnet-5"

    cors_allowed_origins: str = "http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
