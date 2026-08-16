"""Call Claude to generate a grounded answer from retrieved chunks."""

from tenacity import retry, stop_after_attempt, wait_exponential

from paymentcopilot.config import settings
from paymentcopilot.generation.prompts import (
    ESCALATION_SENTINEL,
    POLICY_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    TRANSACTION_SYSTEM_PROMPT,
    build_transaction_user_prompt,
    build_user_prompt,
)
from paymentcopilot.generation.usage_tracking import record_usage
from paymentcopilot.guardrails.confidence import passes_confidence
from paymentcopilot.guardrails.messages import LOW_CONFIDENCE_MESSAGE
from paymentcopilot.models import Answer, RetrievedChunk, Transaction

_NO_INFO_MARKER = "I don't have enough information in the docs"

ESCALATION_MESSAGE = (
    "I can't confirm this from available policy — this has been flagged for a human to review."
)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_claude(system_prompt: str, user_prompt: str) -> str:
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    record_usage(response.usage.input_tokens, response.usage.output_tokens)
    return response.content[0].text


def generate_answer(
    query: str,
    chunks: list[RetrievedChunk],
    confidence_threshold: float | None = None,
    history: list[dict] | None = None,
) -> Answer:
    """UC1 docs Q&A: grounded answer, or an explicit low-info admission (not a hard escalation)."""
    if not chunks:
        return Answer(
            text=f"{_NO_INFO_MARKER} confidently — no relevant documentation was found.",
            retrieved_chunks=[],
            grounded=False,
        )

    threshold = (
        confidence_threshold if confidence_threshold is not None else settings.uc1_confidence_threshold
    )
    if not passes_confidence(chunks, threshold):
        return Answer(text=LOW_CONFIDENCE_MESSAGE, retrieved_chunks=chunks, grounded=False)

    user_prompt = build_user_prompt(query, chunks, history=history)
    text = call_claude(SYSTEM_PROMPT, user_prompt)
    grounded = _NO_INFO_MARKER not in text

    return Answer(text=text, retrieved_chunks=chunks, grounded=grounded)


def generate_policy_answer(
    query: str,
    chunks: list[RetrievedChunk],
    confidence_threshold: float | None = None,
    history: list[dict] | None = None,
) -> Answer:
    """UC3 policy Q&A: confidence-gated, hard-escalates instead of guessing.

    Escalates (returns ESCALATION_MESSAGE, grounded=False) if either:
    - no chunks were retrieved, or the top retrieval score is below threshold, or
    - the model itself determines no clause explicitly resolves the question.
    """
    threshold = (
        confidence_threshold if confidence_threshold is not None else settings.uc3_confidence_threshold
    )

    if not passes_confidence(chunks, threshold):
        return Answer(text=ESCALATION_MESSAGE, retrieved_chunks=chunks, grounded=False)

    user_prompt = build_user_prompt(query, chunks, history=history)
    text = call_claude(POLICY_SYSTEM_PROMPT, user_prompt)

    if ESCALATION_SENTINEL in text:
        return Answer(text=ESCALATION_MESSAGE, retrieved_chunks=chunks, grounded=False)

    return Answer(text=text, retrieved_chunks=chunks, grounded=True)


def generate_transaction_answer(
    query: str,
    transaction: Transaction,
    error_explanation: str | None,
    doc_chunks: list[RetrievedChunk],
    history: list[dict] | None = None,
) -> Answer:
    """UC2 structured lookup: explain a transaction record in plain language."""
    user_prompt = build_transaction_user_prompt(
        query, transaction, error_explanation, doc_chunks, history=history
    )
    text = call_claude(TRANSACTION_SYSTEM_PROMPT, user_prompt)
    return Answer(text=text, retrieved_chunks=doc_chunks, grounded=True)
