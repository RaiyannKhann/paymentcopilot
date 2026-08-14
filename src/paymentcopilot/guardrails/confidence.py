"""Retrieval-confidence gating, shared by UC1 and UC3 (both similarity-search-backed)."""

from paymentcopilot.models import RetrievedChunk


def passes_confidence(chunks: list[RetrievedChunk], threshold: float) -> bool:
    """True if the top retrieved chunk clears the confidence threshold.

    UC2 (structured transaction lookup) does not use this — its grounding is an exact-key
    Postgres lookup, not a similarity search, so a retrieval score doesn't describe confidence
    in the transaction facts.
    """
    return bool(chunks) and chunks[0].score >= threshold
