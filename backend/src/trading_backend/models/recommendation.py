import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from trading_backend.db.base import Base
from trading_backend.models.enums import ConvictionLevel, RecommendationDirection
from trading_backend.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Recommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A generated buy/sell/hold signal for a ticker, produced by the
    scoring algorithm in `algorithms/scoring.py` and narrated by Claude.
    """

    __tablename__ = "recommendations"

    ticker: Mapped[str] = mapped_column(String(32), index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    signal_score: Mapped[float] = mapped_column(Numeric(6, 4))
    conviction: Mapped[ConvictionLevel] = mapped_column(
        Enum(ConvictionLevel, name="conviction_level")
    )
    direction: Mapped[RecommendationDirection] = mapped_column(
        Enum(RecommendationDirection, name="recommendation_direction")
    )
    rationale_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_version: Mapped[str] = mapped_column(String(64))

    supporting_trade_links: Mapped[list["RecommendationSupportingTrade"]] = relationship(
        back_populates="recommendation", cascade="all, delete-orphan"
    )


class RecommendationSupportingTrade(UUIDPrimaryKeyMixin, Base):
    """Join row linking a recommendation to the canonical trades that fed
    its score, so a recommendation's provenance can always be audited.
    """

    __tablename__ = "recommendation_supporting_trades"

    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendations.id"), index=True
    )
    canonical_trade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("canonical_trades.id")
    )

    recommendation: Mapped[Recommendation] = relationship(back_populates="supporting_trade_links")
