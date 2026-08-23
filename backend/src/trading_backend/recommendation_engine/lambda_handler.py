import asyncio
from typing import Any

from trading_backend.db.session import get_sessionmaker
from trading_backend.recommendation_engine.engine import generate_recommendations


async def _run() -> int:
    async with get_sessionmaker()() as db:
        recommendations = await generate_recommendations(db)
    return len(recommendations)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """EventBridge Scheduler entrypoint, invoked nightly after the ingest
    workers finish (see infra/modules/eventbridge).
    """
    count = asyncio.run(_run())
    return {"recommendations_generated": count}
