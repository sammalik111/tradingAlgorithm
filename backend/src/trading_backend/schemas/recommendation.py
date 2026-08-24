import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from trading_backend.models.enums import ConvictionLevel, RecommendationDirection, TransactionType
from trading_backend.schemas.order import SimulatedOrderOut


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ticker: str
    generated_at: datetime
    signal_score: float
    conviction: ConvictionLevel
    direction: RecommendationDirection
    rationale_text: str | None
    model_version: str


class ScoringBreakdownTrade(BaseModel):
    canonical_trade_id: uuid.UUID
    politician_name: str
    transaction_type: TransactionType
    transaction_date: date
    amount_mid: float
    recency_weight: float
    size_weight: float
    signal_contribution: float


class ScoringBreakdown(BaseModel):
    """Recomputed at read time from the supporting trades using the same
    pure functions the recommendation engine used to generate the score
    (see algorithms/scoring.py) -- none of this is persisted separately, so
    it always reflects the current scoring logic, not necessarily the exact
    numbers in effect the night this recommendation was generated.
    """

    raw_total: float
    agreeing_politicians: int
    total_politicians: int
    consensus_multiplier: float


class RecommendationDetail(RecommendationOut):
    scoring_breakdown: ScoringBreakdown
    supporting_trades: list[ScoringBreakdownTrade]
    simulated_orders: list[SimulatedOrderOut]
