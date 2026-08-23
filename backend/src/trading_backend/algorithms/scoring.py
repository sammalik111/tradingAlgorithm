import math
from dataclasses import dataclass
from datetime import UTC, date, datetime

from trading_backend.algorithms.clustering import consensus, consensus_multiplier
from trading_backend.models.enums import ConvictionLevel, RecommendationDirection, TransactionType

RECENCY_HALF_LIFE_DAYS = 21.0
AMOUNT_SATURATION_CAP = 5_000_000.0

BUY_THRESHOLD = 0.15
SELL_THRESHOLD = -0.15

CONVICTION_THRESHOLDS: dict[ConvictionLevel, float] = {
    ConvictionLevel.HIGH: 0.6,
    ConvictionLevel.MEDIUM: 0.3,
    ConvictionLevel.LOW: 0.0,
}

_DIRECTION_SIGN: dict[TransactionType, float] = {
    TransactionType.BUY: 1.0,
    TransactionType.SELL: -1.0,
    TransactionType.EXCHANGE: 0.0,
}


@dataclass(frozen=True)
class ScorableTrade:
    politician_id: object
    transaction_type: TransactionType
    transaction_date: date
    amount_mid: float


@dataclass(frozen=True)
class TickerScore:
    ticker: str
    signal_score: float
    direction: RecommendationDirection
    conviction: ConvictionLevel
    agreeing_politicians: int
    total_politicians: int


def recency_weight(transaction_date: date, as_of: date) -> float:
    """Exponential decay so recent disclosures dominate older ones.

    Returns 1.0 for a trade disclosed today, halving every
    `RECENCY_HALF_LIFE_DAYS` days.
    """
    days_ago = max((as_of - transaction_date).days, 0)
    return 0.5 ** (days_ago / RECENCY_HALF_LIFE_DAYS)


def size_weight(amount_mid: float) -> float:
    """Log-scaled, saturating weight for trade dollar size.

    A $1,000 trade barely moves the needle; a $1M+ trade approaches the
    maximum weight of 1.0 rather than dominating linearly.
    """
    if amount_mid <= 0:
        return 0.0
    return min(1.0, math.log10(amount_mid + 1) / math.log10(AMOUNT_SATURATION_CAP))


def trade_signal_strength(trade: ScorableTrade, as_of: date) -> float:
    """Signed contribution of a single trade toward its ticker's score."""
    sign = _DIRECTION_SIGN[trade.transaction_type]
    return sign * recency_weight(trade.transaction_date, as_of) * size_weight(trade.amount_mid)


def _bucket_conviction(magnitude: float) -> ConvictionLevel:
    for level in (ConvictionLevel.HIGH, ConvictionLevel.MEDIUM, ConvictionLevel.LOW):
        if magnitude >= CONVICTION_THRESHOLDS[level]:
            return level
    return ConvictionLevel.LOW


def _bucket_direction(signal_score: float) -> RecommendationDirection:
    if signal_score >= BUY_THRESHOLD:
        return RecommendationDirection.BUY
    if signal_score <= SELL_THRESHOLD:
        return RecommendationDirection.SELL
    return RecommendationDirection.HOLD


def score_ticker(
    ticker: str,
    trades: list[ScorableTrade],
    as_of: date | datetime | None = None,
) -> TickerScore:
    """Combine every deduplicated trade for a ticker into one recommendation
    signal.

    Each trade contributes a signed, recency- and size-weighted amount. The
    raw total is boosted when multiple distinct politicians agree on a
    direction, then squashed into [-1, 1] with tanh so no single outsized
    trade can dominate the final score.
    """
    if as_of is None:
        as_of_date = datetime.now(UTC).date()
    elif isinstance(as_of, datetime):
        as_of_date = as_of.date()
    else:
        as_of_date = as_of

    politician_ids_by_direction: dict[TransactionType, set] = {}
    raw_total = 0.0
    for trade in trades:
        raw_total += trade_signal_strength(trade, as_of_date)
        politician_ids_by_direction.setdefault(trade.transaction_type, set()).add(
            trade.politician_id
        )

    consensus_result = consensus(politician_ids_by_direction)
    boosted_total = raw_total * consensus_multiplier(consensus_result.agreeing_politicians)
    signal_score = math.tanh(boosted_total)

    return TickerScore(
        ticker=ticker,
        signal_score=signal_score,
        direction=_bucket_direction(signal_score),
        conviction=_bucket_conviction(abs(signal_score)),
        agreeing_politicians=consensus_result.agreeing_politicians,
        total_politicians=consensus_result.total_politicians,
    )
