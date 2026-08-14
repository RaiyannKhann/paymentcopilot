"""Golden-set loading and schema validation (PRD FR16, §7.1)."""

import json
from dataclasses import dataclass, field
from pathlib import Path

KNOWN_CATEGORIES = {
    "uc1_happy",
    "uc2_happy",
    "uc2_not_found",
    "uc3_happy",
    "adversarial_injection",
    "adversarial_pii",
    "refusal_out_of_scope",
    "refusal_low_confidence",
    "refusal_policy_gap",
}

KNOWN_ROUTES = {"uc1_docs", "uc2_transaction", "uc3_policy", "out_of_scope", "blocked"}


@dataclass(frozen=True)
class GoldenItem:
    id: str
    category: str
    query: str
    merchant_id: str
    expected_route: str
    expected_escalated: bool
    expected_guardrail_category: str | None = None
    expected_answer_substring: str | None = None
    ragas_eligible: bool = False
    reference_answer: str | None = None
    expected_grounding_sources: list[str] = field(default_factory=list)
    notes: str | None = None


def _validate(item: GoldenItem) -> None:
    if item.category not in KNOWN_CATEGORIES:
        raise ValueError(f"{item.id}: unknown category {item.category!r}")
    if item.expected_route not in KNOWN_ROUTES:
        raise ValueError(f"{item.id}: unknown expected_route {item.expected_route!r}")
    if item.ragas_eligible and not item.reference_answer:
        raise ValueError(f"{item.id}: ragas_eligible=true requires a reference_answer")


def load_golden_set(path: Path) -> list[GoldenItem]:
    items: list[GoldenItem] = []
    seen_ids: set[str] = set()

    with open(path, encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {e}") from e

            item = GoldenItem(**raw)
            if item.id in seen_ids:
                raise ValueError(f"{path}:{line_no}: duplicate id {item.id!r}")
            seen_ids.add(item.id)

            _validate(item)
            items.append(item)

    return items
