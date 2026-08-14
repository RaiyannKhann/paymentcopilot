import json

from paymentcopilot.evals.golden_set import GoldenItem
from paymentcopilot.evals.report import build_report
from paymentcopilot.evals.runner import EvalRecord


def _record(id, category, expected_route, route, expected_escalated, escalated, answer="the answer"):
    item = GoldenItem(
        id=id,
        category=category,
        query="q",
        merchant_id="demo-merchant",
        expected_route=expected_route,
        expected_escalated=expected_escalated,
    )
    return EvalRecord(item=item, route=route, escalated=escalated, guardrail_status="passed", answer=answer)


_RECORDS = [
    _record("a", "uc1_happy", "uc1_docs", "uc1_docs", False, False),
    _record("b", "refusal_out_of_scope", "out_of_scope", "uc1_docs", True, False),
]


def test_build_report_markdown_has_expected_sections():
    markdown, _ = build_report("eval-test-run", "data/eval/golden_set.jsonl", _RECORDS, skip_ragas=True)
    assert "# Eval run eval-test-run" in markdown
    assert "## Refusal correctness" in markdown
    assert "## Routing accuracy" in markdown
    assert "## Failing items" in markdown
    assert "b" in markdown  # the failing item's id should surface


def test_build_report_json_round_trips_with_expected_keys():
    _, report = build_report("eval-test-run", "data/eval/golden_set.jsonl", _RECORDS, skip_ragas=True)
    round_tripped = json.loads(json.dumps(report, default=str))

    for key in (
        "run_id",
        "golden_set_size",
        "refusal_correctness",
        "refusal_correctness_by_category",
        "strict_refusal_diagnostics",
        "routing_accuracy",
        "failing_items",
        "records",
    ):
        assert key in round_tripped

    assert round_tripped["golden_set_size"] == 2
    assert round_tripped["routing_accuracy"]["correct"] == 1
    assert len(round_tripped["failing_items"]) == 1
    assert round_tripped["failing_items"][0]["id"] == "b"


def test_build_report_includes_ragas_section_when_provided():
    markdown, report = build_report(
        "eval-test-run", "data/eval/golden_set.jsonl", _RECORDS, skip_ragas=False,
        ragas_scores={"faithfulness": 0.9},
    )
    assert "## RAGAS scores" in markdown
    assert report["ragas"] == {"faithfulness": 0.9}
