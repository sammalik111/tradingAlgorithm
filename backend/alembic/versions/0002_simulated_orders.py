"""simulated orders

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-24
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# create_type=False: create_table below would otherwise re-issue CREATE TYPE
# for this column and fail with a duplicate-type error -- see 0001 for the
# full explanation of why Alembic's create_table bypasses checkfirst here.
order_side_enum = postgresql.ENUM("buy", "sell", name="order_side", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    order_side_enum.create(bind, checkfirst=True)

    op.create_table(
        "simulated_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "recommendation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recommendations.id"),
            nullable=False,
        ),
        sa.Column("ticker", sa.String(32), nullable=False),
        sa.Column("side", order_side_enum, nullable=False),
        sa.Column("quantity", sa.Numeric(16, 4), nullable=False),
        sa.Column("price", sa.Numeric(16, 2), nullable=False),
        sa.Column("notional_value", sa.Numeric(16, 2), nullable=False),
    )
    op.create_index(
        "ix_simulated_orders_recommendation_id", "simulated_orders", ["recommendation_id"]
    )


def downgrade() -> None:
    op.drop_table("simulated_orders")

    bind = op.get_bind()
    order_side_enum.drop(bind, checkfirst=True)
