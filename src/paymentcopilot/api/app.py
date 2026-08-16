"""FastAPI gateway (FR23/FR24, PRD §10): POST /query, GET /health, POST /evals/run.

Phase 7 (frontendspec.md) adds a sanitized request-trace object to /query's response,
GET /trace/{request_id} to reload it, and a curated public Attack Lab (GET
/attack-lab/cases, POST /attack-lab/run) that runs the real guardrail functions
against a fixed, server-side payload set - see api/attack_lab.py.

No token-level streaming: output guardrails (faithfulness + PII-leak check) must run
on the complete generated answer before it's safe to return, so /query is a plain
synchronous JSON response - see docs/02-decisions-log.md's Phase 5 entry.
"""

import asyncio
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from paymentcopilot.api import attack_lab
from paymentcopilot.api.dependencies import get_redis, rate_limit_dependency
from paymentcopilot.api.request_logging import RequestLoggingMiddleware
from paymentcopilot.api.schemas import (
    AttackCasesResponse,
    AttackRunRequest,
    AttackRunResult,
    EvalsRunRequest,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    TraceGuardrails,
    TraceResponse,
    TraceRetrieval,
    TraceRetrievalChunk,
    TraceTransaction,
)
from paymentcopilot.cache.rate_limiter import check_and_increment
from paymentcopilot.cache.semantic_cache import get_cached_answer, store_answer
from paymentcopilot.cache.session_memory import append_turn, get_session_history
from paymentcopilot.cache.trace_store import get_trace, store_trace
from paymentcopilot.config import settings
from paymentcopilot.evals.golden_set import load_golden_set
from paymentcopilot.evals.report import build_report, write_report
from paymentcopilot.evals.runner import run_golden_set
from paymentcopilot.generation.usage_tracking import get_usage_totals, reset_usage_tracking
from paymentcopilot.graph.router import run_query
from paymentcopilot.models import RouterResult
from paymentcopilot.structured.db import get_connection

MAX_HISTORY_TURNS = 5

app = FastAPI(title="Payment Copilot")
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _build_grounding_refs(result: RouterResult) -> list[str]:
    refs = []
    if result.transaction is not None:
        refs.append(f"transaction:{result.transaction.txn_id}")
    refs.extend(f"{rc.chunk.source_doc} — {rc.chunk.section}" for rc in result.retrieved_chunks)
    return refs


def _parse_guardrail_status(route: str, escalated: bool, status: str) -> tuple[TraceGuardrails, str]:
    """Turns the graph's comma-joined guardrail_status tags (e.g.
    "input_redacted:pii,output_blocked:faithfulness") into the per-stage pass/
    redacted/blocked shape frontendspec.md §3 shows. Query-level and UC2
    description-field injection/PII are both surfaced as one input signal - the
    Guardrails panel is answering "did the input guardrail act on anything", not
    which field it acted on (that distinction is what the Attack Lab's dedicated
    "Structured Field" case demonstrates).
    """
    tags = [t for t in status.split(",") if t and t != "passed"]

    injection = "passed"
    injection_category: str | None = None
    pii_input = "passed"
    output_blocked_faithfulness = False
    output_redacted_pii = False

    for tag in tags:
        if tag.startswith("input_blocked:injection:"):
            injection = "blocked"
            injection_category = tag.rsplit(":", 1)[-1]
        elif tag == "input_blocked:description_injection":
            injection = "blocked"
            injection_category = "structured_field_injection"
        elif tag in ("input_redacted:pii", "input_redacted:description_pii"):
            pii_input = "redacted"
        elif tag == "output_blocked:faithfulness":
            output_blocked_faithfulness = True
        elif tag == "output_redacted:pii":
            output_redacted_pii = True

    if route == "blocked":
        # blocked -> END: the output guardrail node is never reached.
        return (
            TraceGuardrails(
                injection=injection,
                injection_category=injection_category,
                pii_input=pii_input,
                faithfulness=None,
                pii_output=None,
            ),
            "passed",
        )

    # route != "blocked" is guaranteed here (handled above), so escalated=True with no
    # output_blocked:faithfulness tag can only mean the output guardrail node never ran.
    output_stage_ran = output_blocked_faithfulness or not escalated
    if not output_stage_ran:
        # Escalated before the output guardrail node (low-confidence self-admission,
        # txn not found, out-of-scope) - _output_guardrail_node returns immediately.
        return (
            TraceGuardrails(
                injection=injection,
                injection_category=injection_category,
                pii_input=pii_input,
                faithfulness=None,
                pii_output=None,
            ),
            "escalated",
        )

    return (
        TraceGuardrails(
            injection=injection,
            injection_category=injection_category,
            pii_input=pii_input,
            faithfulness="failed" if output_blocked_faithfulness else "passed",
            pii_output="redacted" if output_redacted_pii else "passed",
        ),
        "passed",
    )


def _build_retrieval_trace(result: RouterResult) -> TraceRetrieval | None:
    if result.route in ("out_of_scope", "blocked"):
        return None
    if result.route == "uc2_transaction" and result.transaction is None:
        return None

    chunks = result.retrieved_chunks
    scores = [rc.score for rc in chunks]
    return TraceRetrieval(
        chunks_retrieved=len(chunks),
        top_score=round(max(scores), 3) if scores else None,
        chunks=[
            TraceRetrievalChunk(
                source_doc=rc.chunk.source_doc,
                section=rc.chunk.section,
                score=round(rc.score, 3),
                snippet=rc.chunk.text[:280],
            )
            for rc in chunks
        ],
    )


def _build_transaction_trace(result: RouterResult) -> TraceTransaction | None:
    if result.route != "uc2_transaction":
        return None
    txn = result.transaction
    if txn is None:
        return TraceTransaction(found=False)
    return TraceTransaction(
        found=True,
        txn_id=txn.txn_id,
        status=txn.status,
        error_code=txn.error_code,
        amount=txn.amount,
        currency=txn.currency,
        merchant_scope_verified=True,
    )


def _build_trace(
    result: RouterResult, request_id: str, latency_ms: float, token_usage: dict
) -> TraceResponse:
    guardrails, confidence_gate = _parse_guardrail_status(
        result.route, result.escalated, result.guardrail_status
    )
    return TraceResponse(
        request_id=request_id,
        route=result.route,
        route_reason=result.route_reason,
        cache_hit=False,
        retrieval=_build_retrieval_trace(result),
        transaction_lookup=_build_transaction_trace(result),
        guardrails=guardrails,
        confidence_gate=confidence_gate,
        escalated=result.escalated,
        token_usage=token_usage or {},
        latency_ms=round(latency_ms, 1),
    )


def _build_cache_hit_trace(request_id: str, cached: dict, latency_ms: float) -> TraceResponse:
    return TraceResponse(
        request_id=request_id,
        route=cached["source_route"],
        route_reason="Served from semantic cache (near-duplicate of a prior query).",
        cache_hit=True,
        retrieval=None,
        transaction_lookup=None,
        guardrails=None,
        confidence_gate="passed",
        escalated=cached["escalated"],
        token_usage={},
        latency_ms=round(latency_ms, 1),
    )


def run_query_with_usage(
    query: str, merchant_id: str, history: list[dict] | None = None
) -> tuple[RouterResult, dict]:
    """Runs entirely inside one asyncio.to_thread call: ContextVar state set by
    reset_usage_tracking() doesn't propagate back out of a thread, so reset/call/read
    must all happen in the same thread."""
    reset_usage_tracking()
    result = run_query(query, merchant_id=merchant_id, history=history)
    return result, get_usage_totals()


@app.post("/query", response_model=QueryResponse)
async def query(
    request: Request,
    payload: QueryRequest,
    redis_client=Depends(get_redis),
    _rate_limit: None = Depends(rate_limit_dependency),
) -> QueryResponse:
    start = time.monotonic()
    session_id = payload.session_id or str(uuid.uuid4())
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    request.state.pc_tenant_id = payload.tenant_id

    cached = await get_cached_answer(payload.tenant_id, payload.query, redis_client)
    if cached is not None:
        request.state.pc_cache_hit = True
        request.state.pc_route = cached["source_route"]
        request.state.pc_guardrail_status = cached["guardrail_status"]
        request.state.pc_escalated = cached["escalated"]
        request.state.pc_token_usage = None
        await append_turn(
            payload.tenant_id,
            session_id,
            {
                "query": payload.query,
                "route": cached["source_route"],
                "answer": cached["answer"],
                "escalated": cached["escalated"],
                "guardrail_status": cached["guardrail_status"],
                "timestamp": datetime.now(UTC).isoformat(),
            },
            redis_client,
        )
        latency_ms = (time.monotonic() - start) * 1000
        trace = _build_cache_hit_trace(request_id, cached, latency_ms)
        await store_trace(request_id, trace.model_dump(), redis_client)
        return QueryResponse(**cached, session_id=session_id, request_id=request_id, trace=trace)

    history = await get_session_history(payload.tenant_id, session_id, redis_client)
    result, usage = await asyncio.to_thread(
        run_query_with_usage, payload.query, payload.tenant_id, history[-MAX_HISTORY_TURNS:]
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

    latency_ms = (time.monotonic() - start) * 1000
    trace = _build_trace(result, request_id, latency_ms, usage)
    await store_trace(request_id, trace.model_dump(), redis_client)

    return QueryResponse(**response_payload, session_id=session_id, request_id=request_id, trace=trace)


@app.get("/trace/{request_id}", response_model=TraceResponse)
async def get_trace_by_id(request_id: str, redis_client=Depends(get_redis)) -> TraceResponse:
    trace = await get_trace(request_id, redis_client)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found or expired.")
    return TraceResponse(**trace)


@app.get("/attack-lab/cases", response_model=AttackCasesResponse)
async def attack_lab_cases() -> AttackCasesResponse:
    return AttackCasesResponse(cases=attack_lab.list_cases())


@app.post("/attack-lab/run", response_model=AttackRunResult)
async def attack_lab_run(
    request: Request,
    payload: AttackRunRequest,
    redis_client=Depends(get_redis),
) -> AttackRunResult:
    client_host = request.client.host if request.client else "unknown"
    rate_limit_result = await check_and_increment(f"attack-lab:{client_host}", redis_client)
    if not rate_limit_result.allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "detail": "Attack Lab rate limit exceeded. Try again shortly.",
                "retry_after_seconds": rate_limit_result.retry_after_seconds,
            },
            headers={"Retry-After": str(rate_limit_result.retry_after_seconds)},
        )

    if attack_lab.get_case(payload.attack_id) is None:
        raise HTTPException(status_code=404, detail=f"Unknown attack_id '{payload.attack_id}'.")

    return attack_lab.run_case(payload.attack_id)


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
