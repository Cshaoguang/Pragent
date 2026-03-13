from redis.asyncio import Redis

from backend.config.settings import get_settings

_redis: Redis | None = None


async def init_redis() -> None:
    global _redis
    if _redis is not None:
        return
    _redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    await _redis.ping()


def get_redis() -> Redis:
    if _redis is None:
        raise RuntimeError("Redis is not initialized")
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
