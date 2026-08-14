"""Lightweight inference-time faithfulness check (PRD FR13, §6.2: "RAGAS metric or LLM-as-judge
at inference time"). Full RAGAS + golden dataset is Phase 4 scope; this is the Phase 3 alternative.
"""

from dataclasses import dataclass

from paymentcopilot.generation.generator import call_claude

_PASS_TOKEN = "PASS"
_FAIL_TOKEN = "FAIL"

JUDGE_SYSTEM_PROMPT = f"""You are a strict faithfulness judge. You are given an ANSWER and the \
GROUNDING TEXT it was supposed to be based on. Determine whether every factual claim in the \
ANSWER is directly supported by the GROUNDING TEXT.

Respond with exactly one line in this format:
{_PASS_TOKEN} or {_FAIL_TOKEN} — <one short reason>

Respond {_FAIL_TOKEN} if the ANSWER makes any claim not present in or contradicted by the \
GROUNDING TEXT. Respond {_PASS_TOKEN} only if every claim is traceable to the GROUNDING TEXT. \
Do not add any other text."""


@dataclass(frozen=True)
class FaithfulnessResult:
    passed: bool
    reason: str


def check_faithfulness(answer_text: str, grounding_text: str) -> FaithfulnessResult:
    if not grounding_text.strip():
        return FaithfulnessResult(passed=False, reason="no grounding text available")

    user_prompt = f"GROUNDING TEXT:\n{grounding_text}\n\nANSWER:\n{answer_text}"
    verdict = call_claude(JUDGE_SYSTEM_PROMPT, user_prompt).strip()

    passed = verdict.upper().startswith(_PASS_TOKEN)
    reason = verdict.split("—", 1)[1].strip() if "—" in verdict else verdict
    return FaithfulnessResult(passed=passed, reason=reason)
