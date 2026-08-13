"""Prompt templates for grounded answer generation."""

from paymentcopilot.models import RetrievedChunk

SYSTEM_PROMPT = """You are a support assistant for a payment API platform. Answer the merchant's \
question using ONLY the provided documentation context below — do not use outside knowledge or \
make assumptions about behavior not stated in the context.

Rules:
- Every claim in your answer must be traceable to the provided context.
- Cite the source doc and section inline for each claim, in the form (source: <source_doc> — <section>).
- If the context does not contain enough information to answer confidently, say so explicitly \
instead of guessing — respond with: "I don't have enough information in the docs to answer this \
confidently." Do not partially answer from context and fill gaps with assumptions.
- Be concise and direct."""


def build_user_prompt(query: str, chunks: list[RetrievedChunk]) -> str:
    context_blocks = []
    for rc in chunks:
        c = rc.chunk
        context_blocks.append(
            f"[source: {c.source_doc} — {c.section}]\n{c.text}"
        )
    context = "\n\n---\n\n".join(context_blocks)

    return f"""Context:
{context}

Question: {query}"""
