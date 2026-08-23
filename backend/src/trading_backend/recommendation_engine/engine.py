from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from trading_backend.algorithms.scoring import ScorableTrade, TickerScore, score_ticker
from trading_backend.config import get_settings
from trading_backend.integrations.claude.client import ClaudeNotConfiguredError
from trading_backend.integrations.claude.rationale import SupportingTradeSummary, generate_rationale
from trading_backend.models.canonical_trade import CanonicalTrade
from trading_backend.models.politician import Politician
from trading_backend.models.recommendation import Recommendation, RecommendationSupportingTrade

SCORING_WINDOW_DAYS = 90


async def _load_recent_trades_by_ticker(
    db: AsyncSession, as_of: datetime
) -> dict[str, list[CanonicalTrade]]:
    window_start = (as_of - timedelta(days=SCORING_WINDOW_DAYS)).date()
    stmt = select(CanonicalTrade).where(CanonicalTrade.transaction_date >= window_start)
    result = await db.execute(stmt)

    trades_by_ticker: dict[str, list[CanonicalTrade]] = defaultdict(list)
    for trade in result.scalars().all():
        trades_by_ticker[trade.ticker].append(trade)
    return trades_by_ticker


async def _persist_recommendation(
    db: AsyncSession,
    score: TickerScore,
    trades: list[CanonicalTrade],
    as_of: datetime,
    model_version: str,
) -> Recommendation:
    politician_ids = {t.politician_id for t in trades}
    politicians_stmt = select(Politician).where(Politician.id.in_(politician_ids))
    politicians_result = await db.execute(politicians_stmt)
    politicians = {p.id: p for p in politicians_result.scalars().all()}

    rationale_text: str | None = None
    try:
        rationale_text = await generate_rationale(
            score,
            [
                SupportingTradeSummary(
                    politician_name=politicians[t.politician_id].full_name,
                    direction=t.transaction_type.value,
                    transaction_date=t.transaction_date.isoformat(),
                    amount_range=f"${t.amount_min:,.0f}-${t.amount_max:,.0f}",
                )
                for t in trades
            ],
        )
    except ClaudeNotConfiguredError:
        rationale_text = None

    recommendation = Recommendation(
        ticker=score.ticker,
        generated_at=as_of,
        signal_score=score.signal_score,
        conviction=score.conviction,
        direction=score.direction,
        rationale_text=rationale_text,
        model_version=model_version,
    )
    db.add(recommendation)
    await db.flush()

    db.add_all(
        RecommendationSupportingTrade(recommendation_id=recommendation.id, canonical_trade_id=t.id)
        for t in trades
    )
    return recommendation


async def generate_recommendations(
    db: AsyncSession, as_of: datetime | None = None
) -> list[Recommendation]:
    """Score every ticker with recent tracked-politician activity and persist
    a `Recommendation` row per ticker.

    Run nightly, after the ingest workers have written that night's
    deduplicated trades to `canonical_trades`.
    """
    settings = get_settings()
    as_of = as_of or datetime.now(UTC)

    trades_by_ticker = await _load_recent_trades_by_ticker(db, as_of)

    recommendations: list[Recommendation] = []
    for ticker, trades in trades_by_ticker.items():
        scorable = [
            ScorableTrade(
                politician_id=t.politician_id,
                transaction_type=t.transaction_type,
                transaction_date=t.transaction_date,
                amount_mid=float(t.amount_mid),
            )
            for t in trades
        ]
        score = score_ticker(ticker, scorable, as_of)
        recommendation = await _persist_recommendation(
            db, score, trades, as_of, settings.recommendation_model
        )
        recommendations.append(recommendation)

    await db.commit()
    return recommendations
