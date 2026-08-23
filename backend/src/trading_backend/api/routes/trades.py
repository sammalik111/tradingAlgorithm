import uuid

from fastapi import APIRouter, Query
from sqlalchemy import select

from trading_backend.api.deps import DbSession
from trading_backend.models.canonical_trade import CanonicalTrade
from trading_backend.schemas.trade import CanonicalTradeOut

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("", response_model=list[CanonicalTradeOut])
async def list_trades(
    db: DbSession,
    ticker: str | None = None,
    politician_id: uuid.UUID | None = None,
    limit: int = Query(default=50, le=200),
) -> list[CanonicalTrade]:
    stmt = select(CanonicalTrade)
    if ticker:
        stmt = stmt.where(CanonicalTrade.ticker == ticker.upper())
    if politician_id:
        stmt = stmt.where(CanonicalTrade.politician_id == politician_id)
    stmt = stmt.order_by(CanonicalTrade.transaction_date.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
