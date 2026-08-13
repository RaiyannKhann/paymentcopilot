"""Load, chunk, embed, and upsert the docs/policy corpora into Pinecone."""

from pathlib import Path

from tqdm import tqdm

from paymentcopilot.config import settings
from paymentcopilot.embeddings.embedder import EMBEDDING_DIM, embed
from paymentcopilot.ingestion.chunker import chunk_documents
from paymentcopilot.ingestion.loader import load_docs
from paymentcopilot.models import Chunk

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
DOCS_CORPUS_DIR = DATA_DIR / "docs_corpus"
POLICY_CORPUS_DIR = DATA_DIR / "policy"
UPSERT_BATCH_SIZE = 100


def _get_pinecone_index(reset: bool = False):
    from pinecone import Pinecone, ServerlessSpec

    pc = Pinecone(api_key=settings.pinecone_api_key)
    existing = {idx["name"] for idx in pc.list_indexes()}

    if reset and settings.pinecone_index_name in existing:
        pc.delete_index(settings.pinecone_index_name)
        existing.discard(settings.pinecone_index_name)

    if settings.pinecone_index_name not in existing:
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_region),
        )
    return pc.Index(settings.pinecone_index_name)


def _to_vector(chunk: Chunk, embedding: list[float]) -> dict:
    return {
        "id": chunk.id,
        "values": embedding,
        "metadata": {
            "text": chunk.text,
            "source_doc": chunk.source_doc,
            "section": chunk.section,
            "chunk_index": chunk.chunk_index,
            "doc_type": chunk.doc_type,
            "tenant_id": chunk.tenant_id,
        },
    }


def _upsert_chunks(index, chunks: list[Chunk], desc: str) -> None:
    for i in tqdm(range(0, len(chunks), UPSERT_BATCH_SIZE), desc=desc):
        batch = chunks[i : i + UPSERT_BATCH_SIZE]
        embeddings = embed([c.text for c in batch])
        vectors = [_to_vector(c, e) for c, e in zip(batch, embeddings)]
        index.upsert(vectors=vectors)


def ingest_corpus(corpus_dir: Path, doc_type: str, index=None) -> tuple[int, int]:
    """Chunk, embed, and upsert one corpus directory tagged with the given doc_type."""
    docs = load_docs(corpus_dir)
    chunks = chunk_documents(docs, doc_type=doc_type)

    if index is None:
        index = _get_pinecone_index()

    _upsert_chunks(index, chunks, desc=f"Embedding + upserting ({doc_type})")
    return len(docs), len(chunks)


def ingest_all(reset: bool = False) -> dict[str, tuple[int, int]]:
    """Ingest both the docs corpus (UC1) and the policy corpus (UC3)."""
    index = _get_pinecone_index(reset=reset)
    return {
        "docs": ingest_corpus(DOCS_CORPUS_DIR, doc_type="docs", index=index),
        "policy": ingest_corpus(POLICY_CORPUS_DIR, doc_type="policy", index=index),
    }


# Backwards-compatible alias used by Phase 1 CLI/tests.
def ingest(corpus_dir: Path = DOCS_CORPUS_DIR) -> tuple[int, int]:
    return ingest_corpus(corpus_dir, doc_type="docs")
