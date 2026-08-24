"""add senate_efd source code

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-24 05:36:04.583223
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Postgres 12+ allows ALTER TYPE ... ADD VALUE inside a transaction as
    # long as the new value isn't used in that same transaction, which
    # this migration doesn't do -- safe here.
    op.execute("ALTER TYPE source_code ADD VALUE IF NOT EXISTS 'senate_efd'")


def downgrade() -> None:
    # Postgres has no DROP VALUE for enum types -- downgrading this
    # migration leaves 'senate_efd' in the source_code type. Harmless to
    # leave (unlike the tables/columns other migrations' downgrade()
    # actually reverse): an unused enum label with no rows referencing it.
    pass
