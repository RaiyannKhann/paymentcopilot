"""Builds the Markdown + JSON report pair written to docs/03-eval-results/ per run."""

import json
from dataclasses import asdict
from pathlib import Path

from paymentcopilot.evals.refusal_metric import (
    RefusalMetrics,
    compute_refusal_correctness,
    compute_strict_refusal_correctness,
)
from paymentcopilot.evals.routing_metric import compute_routing_accuracy
from paymentcopilot.evals.runner import EvalRecord


def _refusal_by_category(records: list[EvalRecord]) -> dict[str, RefusalMetrics]:
    categories = sorted({r.item.category for r in records})
    return {
        category: compute_refusal_correctness([r for r in records if r.item.category == category])
        for category in categories
    }


def _failing_items(records: list[EvalRecord]) -> list[dict]:
    failures = []
    for r in records:
        if r.error is not None:
            continue
        reasons = []
        if r.escalated != r.item.expected_escalated:
            reasons.append(f"escalated={r.escalated} expected={r.item.expected_escalated}")
        if r.route != r.item.expected_route:
            reasons.append(f"route={r.route} expected={r.item.expected_route}")
        if r.item.expected_answer_substring and (
            not r.answer or r.item.expected_answer_substring not in r.answer
        ):
            reasons.append(f"missing expected substring {r.item.expected_answer_substring!r}")
        if reasons:
            failures.append({"id": r.item.id, "category": r.item.category, "reasons": reasons})
    return failures


def build_report(
    run_id: str,
    golden_set_path: str,
    records: list[EvalRecord],
    skip_ragas: bool,
    ragas_scores: dict | None = None,
) -> tuple[str, dict]:
    refusal = compute_refusal_correctness(records)
    refusal_by_category = _refusal_by_category(records)
    strict = compute_strict_refusal_correctness(records)
    routing = compute_routing_accuracy(records)
    failing = _failing_items(records)
    errors = [{"id": r.item.id, "error": r.error} for r in records if r.error is not None]

    report = {
        "run_id": run_id,
        "golden_set_path": golden_set_path,
        "golden_set_size": len(records),
        "skip_ragas": skip_ragas,
        "refusal_correctness": asdict(refusal),
        "refusal_correctness_by_category": {k: asdict(v) for k, v in refusal_by_category.items()},
        "strict_refusal_diagnostics": asdict(strict),
        "routing_accuracy": asdict(routing),
        "ragas": ragas_scores,
        "errors": errors,
        "failing_items": failing,
        "records": [
            {
                "id": r.item.id,
                "category": r.item.category,
                "query": r.item.query,
                "route": r.route,
                "expected_route": r.item.expected_route,
                "escalated": r.escalated,
                "expected_escalated": r.item.expected_escalated,
                "guardrail_status": r.guardrail_status,
                "answer": r.answer,
                "error": r.error,
                "latency_s": r.latency_s,
            }
            for r in records
        ],
    }

    md_lines = [
        f"# Eval run {run_id}",
        "",
        f"- Golden set: `{golden_set_path}` ({len(records)} items)",
        f"- RAGAS: {'skipped' if skip_ragas else 'included'}",
        "",
        "## Refusal correctness",
        "",
        (
            f"TP={refusal.tp} FP={refusal.fp} FN={refusal.fn} TN={refusal.tn} | "
            f"precision={refusal.precision:.3f} recall={refusal.recall:.3f} "
            f"f1={refusal.f1:.3f} accuracy={refusal.accuracy:.3f}"
        ),
        "",
        "### By category",
        "",
        (
            "_precision/recall/f1 show `n/a` for categories with no refusals expected or predicted "
            "(TP=FP=FN=0) — accuracy alone is the meaningful signal there._"
        ),
        "",
        "| category | precision | recall | f1 | accuracy |",
        "|---|---|---|---|---|",
    ]
    for category, m in sorted(refusal_by_category.items()):
        no_positive_signal = m.tp + m.fp + m.fn == 0
        precision = "n/a" if no_positive_signal else f"{m.precision:.3f}"
        recall = "n/a" if no_positive_signal else f"{m.recall:.3f}"
        f1 = "n/a" if no_positive_signal else f"{m.f1:.3f}"
        md_lines.append(f"| {category} | {precision} | {recall} | {f1} | {m.accuracy:.3f} |")

    md_lines += [
        "",
        "### Strict guardrail-reason diagnostic",
        "",
        (
            f"{strict.exact_match}/{strict.checked} matched expected guardrail category "
            f"({strict.exact_match_rate:.3f})"
        ),
        "",
        "## Routing accuracy",
        "",
        f"{routing.correct}/{routing.total} correct ({routing.accuracy:.3f})",
        "",
        "### Confusion matrix (expected->actual)",
        "",
    ]
    for key, count in sorted(routing.confusion_matrix.items()):
        md_lines.append(f"- {key}: {count}")

    if ragas_scores:
        md_lines += ["", "## RAGAS scores", ""]
        for metric_name, value in sorted(ragas_scores.items()):
            md_lines.append(f"- {metric_name}: {value:.3f}")

    md_lines += ["", "## Failing items", ""]
    if failing:
        for f in failing:
            md_lines.append(f"- **{f['id']}** ({f['category']}): {'; '.join(f['reasons'])}")
    else:
        md_lines.append("None.")

    if errors:
        md_lines += ["", "## Errors", ""]
        for e in errors:
            md_lines.append(f"- **{e['id']}**: {e['error']}")

    return "\n".join(md_lines) + "\n", report


def write_report(output_dir: Path, run_id: str, markdown: str, report: dict) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / f"{run_id}.md"
    json_path = output_dir / f"{run_id}.json"
    md_path.write_text(markdown, encoding="utf-8")
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return md_path, json_path
