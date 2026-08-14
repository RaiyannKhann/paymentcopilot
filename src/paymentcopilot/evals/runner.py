"""Runs the golden set against the live system, once per item (no batching path exists)."""

import time
from dataclasses import dataclass, field

from paymentcopilot.evals.golden_set import GoldenItem
from paymentcopilot.graph.router import run_query
from paymentcopilot.models import RetrievedChunk


@dataclass(frozen=True)
class EvalRecord:
    item: GoldenItem
    route: str | None = None
    escalated: bool | None = None
    guardrail_status: str | None = None
    answer: str | None = None
    retrieved_chunks: list[RetrievedChunk] = field(default_factory=list)
    transaction: object | None = None
    error: str | None = None
    latency_s: float = 0.0


def run_golden_set(items: list[GoldenItem]) -> list[EvalRecord]:
    records = []
    for item in items:
        start = time.monotonic()
        try:
            result = run_query(item.query, merchant_id=item.merchant_id)
            records.append(
                EvalRecord(
                    item=item,
                    route=result.route,
                    escalated=result.escalated,
                    guardrail_status=result.guardrail_status,
                    answer=result.answer,
                    retrieved_chunks=result.retrieved_chunks,
                    transaction=result.transaction,
                    latency_s=time.monotonic() - start,
                )
            )
        except Exception as e:  # noqa: BLE001 - one flaky item must not abort the run
            records.append(
                EvalRecord(item=item, error=str(e), latency_s=time.monotonic() - start)
            )
    return records
