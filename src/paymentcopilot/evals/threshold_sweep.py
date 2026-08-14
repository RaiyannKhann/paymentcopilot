"""Manual, occasional-run tool for PRD §14's open question: empirically tune
UC1_CONFIDENCE_THRESHOLD/UC3_CONFIDENCE_THRESHOLD against the golden set.

Deliberately re-runs `run_query` per candidate rather than simulating post-hoc from one run's
recorded scores: a post-hoc check only predicts outcomes correctly when *raising* a threshold
above an item's originally-passing score. Lowering it below an originally-failing score can't be
simulated, because in that direction the LLM call (and faithfulness check) never actually ran the
first time, so there is no real answer to grade — assuming "gate passes => correct answer" would
overstate a lower threshold's apparent quality.
"""

import dataclasses
from unittest.mock import patch

from paymentcopilot.evals.golden_set import GoldenItem
from paymentcopilot.evals.refusal_metric import RefusalMetrics, compute_refusal_correctness
from paymentcopilot.evals.runner import run_golden_set

UC1_SWEEP_CATEGORIES = {"uc1_happy", "refusal_low_confidence"}
UC3_SWEEP_CATEGORIES = {"uc3_happy", "refusal_policy_gap"}


def _sweep(items: list[GoldenItem], settings_field: str, candidates: list[float]) -> list[tuple[float, RefusalMetrics]]:
    from paymentcopilot.config import settings

    results = []
    for candidate in candidates:
        patched = dataclasses.replace(settings, **{settings_field: candidate})
        with patch("paymentcopilot.generation.generator.settings", patched):
            records = run_golden_set(items)
        results.append((candidate, compute_refusal_correctness(records)))
    return results


def sweep_uc1_thresholds(items: list[GoldenItem], candidates: list[float]) -> list[tuple[float, RefusalMetrics]]:
    subset = [i for i in items if i.category in UC1_SWEEP_CATEGORIES]
    return _sweep(subset, "uc1_confidence_threshold", candidates)


def sweep_uc3_thresholds(items: list[GoldenItem], candidates: list[float]) -> list[tuple[float, RefusalMetrics]]:
    subset = [i for i in items if i.category in UC3_SWEEP_CATEGORIES]
    return _sweep(subset, "uc3_confidence_threshold", candidates)


def parse_candidates(raw: str) -> list[float]:
    return [float(x.strip()) for x in raw.split(",") if x.strip()]
