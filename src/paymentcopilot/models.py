"""Shared data models for the RAG pipeline."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    source_doc: str
    section: str
    chunk_index: int
    doc_type: str = "docs"  # "docs" (UC1) | "policy" (UC3)
    tenant_id: str = "shared"  # docs/policy content is platform-wide, not per-merchant


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class Answer:
    text: str
    retrieved_chunks: list[RetrievedChunk] = field(default_factory=list)
    grounded: bool = True


@dataclass(frozen=True)
class Transaction:
    txn_id: str
    merchant_id: str
    status: str
    error_code: str | None
    amount: int
    currency: str
    description: str | None
    created_at: str


@dataclass(frozen=True)
class RouterResult:
    query: str
    route: str  # "uc1_docs" | "uc2_transaction" | "uc3_policy" | "out_of_scope"
    route_reason: str
    answer: str
    escalated: bool
    retrieved_chunks: list[RetrievedChunk] = field(default_factory=list)
    transaction: Transaction | None = None
