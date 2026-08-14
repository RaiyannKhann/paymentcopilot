"""Routing-accuracy scoring (FR1/FR2) — first-class metric alongside refusal-correctness,
since the data (expected vs. actual route) is already available at no extra cost.
"""

from dataclasses import dataclass, field

from paymentcopilot.evals.runner import EvalRecord


@dataclass(frozen=True)
class RoutingMetrics:
    correct: int
    total: int
    accuracy: float
    confusion_matrix: dict[str, int] = field(default_factory=dict)


def compute_routing_accuracy(records: list[EvalRecord]) -> RoutingMetrics:
    scored = [r for r in records if r.error is None]
    confusion: dict[str, int] = {}
    correct = 0
    for r in scored:
        key = f"{r.item.expected_route}->{r.route}"
        confusion[key] = confusion.get(key, 0) + 1
        if r.route == r.item.expected_route:
            correct += 1

    total = len(scored)
    accuracy = correct / total if total else 0.0
    return RoutingMetrics(correct=correct, total=total, accuracy=accuracy, confusion_matrix=confusion)
