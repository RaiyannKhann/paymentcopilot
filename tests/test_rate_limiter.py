import asyncio

from paymentcopilot import config
from paymentcopilot.cache.rate_limiter import check_and_increment


def test_requests_up_to_the_limit_are_allowed(fake_redis):
    async def run():
        results = []
        for _ in range(config.settings.rate_limit_max_requests):
            results.append(await check_and_increment("demo-merchant", fake_redis))
        return results

    results = asyncio.run(run())
    assert all(r.allowed for r in results)


def test_request_over_the_limit_is_rejected(fake_redis):
    async def run():
        for _ in range(config.settings.rate_limit_max_requests):
            await check_and_increment("demo-merchant", fake_redis)
        return await check_and_increment("demo-merchant", fake_redis)

    result = asyncio.run(run())
    assert not result.allowed
    assert result.remaining == 0
    assert result.retry_after_seconds > 0


def test_tenants_have_independent_counters(fake_redis):
    async def run():
        for _ in range(config.settings.rate_limit_max_requests):
            await check_and_increment("demo-merchant", fake_redis)
        return await check_and_increment("acme-retail", fake_redis)

    result = asyncio.run(run())
    assert result.allowed
