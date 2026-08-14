import asyncio

from paymentcopilot import config
from paymentcopilot.cache.session_memory import append_turn, get_session_history


def test_turns_are_read_back_in_insertion_order(fake_redis):
    async def run():
        await append_turn("demo-merchant", "sess-1", {"query": "first"}, fake_redis)
        await append_turn("demo-merchant", "sess-1", {"query": "second"}, fake_redis)
        return await get_session_history("demo-merchant", "sess-1", fake_redis)

    history = asyncio.run(run())
    assert [turn["query"] for turn in history] == ["first", "second"]


def test_ttl_is_set_on_write(fake_redis):
    async def run():
        await append_turn("demo-merchant", "sess-1", {"query": "first"}, fake_redis)
        return await fake_redis.ttl("session:demo-merchant:sess-1")

    ttl = asyncio.run(run())
    assert 0 < ttl <= config.settings.session_ttl_seconds


def test_tenant_and_session_keys_are_isolated(fake_redis):
    async def run():
        await append_turn("demo-merchant", "sess-1", {"query": "demo turn"}, fake_redis)
        await append_turn("acme-retail", "sess-1", {"query": "acme turn"}, fake_redis)
        demo_history = await get_session_history("demo-merchant", "sess-1", fake_redis)
        other_session_history = await get_session_history("demo-merchant", "sess-2", fake_redis)
        return demo_history, other_session_history

    demo_history, other_session_history = asyncio.run(run())
    assert len(demo_history) == 1
    assert demo_history[0]["query"] == "demo turn"
    assert other_session_history == []
