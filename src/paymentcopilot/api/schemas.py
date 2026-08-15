"""Pydantic request/response models for the FastAPI layer (PRD §10, frontendspec.md §4/§5)."""

from pydantic import BaseModel


class QueryRequest(BaseModel):
    tenant_id: str
    query: str
    session_id: str | None = None


class TraceRetrievalChunk(BaseModel):
    source_doc: str
    section: str
    score: float
    snippet: str


class TraceRetrieval(BaseModel):
    chunks_retrieved: int
    top_score: float | None = None
    chunks: list[TraceRetrievalChunk] = []


class TraceTransaction(BaseModel):
    found: bool
    txn_id: str | None = None
    status: str | None = None
    error_code: str | None = None
    amount: int | None = None
    currency: str | None = None
    merchant_scope_verified: bool | None = None


class TraceGuardrails(BaseModel):
    injection: str  # "passed" | "blocked"
    injection_category: str | None = None
    pii_input: str  # "passed" | "redacted"
    pii_input_entities: list[str] = []
    faithfulness: str | None = None  # "passed" | "failed" | None (skipped)
    pii_output: str | None = None  # "passed" | "redacted" | None (skipped)
    pii_output_entities: list[str] = []


class TraceResponse(BaseModel):
    request_id: str
    route: str
    route_reason: str
    cache_hit: bool
    rate_limit_status: str = "passed"
    retrieval: TraceRetrieval | None = None
    transaction_lookup: TraceTransaction | None = None
    guardrails: TraceGuardrails | None = None
    confidence_gate: str = "passed"  # "passed" | "escalated"
    escalated: bool = False
    token_usage: dict = {}
    latency_ms: float


class QueryResponse(BaseModel):
    answer: str
    source_route: str
    grounding_refs: list[str]
    guardrail_status: str
    escalated: bool
    session_id: str
    request_id: str
    trace: TraceResponse


class HealthResponse(BaseModel):
    status: str  # "ok" | "degraded"
    checks: dict[str, str]


class EvalsRunRequest(BaseModel):
    golden_path: str = "data/eval/golden_set.jsonl"
    output_dir: str = "docs/03-eval-results"
    skip_ragas: bool = False


class AttackCase(BaseModel):
    attack_id: str
    category: str
    label: str
    description: str
    mode: str  # "live" | "recorded"
    secondary_of: str | None = None  # set when this case is a secondary variant of another


class AttackCasesResponse(BaseModel):
    cases: list[AttackCase]


class AttackRunRequest(BaseModel):
    attack_id: str


class AttackRunResult(BaseModel):
    attack_id: str
    category: str
    label: str
    mode: str  # "live" | "recorded"
    blocked: bool
    guardrail: str  # e.g. "injection" | "pii" | "faithfulness"
    action: str
    detail: str
    entities_found: list[str] = []
    pipeline: list[str]
