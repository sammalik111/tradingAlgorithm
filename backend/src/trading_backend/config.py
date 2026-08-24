from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from trading_backend.db.secret_credentials import resolve_database_url


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"

    # Local dev sets `database_url` directly. In AWS, Terraform instead sets
    # `db_secret_arn`/`db_host`/`db_name` and the password is resolved from
    # the RDS-managed Secrets Manager secret at cold start, never embedded
    # in a Lambda environment variable.
    database_url: str | None = None
    db_secret_arn: str | None = None
    db_host: str | None = None
    db_name: str | None = None
    database_pool_size: int = 5
    database_echo: bool = False

    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl_seconds: int = 300

    anthropic_api_key: str | None = None
    recommendation_model: str = "claude-sonnet-5"

    cors_allowed_origins: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def resolved_database_url(self) -> str:
        return resolve_database_url(
            database_url=self.database_url,
            secret_arn=self.db_secret_arn,
            host=self.db_host,
            db_name=self.db_name,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
