"""Pydantic request/response models for the FastAPI layer (PRD §10)."""

from pydantic import BaseModel


class QueryRequest(BaseModel):
    tenant_id: str
    query: str
    session_id: str | None = None


class QueryResponse(BaseModel):
    answer: str
    source_route: str
    grounding_refs: list[str]
    guardrail_status: str
    escalated: bool
    session_id: str


class HealthResponse(BaseModel):
    status: str  # "ok" | "degraded"
    checks: dict[str, str]


class EvalsRunRequest(BaseModel):
    golden_path: str = "data/eval/golden_set.jsonl"
    output_dir: str = "docs/03-eval-results"
    skip_ragas: bool = False
