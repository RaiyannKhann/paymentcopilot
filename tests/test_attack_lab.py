from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from paymentcopilot.api.app import app
from paymentcopilot.api.dependencies import get_redis


@pytest.fixture
def client(fake_redis):
    async def override_get_redis():
        return fake_redis

    app.dependency_overrides[get_redis] = override_get_redis
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_cases_exposes_no_payloads(client):
    response = client.get("/attack-lab/cases")

    assert response.status_code == 200
    cases = response.json()["cases"]
    ids = {c["attack_id"] for c in cases}
    assert ids == {
        "instruction_override",
        "jailbreak",
        "cross_tenant",
        "structured_field",
        "pii_query",
        "pii_structured_field",
        "policy_gap",
    }
    for case in cases:
        assert "payload" not in case


@pytest.mark.parametrize(
    "attack_id,expected_category",
    [
        ("instruction_override", "instruction_override"),
        ("jailbreak", "jailbreak"),
        ("cross_tenant", "cross_tenant_exfiltration"),
        ("structured_field", "structured_field_injection"),
    ],
)
def test_injection_cases_block_without_calling_claude(client, attack_id, expected_category):
    with (
        patch("paymentcopilot.graph.router.generate_answer") as mock_generate,
        patch("paymentcopilot.generation.generator.call_claude") as mock_claude,
    ):
        response = client.post("/attack-lab/run", json={"attack_id": attack_id})

    assert response.status_code == 200
    body = response.json()
    assert body["blocked"] is True
    assert body["guardrail"] == "injection"
    assert body["mode"] == "live"
    assert "No Claude call" in body["pipeline"][-1]
    mock_generate.assert_not_called()
    mock_claude.assert_not_called()


@pytest.mark.parametrize("attack_id", ["pii_query", "pii_structured_field"])
def test_pii_cases_redact_and_never_expose_raw_value(client, attack_id):
    with patch("paymentcopilot.generation.generator.call_claude") as mock_claude:
        response = client.post("/attack-lab/run", json={"attack_id": attack_id})

    assert response.status_code == 200
    body = response.json()
    assert body["blocked"] is True
    assert body["guardrail"] == "pii"
    assert "CREDIT_CARD" in body["entities_found"]
    assert "4111111111111111" not in body["detail"]
    assert "4111111111111111" not in body["action"]
    mock_claude.assert_not_called()


def test_policy_gap_is_recorded_not_live(client):
    with patch("paymentcopilot.generation.generator.call_claude") as mock_claude:
        response = client.post("/attack-lab/run", json={"attack_id": "policy_gap"})

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "recorded"
    assert body["blocked"] is True
    mock_claude.assert_not_called()


def test_unknown_attack_id_returns_404(client):
    response = client.post("/attack-lab/run", json={"attack_id": "not-a-real-case"})

    assert response.status_code == 404


def test_attack_lab_rate_limited_per_client(client):
    from paymentcopilot.config import settings as real_settings

    for _ in range(real_settings.rate_limit_max_requests):
        client.post("/attack-lab/run", json={"attack_id": "jailbreak"})

    response = client.post("/attack-lab/run", json={"attack_id": "jailbreak"})

    assert response.status_code == 429
    assert "Retry-After" in response.headers
