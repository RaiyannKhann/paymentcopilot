"""Load markdown documents from the docs corpus directory."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Document:
    source_doc: str
    text: str


def load_docs(corpus_dir: Path) -> list[Document]:
    docs = []
    for path in sorted(corpus_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        docs.append(Document(source_doc=path.name, text=path.read_text()))
    return docs
