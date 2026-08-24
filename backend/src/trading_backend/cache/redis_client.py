import json
import logging
from functools import lru_cache
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from trading_backend.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_redis() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


# The cache is a pure read-through optimization backed by the DB as the
# source of truth (see recommendations.py), so any Redis failure here
# (connectivity, TLS handshake, timeout) should degrade to a cache miss
# instead of failing the request.
async def get_cached_json(key: str) -> Any | None:
    try:
        raw = await get_redis().get(key)
    except RedisError:
        logger.warning("Redis GET failed for key %s; falling back to DB", key, exc_info=True)
        return None
    return json.loads(raw) if raw is not None else None


async def set_cached_json(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    settings = get_settings()
    ttl = ttl_seconds or settings.redis_cache_ttl_seconds
    try:
        await get_redis().set(key, json.dumps(value), ex=ttl)
    except RedisError:
        logger.warning(
            "Redis SET failed for key %s; continuing without caching", key, exc_info=True
        )
