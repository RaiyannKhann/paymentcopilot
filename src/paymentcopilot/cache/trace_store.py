"""Request-trace persistence (Phase 7 frontend, `frontendspec.md` §3/§4).

Stores the sanitized trace object built in api/app.py per request_id, TTL'd so the
frontend's Request Trace page can be reloaded/shared for a short window without the
frontend having to hold trace state in memory. Same short-lived Redis-entry shape as
cache/session_memory.py - no new storage engine introduced for this.
"""

import json

import redis.asyncio as redis

from paymentcopilot.config import settings

_KEY_PREFIX = "trace"


def _key(request_id: str) -> str:
    return f"{_KEY_PREFIX}:{request_id}"


async def store_trace(request_id: str, trace: dict, redis_client: redis.Redis) -> None:
    await redis_client.set(_key(request_id), json.dumps(trace), ex=settings.trace_ttl_seconds)


async def get_trace(request_id: str, redis_client: redis.Redis) -> dict | None:
    raw = await redis_client.get(_key(request_id))
    return json.loads(raw) if raw is not None else None
