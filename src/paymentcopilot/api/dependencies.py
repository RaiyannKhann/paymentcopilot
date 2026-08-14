"""FastAPI dependency wiring: shared Redis client, per-tenant rate limiting."""

import redis.asyncio as redis
from fastapi import Depends, HTTPException

from paymentcopilot.api.schemas import QueryRequest
from paymentcopilot.cache.rate_limiter import check_and_increment
from paymentcopilot.cache.redis_client import get_redis_client


async def get_redis() -> redis.Redis:
    return get_redis_client()


async def rate_limit_dependency(
    payload: QueryRequest, redis_client: redis.Redis = Depends(get_redis)
) -> None:
    """Runs before the semantic cache lookup and before run_query() - even a cache
    lookup costs a local embed + Redis round trip, so rate limiting must gate all
    incoming requests, not just LLM-invoking ones."""
    result = await check_and_increment(payload.tenant_id, redis_client)
    if not result.allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "detail": (
                    f"Rate limit exceeded for tenant '{payload.tenant_id}'. "
                    f"Try again in {result.retry_after_seconds}s."
                ),
                "retry_after_seconds": result.retry_after_seconds,
            },
            headers={"Retry-After": str(result.retry_after_seconds)},
        )
