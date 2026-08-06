"""Redis client setup using redis.asyncio."""

import logging
import redis.asyncio as redis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

_redis_client: Redis | None = None


async def connect_redis(redis_url: str) -> None:
    global _redis_client
    _redis_client = redis.from_url(redis_url, decode_responses=True)
    logger.info("Connected to Redis at %s", redis_url)


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Closed Redis connection.")


def get_redis_client() -> Redis:
    if _redis_client is None:
        raise RuntimeError("Redis client is not initialized.")
    return _redis_client
