"""Query Pinecone for the top-k most similar chunks to a query.

Docs/policy content is platform-wide (shared across all merchants), so retrieval
filters by doc_type ("docs" for UC1, "policy" for UC3), not by tenant_id. tenant_id
scoping is reserved for content that is genuinely per-merchant (see structured/lookup.py
for the actual multi-tenant boundary: the transactions table).
"""

from functools import lru_cache

from paymentcopilot.config import settings
from paymentcopilot.embeddings.embedder import embed_one
from paymentcopilot.models import Chunk, RetrievedChunk


@lru_cache(maxsize=1)
def _get_index():
    from pinecone import Pinecone

    pc = Pinecone(api_key=settings.pinecone_api_key)
    return pc.Index(settings.pinecone_index_name)


def retrieve(
    query: str,
    top_k: int = 5,
    doc_type: str = "docs",
    tenant_id: str | None = None,
) -> list[RetrievedChunk]:
    index = _get_index()
    query_vector = embed_one(query)

    filter_ = {"doc_type": {"$eq": doc_type}}
    if tenant_id is not None:
        filter_["tenant_id"] = {"$eq": tenant_id}

    result = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        filter=filter_,
    )

    retrieved = []
    for match in result["matches"]:
        metadata = match["metadata"]
        chunk = Chunk(
            id=match["id"],
            text=metadata["text"],
            source_doc=metadata["source_doc"],
            section=metadata["section"],
            chunk_index=metadata["chunk_index"],
            doc_type=metadata["doc_type"],
            tenant_id=metadata["tenant_id"],
        )
        retrieved.append(RetrievedChunk(chunk=chunk, score=match["score"]))
    return retrieved
