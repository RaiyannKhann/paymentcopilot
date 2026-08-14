from paymentcopilot.evals.golden_set import GoldenItem
from paymentcopilot.evals.routing_metric import compute_routing_accuracy
from paymentcopilot.evals.runner import EvalRecord


def _record(id, expected_route, actual_route, error=None):
    item = GoldenItem(
        id=id,
        category="uc1_happy",
        query="q",
        merchant_id="demo-merchant",
        expected_route=expected_route,
        expected_escalated=False,
    )
    return EvalRecord(item=item, route=actual_route, escalated=False, error=error)


def test_all_correct():
    records = [_record("a", "uc1_docs", "uc1_docs"), _record("b", "uc3_policy", "uc3_policy")]
    m = compute_routing_accuracy(records)
    assert m.correct == 2
    assert m.total == 2
    assert m.accuracy == 1.0


def test_misroute_lowers_accuracy_and_appears_in_confusion_matrix():
    records = [_record("a", "uc3_policy", "uc1_docs")]
    m = compute_routing_accuracy(records)
    assert m.correct == 0
    assert m.accuracy == 0.0
    assert m.confusion_matrix == {"uc3_policy->uc1_docs": 1}


def test_errored_records_excluded():
    records = [_record("a", "uc1_docs", "uc1_docs"), _record("b", "uc1_docs", None, error="boom")]
    m = compute_routing_accuracy(records)
    assert m.total == 1


def test_empty_records_no_division_by_zero():
    m = compute_routing_accuracy([])
    assert m.total == 0
    assert m.accuracy == 0.0
