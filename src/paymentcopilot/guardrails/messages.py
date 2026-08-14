"""Fixed, non-evasive messages returned when a guardrail blocks or downgrades a response.

Kept separate from `generation.generator.ESCALATION_MESSAGE` (UC3-specific policy wording,
shipped in Phase 2) so each guardrail trigger has its own explicit, auditable copy per PRD §6.3.
"""

INJECTION_BLOCKED_MESSAGE = (
    "This request could not be processed because it contains content that looks like an "
    "attempt to manipulate this assistant. This has been logged and flagged for review."
)

TRANSACTION_DESCRIPTION_FLAGGED_NOTE = (
    "Note: this transaction's description field contained content flagged as a possible "
    "manipulation attempt, so it was excluded from this explanation. The status and other "
    "fields below are drawn directly from verified transaction records."
)

FAITHFULNESS_FAILURE_MESSAGE = (
    "I found related information but couldn't confirm my answer is fully supported by it, "
    "so I'm not going to guess — this has been flagged for a human to review."
)

LOW_CONFIDENCE_MESSAGE = (
    "I don't have enough reliable information to answer this confidently — this has been "
    "flagged for a human to review."
)
