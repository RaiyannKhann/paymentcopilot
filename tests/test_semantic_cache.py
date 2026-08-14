import asyncio
import time

from paymentcopilot.cache.semantic_cache import get_cached_answer, store_answer

_RESPONSE = {
    "answer": "Webhook signatures are verified using HMAC-SHA256.",
    "source_route": "uc1_docs",
    "grounding_refs": ["02-webhook-signatures.md — Verification"],
    "guardrail_status": "passed",
    "escalated": False,
}


def test_exact_duplicate_query_is_a_cache_hit(fake_redis):
    async def run():
        await store_answer("demo-merchant", "How do I verify a webhook signature?", _RESPONSE, False, fake_redis)
        return await get_cached_answer("demo-merchant", "How do I verify a webhook signature?", fake_redis)

    result = asyncio.run(run())
    assert result == _RESPONSE


def test_near_duplicate_paraphrase_is_a_cache_hit(fake_redis):
    async def run():
        await store_answer("demo-merchant", "How do I verify a webhook signature?", _RESPONSE, False, fake_redis)
        return await get_cached_answer("demo-merchant", "How can I verify a webhook signature?", fake_redis)

    result = asyncio.run(run())
    assert result == _RESPONSE


def test_unrelated_query_returns_none(fake_redis):
    async def run():
        await store_answer("demo-merchant", "How do I verify a webhook signature?", _RESPONSE, False, fake_redis)
        return await get_cached_answer("demo-merchant", "Why did txn_88213 fail?", fake_redis)

    assert asyncio.run(run()) is None


def test_escalated_results_are_never_stored(fake_redis):
    async def run():
        await store_answer("demo-merchant", "How do I verify a webhook signature?", _RESPONSE, True, fake_redis)
        return await get_cached_answer("demo-merchant", "How do I verify a webhook signature?", fake_redis)

    assert asyncio.run(run()) is None


def test_tenant_isolation(fake_redis):
    async def run():
        await store_answer("demo-merchant", "How do I verify a webhook signature?", _RESPONSE, False, fake_redis)
        return await get_cached_answer("acme-retail", "How do I verify a webhook signature?", fake_redis)

    assert asyncio.run(run()) is None


def test_cap_eviction_keeps_only_newest_entries(fake_redis):
    from paymentcopilot import config

    async def run():
        for i in range(config.settings.semantic_cache_max_entries_per_tenant + 1):
            await store_answer("demo-merchant", f"unrelated distinct query number {i}", _RESPONSE, False, fake_redis)
        return await fake_redis.llen("semcache:demo-merchant")

    length = asyncio.run(run())
    assert length == config.settings.semantic_cache_max_entries_per_tenant


def test_lazy_ttl_expiry_skips_stale_entries(fake_redis):
    import json

    from paymentcopilot.embeddings.embedder import embed_one

    async def run():
        stale_entry = {
            "query": "How do I verify a webhook signature?",
            "embedding": embed_one("How do I verify a webhook signature?"),
            "response": _RESPONSE,
            "created_at": time.time() - 999999,
        }
        await fake_redis.lpush("semcache:demo-merchant", json.dumps(stale_entry))
        return await get_cached_answer("demo-merchant", "How do I verify a webhook signature?", fake_redis)

    assert asyncio.run(run()) is None
