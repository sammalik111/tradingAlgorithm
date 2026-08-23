import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from trading_workers.db.base import Base
from trading_workers.models.enums import TransactionType
from trading_workers.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CanonicalTrade(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The deduplicated, source-agnostic view of a disclosed trade. See
    `documentation/database-schema.md` for the collapsing rules this
    table enforces.
    """

    __tablename__ = "canonical_trades"
    __table_args__ = (UniqueConstraint("dedup_key", name="uq_canonical_trades_dedup_key"),)

    politician_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("politicians.id"), index=True
    )
    ticker: Mapped[str] = mapped_column(String(32), index=True)
    asset_name: Mapped[str] = mapped_column(String(256))
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="canonical_transaction_type")
    )
    transaction_date: Mapped[date] = mapped_column(Date, index=True)
    disclosure_date: Mapped[date] = mapped_column(Date)
    amount_min: Mapped[float] = mapped_column(Numeric(16, 2))
    amount_max: Mapped[float] = mapped_column(Numeric(16, 2))
    amount_mid: Mapped[float] = mapped_column(Numeric(16, 2))
    dedup_key: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    source_count: Mapped[int] = mapped_column(Integer, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    source_links: Mapped[list["CanonicalTradeSource"]] = relationship(
        back_populates="canonical_trade", cascade="all, delete-orphan"
    )


class CanonicalTradeSource(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "canonical_trade_sources"
    __table_args__ = (
        UniqueConstraint(
            "canonical_trade_id", "raw_trade_event_id", name="uq_canonical_trade_raw_event"
        ),
    )

    canonical_trade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_trades.id"), index=True
    )
    raw_trade_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("raw_trade_events.id")
    )
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id"))

    canonical_trade: Mapped[CanonicalTrade] = relationship(back_populates="source_links")
