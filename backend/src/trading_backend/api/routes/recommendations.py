import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from trading_backend.algorithms.clustering import consensus, consensus_multiplier
from trading_backend.algorithms.scoring import (
    ScorableTrade,
    recency_weight,
    size_weight,
    trade_signal_strength,
)
from trading_backend.api.deps import DbSession
from trading_backend.cache.redis_client import get_cached_json, set_cached_json
from trading_backend.models.canonical_trade import CanonicalTrade
from trading_backend.models.enums import TransactionType
from trading_backend.models.politician import Politician
from trading_backend.models.recommendation import Recommendation, RecommendationSupportingTrade
from trading_backend.models.simulated_order import SimulatedOrder
from trading_backend.schemas.order import SimulatedOrderCreate, SimulatedOrderOut
from trading_backend.schemas.recommendation import (
    RecommendationDetail,
    RecommendationOut,
    ScoringBreakdown,
    ScoringBreakdownTrade,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

_LATEST_CACHE_KEY = "recommendations:latest"


@router.get("", response_model=list[RecommendationOut])
async def list_recommendations(
    db: DbSession,
    ticker: str | None = None,
    limit: int = Query(default=25, le=100),
) -> list[Recommendation]:
    if ticker is None:
        cached = await get_cached_json(_LATEST_CACHE_KEY)
        if cached is not None:
            return [RecommendationOut.model_validate(item) for item in cached]

    stmt = select(Recommendation)
    if ticker:
        stmt = stmt.where(Recommendation.ticker == ticker.upper())
    stmt = stmt.order_by(Recommendation.generated_at.desc()).limit(limit)
    result = await db.execute(stmt)
    recommendations = list(result.scalars().all())

    if ticker is None:
        payload = [
            RecommendationOut.model_validate(r).model_dump(mode="json") for r in recommendations
        ]
        await set_cached_json(_LATEST_CACHE_KEY, payload)

    return recommendations


@router.get("/{recommendation_id}", response_model=RecommendationDetail)
async def get_recommendation_detail(
    recommendation_id: uuid.UUID, db: DbSession
) -> RecommendationDetail:
    recommendation = await db.get(Recommendation, recommendation_id)
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    links_stmt = select(RecommendationSupportingTrade).where(
        RecommendationSupportingTrade.recommendation_id == recommendation_id
    )
    links_result = await db.execute(links_stmt)
    canonical_trade_ids = [link.canonical_trade_id for link in links_result.scalars().all()]

    trades: list[CanonicalTrade] = []
    if canonical_trade_ids:
        trades_stmt = select(CanonicalTrade).where(CanonicalTrade.id.in_(canonical_trade_ids))
        trades_result = await db.execute(trades_stmt)
        trades = list(trades_result.scalars().all())

    politicians: dict[uuid.UUID, Politician] = {}
    if trades:
        politicians_stmt = select(Politician).where(
            Politician.id.in_({t.politician_id for t in trades})
        )
        politicians_result = await db.execute(politicians_stmt)
        politicians = {p.id: p for p in politicians_result.scalars().all()}

    # Nothing about the scoring breakdown is persisted (see engine.py) --
    # recompute it here from the same supporting trades using the exact
    # pure functions the recommendation engine called at generation time.
    as_of_date: date = recommendation.generated_at.date()
    politician_ids_by_direction: dict[TransactionType, set] = {}
    breakdown_trades: list[ScoringBreakdownTrade] = []
    raw_total = 0.0
    for trade in trades:
        scorable = ScorableTrade(
            politician_id=trade.politician_id,
            transaction_type=trade.transaction_type,
            transaction_date=trade.transaction_date,
            amount_mid=float(trade.amount_mid),
        )
        contribution = trade_signal_strength(scorable, as_of_date)
        raw_total += contribution
        politician_ids_by_direction.setdefault(trade.transaction_type, set()).add(
            trade.politician_id
        )

        politician = politicians.get(trade.politician_id)
        breakdown_trades.append(
            ScoringBreakdownTrade(
                canonical_trade_id=trade.id,
                politician_name=politician.full_name if politician else "Unknown",
                transaction_type=trade.transaction_type,
                transaction_date=trade.transaction_date,
                amount_mid=float(trade.amount_mid),
                recency_weight=recency_weight(trade.transaction_date, as_of_date),
                size_weight=size_weight(float(trade.amount_mid)),
                signal_contribution=contribution,
            )
        )

    consensus_result = consensus(politician_ids_by_direction)

    orders_stmt = (
        select(SimulatedOrder)
        .where(SimulatedOrder.recommendation_id == recommendation_id)
        .order_by(SimulatedOrder.created_at.desc())
    )
    orders_result = await db.execute(orders_stmt)
    orders = list(orders_result.scalars().all())

    return RecommendationDetail(
        **RecommendationOut.model_validate(recommendation).model_dump(),
        scoring_breakdown=ScoringBreakdown(
            raw_total=raw_total,
            agreeing_politicians=consensus_result.agreeing_politicians,
            total_politicians=consensus_result.total_politicians,
            consensus_multiplier=consensus_multiplier(consensus_result.agreeing_politicians),
        ),
        supporting_trades=breakdown_trades,
        simulated_orders=[SimulatedOrderOut.model_validate(o) for o in orders],
    )


@router.post(
    "/{recommendation_id}/simulated-orders",
    response_model=SimulatedOrderOut,
    status_code=201,
)
async def create_simulated_order(
    recommendation_id: uuid.UUID, payload: SimulatedOrderCreate, db: DbSession
) -> SimulatedOrder:
    """Logs a paper-trade entry against a recommendation. Never calls a real
    brokerage -- see integrations/robinhood/client.py.
    """
    recommendation = await db.get(Recommendation, recommendation_id)
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    order = SimulatedOrder(
        recommendation_id=recommendation.id,
        ticker=recommendation.ticker,
        side=payload.side,
        quantity=payload.quantity,
        price=payload.price,
        notional_value=payload.quantity * payload.price,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order
