from fastapi import APIRouter, Query
from sqlalchemy import select

from trading_backend.api.deps import DbSession
from trading_backend.cache.redis_client import get_cached_json, set_cached_json
from trading_backend.models.recommendation import Recommendation
from trading_backend.schemas.recommendation import RecommendationOut

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
