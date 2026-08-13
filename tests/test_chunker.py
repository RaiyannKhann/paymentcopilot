from paymentcopilot.ingestion.chunker import chunk_document
from paymentcopilot.ingestion.loader import Document

SAMPLE_DOC = """# Sample Doc

## Section One

This is the first section with a small amount of text.

## Section Two

This is the second section with a small amount of text.
"""


def test_chunk_document_splits_on_headers():
    doc = Document(source_doc="sample.md", text=SAMPLE_DOC)
    chunks = chunk_document(doc)

    assert len(chunks) == 2
    assert chunks[0].section == "Sample Doc — Section One"
    assert chunks[1].section == "Sample Doc — Section Two"
    assert "first section" in chunks[0].text
    assert "second section" in chunks[1].text


def test_chunk_ids_are_deterministic():
    doc = Document(source_doc="sample.md", text=SAMPLE_DOC)
    chunks_a = chunk_document(doc)
    chunks_b = chunk_document(doc)

    assert [c.id for c in chunks_a] == [c.id for c in chunks_b]


def test_long_section_is_sub_split_with_overlap():
    long_body = " ".join(f"word{i}" for i in range(900))
    doc = Document(source_doc="long.md", text=f"# Long Doc\n\n## Big Section\n\n{long_body}\n")
    chunks = chunk_document(doc)

    assert len(chunks) > 1
    assert all(c.source_doc == "long.md" for c in chunks)
