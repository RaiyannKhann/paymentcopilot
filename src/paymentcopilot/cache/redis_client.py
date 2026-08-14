"""Shared async Redis client (cache, rate limiter, session memory)."""

from functools import lru_cache

import redis.asyncio as redis

from paymentcopilot.config import settings


@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)
