import fakeredis.aioredis
import pytest

from paymentcopilot.guardrails.injection_ml import MlInjectionResult


@pytest.fixture
def fake_redis():
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture(autouse=True)
def _stub_ml_injection_scanner(monkeypatch):
    """Default the ML injection fallback (guardrails/injection_ml.py) to "not matched" so
    the suite doesn't load the real DeBERTa classifier — and doesn't need network access
    to fetch its weights — on every query. Tests exercising the ML path patch
    `paymentcopilot.graph.router.scan_injection_ml` directly, which overrides this stub.
    """
    monkeypatch.setattr(
        "paymentcopilot.graph.router.scan_injection_ml",
        lambda text: MlInjectionResult(matched=False),
    )
