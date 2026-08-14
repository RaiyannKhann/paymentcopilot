from pathlib import Path

import pytest

from paymentcopilot.evals.golden_set import load_golden_set

FIXTURES = Path(__file__).parent / "fixtures"


def test_valid_golden_set_loads():
    items = load_golden_set(FIXTURES / "mini_golden_set.jsonl")
    assert len(items) == 2
    assert items[0].id == "mini_001"
    assert items[0].ragas_eligible is True
    assert items[1].expected_escalated is True


def test_duplicate_id_raises():
    with pytest.raises(ValueError, match="duplicate id"):
        load_golden_set(FIXTURES / "malformed_duplicate_id.jsonl")


def test_unknown_category_raises():
    with pytest.raises(ValueError, match="unknown category"):
        load_golden_set(FIXTURES / "malformed_unknown_category.jsonl")


def test_ragas_eligible_without_reference_raises():
    with pytest.raises(ValueError, match="reference_answer"):
        load_golden_set(FIXTURES / "malformed_missing_reference.jsonl")


def test_unknown_route_raises():
    with pytest.raises(ValueError, match="unknown expected_route"):
        load_golden_set(FIXTURES / "malformed_unknown_route.jsonl")
