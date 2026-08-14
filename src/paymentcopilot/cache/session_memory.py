"""Short-term session memory (FR22): stores each turn with a TTL.

Storage/plumbing only for now - history is persisted per session_id but not fed
into generation this phase. Turns are sourced from the post-guardrail RouterResult
(redacted query, already-checked answer), so no raw/unredacted text is ever
persisted here.
"""

import json

import redis.asyncio as redis

from paymentcopilot.config import settings

_KEY_PREFIX = "session"


def _key(merchant_id: str, session_id: str) -> str:
    return f"{_KEY_PREFIX}:{merchant_id}:{session_id}"


async def append_turn(
    merchant_id: str, session_id: str, turn: dict, redis_client: redis.Redis
) -> None:
    key = _key(merchant_id, session_id)
    async with redis_client.pipeline() as pipe:
        pipe.rpush(key, json.dumps(turn))
        pipe.expire(key, settings.session_ttl_seconds)
        await pipe.execute()


async def get_session_history(
    merchant_id: str, session_id: str, redis_client: redis.Redis
) -> list[dict]:
    raw_entries = await redis_client.lrange(_key(merchant_id, session_id), 0, -1)
    return [json.loads(raw) for raw in raw_entries]
