"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-23
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# create_type=False on every enum used in a column: the enums are created
# explicitly in upgrade() below (and dropped explicitly in downgrade()).
# Without this, op.create_table's DDL for an ENUM column re-issues
# CREATE TYPE unconditionally (Alembic executes CreateTable directly rather
# than through MetaData.create_all()'s checkfirst path, so the type's own
# checkfirst default never applies there), causing a duplicate-type error.
source_code_enum = postgresql.ENUM(
    "senate_stock_watcher",
    "house_stock_watcher",
    "quiver_quant",
    "sec_edgar",
    name="source_code",
    create_type=False,
)
chamber_enum = postgresql.ENUM("house", "senate", "executive", name="chamber", create_type=False)
transaction_type_enum = postgresql.ENUM(
    "buy", "sell", "exchange", name="transaction_type", create_type=False
)
canonical_transaction_type_enum = postgresql.ENUM(
    "buy", "sell", "exchange", name="canonical_transaction_type", create_type=False
)
conviction_level_enum = postgresql.ENUM(
    "low", "medium", "high", name="conviction_level", create_type=False
)
recommendation_direction_enum = postgresql.ENUM(
    "buy", "sell", "hold", name="recommendation_direction", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    for enum in (
        source_code_enum,
        chamber_enum,
        transaction_type_enum,
        canonical_transaction_type_enum,
        conviction_level_enum,
        recommendation_direction_enum,
    ):
        enum.create(bind, checkfirst=True)

    op.create_table(
        "sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("code", source_code_enum, nullable=False, unique=True),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("base_url", sa.String(512), nullable=False),
    )

    op.create_table(
        "politicians",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("full_name", sa.String(256), nullable=False),
        sa.Column("normalized_name", sa.String(256), nullable=False, unique=True),
        sa.Column("chamber", chamber_enum, nullable=False),
        sa.Column("party", sa.String(32), nullable=True),
        sa.Column("state", sa.String(2), nullable=True),
        sa.Column("bioguide_id", sa.String(32), nullable=True, unique=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_politicians_normalized_name", "politicians", ["normalized_name"])

    op.create_table(
        "raw_trade_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column(
            "politician_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("politicians.id"), nullable=False
        ),
        sa.Column("external_id", sa.String(256), nullable=True),
        sa.Column("ticker_raw", sa.String(32), nullable=False),
        sa.Column("asset_name_raw", sa.String(256), nullable=False),
        sa.Column("transaction_type_raw", transaction_type_enum, nullable=False),
        sa.Column("transaction_date", sa.Date, nullable=False),
        sa.Column("disclosure_date", sa.Date, nullable=False),
        sa.Column("amount_min", sa.Numeric(16, 2), nullable=False),
        sa.Column("amount_max", sa.Numeric(16, 2), nullable=False),
        sa.Column("raw_payload", sa.JSON, nullable=False),
        sa.Column("dedup_key", sa.String(128), nullable=False),
    )
    op.create_index("ix_raw_trade_events_ticker_raw", "raw_trade_events", ["ticker_raw"])
    op.create_index("ix_raw_trade_events_transaction_date", "raw_trade_events", ["transaction_date"])
    op.create_index("ix_raw_trade_events_dedup_key", "raw_trade_events", ["dedup_key"])

    op.create_table(
        "canonical_trades",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "politician_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("politicians.id"), nullable=False
        ),
        sa.Column("ticker", sa.String(32), nullable=False),
        sa.Column("asset_name", sa.String(256), nullable=False),
        sa.Column("transaction_type", canonical_transaction_type_enum, nullable=False),
        sa.Column("transaction_date", sa.Date, nullable=False),
        sa.Column("disclosure_date", sa.Date, nullable=False),
        sa.Column("amount_min", sa.Numeric(16, 2), nullable=False),
        sa.Column("amount_max", sa.Numeric(16, 2), nullable=False),
        sa.Column("amount_mid", sa.Numeric(16, 2), nullable=False),
        sa.Column("dedup_key", sa.String(128), nullable=False),
        sa.Column("source_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("dedup_key", name="uq_canonical_trades_dedup_key"),
    )
    op.create_index("ix_canonical_trades_politician_id", "canonical_trades", ["politician_id"])
    op.create_index("ix_canonical_trades_ticker", "canonical_trades", ["ticker"])
    op.create_index("ix_canonical_trades_transaction_date", "canonical_trades", ["transaction_date"])
    op.create_index("ix_canonical_trades_dedup_key", "canonical_trades", ["dedup_key"])

    op.create_table(
        "canonical_trade_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "canonical_trade_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("canonical_trades.id"),
            nullable=False,
        ),
        sa.Column(
            "raw_trade_event_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("raw_trade_events.id"),
            nullable=False,
        ),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sources.id"), nullable=False),
        sa.UniqueConstraint(
            "canonical_trade_id", "raw_trade_event_id", name="uq_canonical_trade_raw_event"
        ),
    )
    op.create_index(
        "ix_canonical_trade_sources_canonical_trade_id",
        "canonical_trade_sources",
        ["canonical_trade_id"],
    )

    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ticker", sa.String(32), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("signal_score", sa.Numeric(6, 4), nullable=False),
        sa.Column("conviction", conviction_level_enum, nullable=False),
        sa.Column("direction", recommendation_direction_enum, nullable=False),
        sa.Column("rationale_text", sa.Text, nullable=True),
        sa.Column("model_version", sa.String(64), nullable=False),
    )
    op.create_index("ix_recommendations_ticker", "recommendations", ["ticker"])

    op.create_table(
        "recommendation_supporting_trades",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "recommendation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recommendations.id"),
            nullable=False,
        ),
        sa.Column(
            "canonical_trade_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("canonical_trades.id"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_recommendation_supporting_trades_recommendation_id",
        "recommendation_supporting_trades",
        ["recommendation_id"],
    )


def downgrade() -> None:
    op.drop_table("recommendation_supporting_trades")
    op.drop_table("recommendations")
    op.drop_table("canonical_trade_sources")
    op.drop_table("canonical_trades")
    op.drop_table("raw_trade_events")
    op.drop_table("politicians")
    op.drop_table("sources")

    bind = op.get_bind()
    for enum in (
        recommendation_direction_enum,
        conviction_level_enum,
        canonical_transaction_type_enum,
        transaction_type_enum,
        chamber_enum,
        source_code_enum,
    ):
        enum.drop(bind, checkfirst=True)
