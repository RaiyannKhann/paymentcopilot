"""Load, chunk, embed, and upsert the docs corpus into Pinecone."""

from pathlib import Path

from tqdm import tqdm

from paymentcopilot.config import settings
from paymentcopilot.embeddings.embedder import EMBEDDING_DIM, embed
from paymentcopilot.ingestion.chunker import chunk_documents
from paymentcopilot.ingestion.loader import load_docs
from paymentcopilot.models import Chunk

DEFAULT_CORPUS_DIR = Path(__file__).resolve().parents[3] / "data" / "docs_corpus"
UPSERT_BATCH_SIZE = 100


def _get_pinecone_index():
    from pinecone import Pinecone, ServerlessSpec

    pc = Pinecone(api_key=settings.pinecone_api_key)
    existing = {idx["name"] for idx in pc.list_indexes()}
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
            "tenant_id": chunk.tenant_id,
        },
    }


def ingest(corpus_dir: Path = DEFAULT_CORPUS_DIR) -> tuple[int, int]:
    docs = load_docs(corpus_dir)
    chunks = chunk_documents(docs)

    index = _get_pinecone_index()

    for i in tqdm(range(0, len(chunks), UPSERT_BATCH_SIZE), desc="Embedding + upserting"):
        batch = chunks[i : i + UPSERT_BATCH_SIZE]
        embeddings = embed([c.text for c in batch])
        vectors = [_to_vector(c, e) for c, e in zip(batch, embeddings)]
        index.upsert(vectors=vectors)

    return len(docs), len(chunks)
