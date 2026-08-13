"""Query Pinecone for the top-k most similar chunks to a query."""

from functools import lru_cache

from paymentcopilot.config import settings
from paymentcopilot.embeddings.embedder import embed_one
from paymentcopilot.models import Chunk, RetrievedChunk


@lru_cache(maxsize=1)
def _get_index():
    from pinecone import Pinecone

    pc = Pinecone(api_key=settings.pinecone_api_key)
    return pc.Index(settings.pinecone_index_name)


def retrieve(query: str, top_k: int = 5, tenant_id: str = "demo-merchant") -> list[RetrievedChunk]:
    index = _get_index()
    query_vector = embed_one(query)

    result = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
        filter={"tenant_id": {"$eq": tenant_id}},
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
            tenant_id=metadata["tenant_id"],
        )
        retrieved.append(RetrievedChunk(chunk=chunk, score=match["score"]))
    return retrieved
