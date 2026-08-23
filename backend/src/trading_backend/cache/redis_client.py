import json
from functools import lru_cache
from typing import Any

from redis.asyncio import Redis

from trading_backend.config import get_settings


@lru_cache
def get_redis() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def get_cached_json(key: str) -> Any | None:
    raw = await get_redis().get(key)
    return json.loads(raw) if raw is not None else None


async def set_cached_json(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    settings = get_settings()
    ttl = ttl_seconds or settings.redis_cache_ttl_seconds
    await get_redis().set(key, json.dumps(value), ex=ttl)
