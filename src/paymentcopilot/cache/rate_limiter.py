"""Per-tenant rate limiting (FR21): fixed-window counter in Redis.

Fixed-window INCR+EXPIRE is the simplest correct approach at this project's scale.
Documented tradeoff: a burst straddling a window boundary can admit up to ~2x
rate_limit_max_requests in a short span - not worth sliding-window/token-bucket
complexity here.
"""

from dataclasses import dataclass

import redis.asyncio as redis

from paymentcopilot.config import settings

_KEY_PREFIX = "ratelimit"


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after_seconds: int


async def check_and_increment(merchant_id: str, redis_client: redis.Redis) -> RateLimitResult:
    key = f"{_KEY_PREFIX}:{merchant_id}"

    count = await redis_client.incr(key)
    if count == 1:
        await redis_client.expire(key, settings.rate_limit_window_seconds)

    ttl = await redis_client.ttl(key)
    retry_after = ttl if ttl > 0 else settings.rate_limit_window_seconds

    return RateLimitResult(
        allowed=count <= settings.rate_limit_max_requests,
        remaining=max(0, settings.rate_limit_max_requests - count),
        retry_after_seconds=retry_after,
    )
