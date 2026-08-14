from dataclasses import replace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from paymentcopilot.api.app import app
from paymentcopilot.api.dependencies import get_redis
from paymentcopilot.cache.rate_limiter import check_and_increment
from paymentcopilot.cache.semantic_cache import store_answer
from paymentcopilot.config import settings as real_settings
from paymentcopilot.models import Chunk, RetrievedChunk, RouterResult

_GOOD_CHUNK = RetrievedChunk(
    chunk=Chunk(
        id="c1",
        text="Webhook signatures are verified using HMAC-SHA256.",
        source_doc="02-webhook-signatures.md",
        section="Verification",
        chunk_index=0,
        doc_type="docs",
    ),
    score=0.90,
)

_ROUTER_RESULT = RouterResult(
    query="How do I verify a webhook signature?",
    route="uc1_docs",
    route_reason="payment domain keyword match",
    answer="Webhook signatures are verified using HMAC-SHA256.",
    escalated=False,
    retrieved_chunks=[_GOOD_CHUNK],
    guardrail_status="passed",
)


@pytest.fixture
def client(fake_redis):
    async def override_get_redis():
        return fake_redis

    app.dependency_overrides[get_redis] = override_get_redis
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_query_translates_tenant_id_to_merchant_id(client):
    with patch("paymentcopilot.api.app.run_query", return_value=_ROUTER_RESULT) as mock_run_query:
        response = client.post(
            "/query",
            json={"tenant_id": "demo-merchant", "query": "How do I verify a webhook signature?"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == _ROUTER_RESULT.answer
    assert body["source_route"] == "uc1_docs"
    assert body["escalated"] is False
    assert body["grounding_refs"] == ["02-webhook-signatures.md — Verification"]
    assert body["session_id"]
    mock_run_query.assert_called_once_with(
        "How do I verify a webhook signature?", merchant_id="demo-merchant"
    )


def test_query_over_rate_limit_returns_429(client, fake_redis):
    import asyncio

    async def exhaust():
        for _ in range(real_settings.rate_limit_max_requests):
            await check_and_increment("demo-merchant", fake_redis)

    asyncio.run(exhaust())

    with patch("paymentcopilot.api.app.run_query", return_value=_ROUTER_RESULT) as mock_run_query:
        response = client.post(
            "/query",
            json={"tenant_id": "demo-merchant", "query": "How do I verify a webhook signature?"},
        )

    assert response.status_code == 429
    assert "Retry-After" in response.headers
    mock_run_query.assert_not_called()


def test_query_cache_hit_skips_run_query(client, fake_redis):
    import asyncio

    cached_response = {
        "answer": "Cached: verify via HMAC-SHA256.",
        "source_route": "uc1_docs",
        "grounding_refs": ["02-webhook-signatures.md — Verification"],
        "guardrail_status": "passed",
        "escalated": False,
    }
    asyncio.run(
        store_answer(
            "demo-merchant",
            "How do I verify a webhook signature?",
            cached_response,
            False,
            fake_redis,
        )
    )

    with patch("paymentcopilot.api.app.run_query") as mock_run_query:
        response = client.post(
            "/query",
            json={"tenant_id": "demo-merchant", "query": "How do I verify a webhook signature?"},
        )

    assert response.status_code == 200
    assert response.json()["answer"] == cached_response["answer"]
    mock_run_query.assert_not_called()


def test_health_returns_200_when_dependencies_reachable(client):
    with patch("paymentcopilot.api.app._check_postgres", return_value=None):
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["redis"] == "ok"
    assert body["checks"]["postgres"] == "ok"


def test_health_returns_503_when_postgres_unreachable(client):
    with patch("paymentcopilot.api.app._check_postgres", side_effect=RuntimeError("down")):
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["checks"]["postgres"] == "unreachable"


def test_evals_run_returns_404_when_disabled(client):
    response = client.post("/evals/run", json={"skip_ragas": True})

    assert response.status_code == 404


def test_evals_run_returns_200_when_enabled(client, tmp_path):
    enabled_settings = replace(real_settings, enable_evals_endpoint=True)
    fake_report = {"run_id": "eval-test", "failing_items": []}

    with (
        patch("paymentcopilot.api.app.settings", enabled_settings),
        patch("paymentcopilot.api.app.load_golden_set", return_value=[]),
        patch("paymentcopilot.api.app.run_golden_set", return_value=[]),
        patch("paymentcopilot.api.app.build_report", return_value=("md", fake_report)),
        patch(
            "paymentcopilot.api.app.write_report",
            return_value=(tmp_path / "a.md", tmp_path / "a.json"),
        ),
    ):
        response = client.post("/evals/run", json={"skip_ragas": True})

    assert response.status_code == 200
    assert response.json() == fake_report
