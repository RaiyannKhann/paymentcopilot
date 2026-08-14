from paymentcopilot.evals.golden_set import GoldenItem
from paymentcopilot.evals.refusal_metric import (
    compute_refusal_correctness,
    compute_strict_refusal_correctness,
)
from paymentcopilot.evals.runner import EvalRecord


def _item(id, expected_escalated, expected_guardrail_category=None):
    return GoldenItem(
        id=id,
        category="uc1_happy",
        query="q",
        merchant_id="demo-merchant",
        expected_route="uc1_docs",
        expected_escalated=expected_escalated,
        expected_guardrail_category=expected_guardrail_category,
    )


def _record(id, escalated, expected_escalated, guardrail_status="passed", error=None, expected_guardrail_category=None):
    return EvalRecord(
        item=_item(id, expected_escalated, expected_guardrail_category),
        route="uc1_docs",
        escalated=escalated,
        guardrail_status=guardrail_status,
        answer="answer",
        error=error,
    )


def test_all_true_positive():
    records = [_record("a", True, True), _record("b", True, True)]
    m = compute_refusal_correctness(records)
    assert (m.tp, m.fp, m.fn, m.tn) == (2, 0, 0, 0)
    assert m.precision == 1.0
    assert m.recall == 1.0
    assert m.f1 == 1.0
    assert m.accuracy == 1.0


def test_over_refusal_hurts_precision_not_recall():
    records = [
        _record("a", True, True),  # TP
        _record("b", True, False),  # FP (over-refusal)
    ]
    m = compute_refusal_correctness(records)
    assert (m.tp, m.fp, m.fn, m.tn) == (1, 1, 0, 0)
    assert m.precision == 0.5
    assert m.recall == 1.0


def test_under_refusal_hurts_recall():
    records = [
        _record("a", False, True),  # FN (under-refusal)
        _record("b", False, False),  # TN
    ]
    m = compute_refusal_correctness(records)
    assert (m.tp, m.fp, m.fn, m.tn) == (0, 0, 1, 1)
    assert m.recall == 0.0
    assert m.accuracy == 0.5


def test_no_positives_predicted_does_not_divide_by_zero():
    records = [_record("a", False, False)]
    m = compute_refusal_correctness(records)
    assert m.precision == 0.0
    assert m.recall == 0.0
    assert m.f1 == 0.0
    assert m.accuracy == 1.0


def test_errored_records_excluded_from_scoring():
    records = [_record("a", True, True), _record("b", None, True, error="boom")]
    m = compute_refusal_correctness(records)
    assert (m.tp, m.fp, m.fn, m.tn) == (1, 0, 0, 0)


def test_strict_diagnostic_matches_substring_in_composed_status():
    records = [
        _record(
            "a", True, True,
            guardrail_status="input_redacted:pii,output_redacted:pii",
            expected_guardrail_category="output_redacted:pii",
        ),
        _record(
            "b", True, True,
            guardrail_status="input_blocked:injection:instruction_override",
            expected_guardrail_category="input_blocked:injection:role_play_jailbreak",
        ),
    ]
    diag = compute_strict_refusal_correctness(records)
    assert diag.checked == 2
    assert diag.exact_match == 1
    assert diag.exact_match_rate == 0.5


def test_strict_diagnostic_ignores_items_without_expected_category():
    records = [_record("a", True, True)]
    diag = compute_strict_refusal_correctness(records)
    assert diag.checked == 0
    assert diag.exact_match_rate == 0.0
