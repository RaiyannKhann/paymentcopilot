"""Local sentence-transformers embedding wrapper."""

from functools import lru_cache

from paymentcopilot.config import settings

EMBEDDING_DIM = 384


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


def embed(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()


def embed_one(text: str) -> list[float]:
    return embed([text])[0]
