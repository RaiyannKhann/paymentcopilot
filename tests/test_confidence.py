from paymentcopilot.guardrails.confidence import passes_confidence
from paymentcopilot.models import Chunk, RetrievedChunk

_CHUNK = Chunk(id="c1", text="text", source_doc="doc.md", section="Section", chunk_index=0)


def test_empty_chunks_fails():
    assert passes_confidence([], threshold=0.45) is False


def test_below_threshold_fails():
    chunks = [RetrievedChunk(chunk=_CHUNK, score=0.30)]
    assert passes_confidence(chunks, threshold=0.45) is False


def test_above_threshold_passes():
    chunks = [RetrievedChunk(chunk=_CHUNK, score=0.80)]
    assert passes_confidence(chunks, threshold=0.45) is True


def test_boundary_exact_score_passes():
    chunks = [RetrievedChunk(chunk=_CHUNK, score=0.45)]
    assert passes_confidence(chunks, threshold=0.45) is True
