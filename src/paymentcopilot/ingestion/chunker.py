"""Header-aware chunking with word-count based sub-splitting."""

import hashlib
import re

from paymentcopilot.ingestion.loader import Document
from paymentcopilot.models import Chunk

MAX_SECTION_WORDS = 400
OVERLAP_WORDS = 50

_SECTION_SPLIT_RE = re.compile(r"^## (.+)$", re.MULTILINE)


def _split_into_sections(text: str) -> list[tuple[str, str]]:
    """Split doc text into (section_heading, section_body) pairs on '## ' headers."""
    title_match = re.match(r"^# (.+)$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Untitled"

    matches = list(_SECTION_SPLIT_RE.finditer(text))
    if not matches:
        return [(title, text.strip())]

    sections = []
    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sections.append((f"{title} — {heading}", body))
    return sections


def _sub_split(text: str, max_words: int, overlap_words: int) -> list[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text]

    parts = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        parts.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap_words
    return parts


def _make_id(doc_type: str, source_doc: str, chunk_index: int) -> str:
    digest = hashlib.sha1(f"{doc_type}::{source_doc}::{chunk_index}".encode()).hexdigest()
    return digest[:16]


def chunk_document(doc: Document, doc_type: str = "docs", tenant_id: str = "shared") -> list[Chunk]:
    chunks = []
    chunk_index = 0
    for heading, body in _split_into_sections(doc.text):
        if not body:
            continue
        for part in _sub_split(body, MAX_SECTION_WORDS, OVERLAP_WORDS):
            chunks.append(
                Chunk(
                    id=_make_id(doc_type, doc.source_doc, chunk_index),
                    text=part,
                    source_doc=doc.source_doc,
                    section=heading,
                    chunk_index=chunk_index,
                    doc_type=doc_type,
                    tenant_id=tenant_id,
                )
            )
            chunk_index += 1
    return chunks


def chunk_documents(docs: list[Document], doc_type: str = "docs", tenant_id: str = "shared") -> list[Chunk]:
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc, doc_type=doc_type, tenant_id=tenant_id))
    return all_chunks
