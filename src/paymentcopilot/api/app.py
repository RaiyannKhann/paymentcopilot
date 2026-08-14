"""FastAPI gateway (FR23/FR24, PRD §10): POST /query, GET /health, POST /evals/run.

No token-level streaming: output guardrails (faithfulness + PII-leak check) must run
on the complete generated answer before it's safe to return, so /query is a plain
synchronous JSON response - see docs/02-decisions-log.md's Phase 5 entry.
"""

import asyncio
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from paymentcopilot.api.dependencies import get_redis, rate_limit_dependency
from paymentcopilot.api.request_logging import RequestLoggingMiddleware
from paymentcopilot.api.schemas import (
    EvalsRunRequest,
    HealthResponse,
    QueryRequest,
    QueryResponse,
)
from paymentcopilot.cache.semantic_cache import get_cached_answer, store_answer
from paymentcopilot.cache.session_memory import append_turn
from paymentcopilot.config import settings
from paymentcopilot.evals.golden_set import load_golden_set
from paymentcopilot.evals.report import build_report, write_report
from paymentcopilot.evals.runner import run_golden_set
from paymentcopilot.generation.usage_tracking import get_usage_totals, reset_usage_tracking
from paymentcopilot.graph.router import run_query
from paymentcopilot.models import RouterResult
from paymentcopilot.structured.db import get_connection

app = FastAPI(title="Payment Copilot")
app.add_middleware(RequestLoggingMiddleware)


def _build_grounding_refs(result: RouterResult) -> list[str]:
    refs = []
    if result.transaction is not None:
        refs.append(f"transaction:{result.transaction.txn_id}")
    refs.extend(f"{rc.chunk.source_doc} — {rc.chunk.section}" for rc in result.retrieved_chunks)
    return refs


def run_query_with_usage(query: str, merchant_id: str) -> tuple[RouterResult, dict]:
    """Runs entirely inside one asyncio.to_thread call: ContextVar state set by
    reset_usage_tracking() doesn't propagate back out of a thread, so reset/call/read
    must all happen in the same thread."""
    reset_usage_tracking()
    result = run_query(query, merchant_id=merchant_id)
    return result, get_usage_totals()


@app.post("/query", response_model=QueryResponse)
async def query(
    request: Request,
    payload: QueryRequest,
    redis_client=Depends(get_redis),
    _rate_limit: None = Depends(rate_limit_dependency),
) -> QueryResponse:
    session_id = payload.session_id or str(uuid.uuid4())
    request.state.pc_tenant_id = payload.tenant_id

    cached = await get_cached_answer(payload.tenant_id, payload.query, redis_client)
    if cached is not None:
        request.state.pc_cache_hit = True
        request.state.pc_route = cached["source_route"]
        request.state.pc_guardrail_status = cached["guardrail_status"]
        request.state.pc_escalated = cached["escalated"]
        request.state.pc_token_usage = None
        return QueryResponse(**cached, session_id=session_id)

    result, usage = await asyncio.to_thread(
        run_query_with_usage, payload.query, payload.tenant_id
    )

    await append_turn(
        payload.tenant_id,
        session_id,
        {
            "query": result.query,
            "route": result.route,
            "answer": result.answer,
            "escalated": result.escalated,
            "guardrail_status": result.guardrail_status,
            "timestamp": datetime.now(UTC).isoformat(),
        },
        redis_client,
    )

    response_payload = {
        "answer": result.answer,
        "source_route": result.route,
        "grounding_refs": _build_grounding_refs(result),
        "guardrail_status": result.guardrail_status,
        "escalated": result.escalated,
    }
    await store_answer(
        payload.tenant_id, payload.query, response_payload, result.escalated, redis_client
    )

    request.state.pc_cache_hit = False
    request.state.pc_route = result.route
    request.state.pc_guardrail_status = result.guardrail_status
    request.state.pc_escalated = result.escalated
    request.state.pc_token_usage = usage

    return QueryResponse(**response_payload, session_id=session_id)


def _check_postgres() -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1")


@app.get("/health", response_model=HealthResponse)
async def health(redis_client=Depends(get_redis)) -> JSONResponse:
    """Liveness/readiness check. Pinecone is not actively pinged here - there's no
    equally-cheap health call, and Pinecone outages already surface as 5xx on /query."""
    checks = {}

    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception:  # noqa: BLE001 - liveness check must report, not raise, on any failure
        checks["redis"] = "unreachable"

    try:
        await asyncio.to_thread(_check_postgres)
        checks["postgres"] = "ok"
    except Exception:  # noqa: BLE001 - liveness check must report, not raise, on any failure
        checks["postgres"] = "unreachable"

    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return JSONResponse(
        status_code=200 if status == "ok" else 503,
        content={"status": status, "checks": checks},
    )


@app.post("/evals/run")
async def evals_run(payload: EvalsRunRequest) -> dict:
    """Internal/dev only - gated behind ENABLE_EVALS_ENDPOINT. 404s (not 403) when
    disabled so the endpoint's existence isn't confirmed to a prober; no new auth
    system is introduced for this."""
    if not settings.enable_evals_endpoint:
        raise HTTPException(status_code=404)

    def _run() -> dict:
        items = load_golden_set(Path(payload.golden_path))
        records = run_golden_set(items)

        ragas_scores = None
        if not payload.skip_ragas:
            from paymentcopilot.evals.ragas_eval import run_ragas

            ragas_scores = run_ragas(records)

        run_id = f"eval-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
        markdown, report = build_report(
            run_id, payload.golden_path, records, payload.skip_ragas, ragas_scores
        )
        write_report(Path(payload.output_dir), run_id, markdown, report)
        return report

    return await asyncio.to_thread(_run)
