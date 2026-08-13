"""Shared data models for the RAG pipeline."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    source_doc: str
    section: str
    chunk_index: int
    tenant_id: str = "demo-merchant"


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class Answer:
    text: str
    retrieved_chunks: list[RetrievedChunk] = field(default_factory=list)
    grounded: bool = True
