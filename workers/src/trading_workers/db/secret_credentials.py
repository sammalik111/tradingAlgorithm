import json
from functools import lru_cache

import boto3


@lru_cache
def _fetch_secret_json(secret_arn: str) -> dict:
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_arn)
    return json.loads(response["SecretString"])


def resolve_database_url(
    database_url: str | None,
    secret_arn: str | None,
    host: str | None,
    db_name: str | None,
) -> str:
    """Build the SQLAlchemy connection URL.

    Local dev sets `DATABASE_URL` directly. In AWS, Terraform instead sets
    `DB_SECRET_ARN`/`DB_HOST`/`DB_NAME`, and the password is read from the
    RDS-managed Secrets Manager secret at cold start rather than being
    embedded in a Lambda environment variable.
    """
    if database_url:
        return database_url

    if secret_arn and host and db_name:
        credentials = _fetch_secret_json(secret_arn)
        return (
            f"postgresql+asyncpg://{credentials['username']}:{credentials['password']}"
            f"@{host}:5432/{db_name}"
        )

    return "postgresql+asyncpg://trading:trading@localhost:5432/trading"
