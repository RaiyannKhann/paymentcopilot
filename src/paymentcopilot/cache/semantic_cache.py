"""Semantic-similarity cache (FR20): short-circuits repeated/near-duplicate queries.

Stores the API response payload (not RouterResult/Chunk/Transaction) so this module
stays decoupled from graph internals. Never caches escalated/refused answers - a
refusal shouldn't be served as a stable cached answer once retrieval data or
transaction state changes. Tenant isolation is structural: one Redis list per
merchant_id, so a lookup can never scan another tenant's entries.
"""

import json
import time

import numpy as np
import redis.asyncio as redis

from paymentcopilot.config import settings
from paymentcopilot.embeddings.embedder import embed_one

_KEY_PREFIX = "semcache"


def _key(merchant_id: str) -> str:
    return f"{_KEY_PREFIX}:{merchant_id}"


async def get_cached_answer(
    merchant_id: str, query: str, redis_client: redis.Redis
) -> dict | None:
    """Return a cached response dict for a near-duplicate query, or None on a miss.

    Scans newest-first; entries older than semantic_cache_ttl_seconds are skipped
    (lazy expiry) rather than trusting the key's own backstop TTL alone, since a
    heavily-hit tenant's key would otherwise never let individual stale entries expire.
    """
    embedding = embed_one(query)
    raw_entries = await redis_client.lrange(_key(merchant_id), 0, -1)
    now = time.time()

    for raw in raw_entries:
        entry = json.loads(raw)
        if now - entry["created_at"] > settings.semantic_cache_ttl_seconds:
            continue
        similarity = float(np.dot(embedding, entry["embedding"]))
        if similarity >= settings.semantic_cache_similarity_threshold:
            return entry["response"]

    return None


async def store_answer(
    merchant_id: str,
    query: str,
    response: dict,
    escalated: bool,
    redis_client: redis.Redis,
) -> None:
    """Cache a response, unless it was an escalation/refusal."""
    if escalated:
        return

    key = _key(merchant_id)
    entry = {
        "query": query,
        "embedding": embed_one(query),
        "response": response,
        "created_at": time.time(),
    }

    async with redis_client.pipeline() as pipe:
        pipe.lpush(key, json.dumps(entry))
        pipe.ltrim(key, 0, settings.semantic_cache_max_entries_per_tenant - 1)
        pipe.expire(key, settings.semantic_cache_ttl_seconds * 2)
        await pipe.execute()
