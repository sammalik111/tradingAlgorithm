from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from trading_workers.db.secret_credentials import resolve_database_url


class Settings(BaseSettings):
    """Runtime configuration, sourced from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    log_level: str = "INFO"

    # Local dev sets `database_url` directly. In AWS, Terraform instead sets
    # `db_secret_arn`/`db_host`/`db_name` and the password is resolved from
    # the RDS-managed Secrets Manager secret at cold start.
    database_url: str | None = None
    db_secret_arn: str | None = None
    db_host: str | None = None
    db_name: str | None = None
    database_pool_size: int = 5
    database_echo: bool = False

    aws_region: str = "us-east-1"
    trade_ingest_queue_url: str | None = None
    # Unset in AWS (real endpoints). Local dev points this at LocalStack
    # (see docker-compose.yml) so `sqs_client.py` never needs to know the
    # difference -- boto3 treats endpoint_url=None as "use the real AWS
    # endpoint" for either service.
    aws_endpoint_url: str | None = None

    quiver_quant_api_key: str | None = None

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
