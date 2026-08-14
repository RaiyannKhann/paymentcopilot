from unittest.mock import patch

from paymentcopilot.evals.golden_set import GoldenItem
from paymentcopilot.evals.runner import run_golden_set
from paymentcopilot.models import RouterResult

_ITEM_A = GoldenItem(
    id="a",
    category="uc1_happy",
    query="How do I verify a webhook signature?",
    merchant_id="demo-merchant",
    expected_route="uc1_docs",
    expected_escalated=False,
)
_ITEM_B = GoldenItem(
    id="b",
    category="refusal_out_of_scope",
    query="What's the weather?",
    merchant_id="demo-merchant",
    expected_route="out_of_scope",
    expected_escalated=True,
)


def _router_result(query):
    return RouterResult(
        query=query,
        route="uc1_docs",
        route_reason="matched",
        answer="the answer",
        escalated=False,
        guardrail_status="passed",
    )


def test_run_golden_set_maps_results_correctly():
    with patch("paymentcopilot.evals.runner.run_query", side_effect=lambda query, merchant_id: _router_result(query)):
        records = run_golden_set([_ITEM_A])

    assert len(records) == 1
    r = records[0]
    assert r.item is _ITEM_A
    assert r.route == "uc1_docs"
    assert r.answer == "the answer"
    assert r.error is None
    assert r.latency_s >= 0


def test_run_golden_set_isolates_per_item_exceptions():
    def side_effect(query, merchant_id):
        if query == _ITEM_B.query:
            raise RuntimeError("boom")
        return _router_result(query)

    with patch("paymentcopilot.evals.runner.run_query", side_effect=side_effect):
        records = run_golden_set([_ITEM_A, _ITEM_B])

    assert len(records) == 2
    assert records[0].error is None
    assert records[1].error == "boom"
    assert records[1].route is None
