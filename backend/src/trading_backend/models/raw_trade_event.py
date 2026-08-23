import uuid
from datetime import date

from sqlalchemy import JSON, Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from trading_backend.db.base import Base
from trading_backend.models.enums import TransactionType
from trading_backend.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RawTradeEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single disclosure record exactly as scraped from one source.

    Never mutated after ingest. `dedup_key` is computed the same way as on
    `CanonicalTrade` so the ingest pipeline can group raw events that
    describe the same underlying trade across multiple sources.
    """

    __tablename__ = "raw_trade_events"

    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sources.id"))
    politician_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("politicians.id")
    )

    external_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    ticker_raw: Mapped[str] = mapped_column(String(32), index=True)
    asset_name_raw: Mapped[str] = mapped_column(String(256))
    transaction_type_raw: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type")
    )
    transaction_date: Mapped[date] = mapped_column(Date, index=True)
    disclosure_date: Mapped[date] = mapped_column(Date)
    amount_min: Mapped[float] = mapped_column(Numeric(16, 2))
    amount_max: Mapped[float] = mapped_column(Numeric(16, 2))
    raw_payload: Mapped[dict] = mapped_column(JSON)
    dedup_key: Mapped[str] = mapped_column(String(128), index=True)
