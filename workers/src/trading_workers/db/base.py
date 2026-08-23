from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for the worker-side ORM models.

    These models map to the same Aurora tables as `backend/`'s models
    (schema owned by `backend/alembic`, documented in
    `documentation/database-schema.md`). Kept as a separate package,
    matching workers/backend being independently deployable apps.
    """
