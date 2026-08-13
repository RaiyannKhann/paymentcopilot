"""Call Claude to generate a grounded answer from retrieved chunks."""

from tenacity import retry, stop_after_attempt, wait_exponential

from paymentcopilot.config import settings
from paymentcopilot.generation.prompts import SYSTEM_PROMPT, build_user_prompt
from paymentcopilot.models import Answer, RetrievedChunk

_NO_INFO_MARKER = "I don't have enough information in the docs"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def _call_claude(user_prompt: str) -> str:
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return response.content[0].text


def generate_answer(query: str, chunks: list[RetrievedChunk]) -> Answer:
    if not chunks:
        return Answer(
            text=f"{_NO_INFO_MARKER} confidently — no relevant documentation was found.",
            retrieved_chunks=[],
            grounded=False,
        )

    user_prompt = build_user_prompt(query, chunks)
    text = _call_claude(user_prompt)
    grounded = _NO_INFO_MARKER not in text

    return Answer(text=text, retrieved_chunks=chunks, grounded=grounded)
