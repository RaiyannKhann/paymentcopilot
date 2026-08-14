from paymentcopilot.evals.golden_set import GoldenItem
from paymentcopilot.evals.ragas_eval import run_ragas
from paymentcopilot.evals.runner import EvalRecord


def test_run_ragas_returns_none_with_no_eligible_items_and_makes_no_network_call():
    item = GoldenItem(
        id="a",
        category="refusal_out_of_scope",
        query="q",
        merchant_id="demo-merchant",
        expected_route="out_of_scope",
        expected_escalated=True,
        ragas_eligible=False,
    )
    record = EvalRecord(item=item, route="out_of_scope", escalated=True, answer="refused")
    assert run_ragas([record]) is None
