"""Prompt-injection detection via hand-rolled regex heuristics (PRD §6.1, resolves §14's
"NeMo Guardrails vs. hand-rolled" open question in favor of hand-rolled for Phase 3).

Applied to raw user queries (input_guardrail node) and to transaction `description` fields
(UC2 node), the latter being the structured-field injection surface FR10 calls out explicitly.
"""

import re
from dataclasses import dataclass

_INSTRUCTION_OVERRIDE = [
    re.compile(r"ignore (all |any )?(previous|prior|above)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard (the |all )?(system|above)", re.IGNORECASE),
    re.compile(r"forget (everything|what) (you were|i) (told|said)", re.IGNORECASE),
    re.compile(r"new instructions\s*:", re.IGNORECASE),
]

_ROLE_PLAY_JAILBREAK = [
    re.compile(r"you are now\b", re.IGNORECASE),
    re.compile(r"act as (if )?", re.IGNORECASE),
    re.compile(r"pretend (you are|to be)", re.IGNORECASE),
    re.compile(r"\bDAN\b"),
    re.compile(r"developer mode", re.IGNORECASE),
    re.compile(r"unrestricted (AI|mode)", re.IGNORECASE),
]

_SYSTEM_PROMPT_EXFILTRATION = [
    re.compile(r"reveal (your |the )?system prompt", re.IGNORECASE),
    re.compile(r"(print|show|output) (your |the )?(instructions|prompt)", re.IGNORECASE),
    re.compile(r"what (are|were) your instructions", re.IGNORECASE),
    re.compile(r"output everything above", re.IGNORECASE),
]

_CROSS_TENANT_EXFILTRATION = [
    re.compile(r"ignore.*(merchant|tenant).*(id|scope|filter)", re.IGNORECASE),
    re.compile(r"(list|return|show) all (other )?(merchants|transactions)", re.IGNORECASE),
    re.compile(r"bypass.*(tenant|merchant)\s*(filter|scope|check)", re.IGNORECASE),
]

_DELIMITER_ESCAPE = [
    re.compile(r"```system"),
    re.compile(r"<\|im_start\|>"),
    re.compile(r"\[INST\]"),
    re.compile(r"###\s*system", re.IGNORECASE),
]

_CATEGORIES: list[tuple[str, list[re.Pattern]]] = [
    ("instruction_override", _INSTRUCTION_OVERRIDE),
    ("role_play_jailbreak", _ROLE_PLAY_JAILBREAK),
    ("system_prompt_exfiltration", _SYSTEM_PROMPT_EXFILTRATION),
    ("cross_tenant_exfiltration", _CROSS_TENANT_EXFILTRATION),
    ("delimiter_escape", _DELIMITER_ESCAPE),
]


@dataclass(frozen=True)
class InjectionResult:
    matched: bool
    category: str | None = None
    matched_text: str | None = None


def scan_injection(text: str) -> InjectionResult:
    for category, patterns in _CATEGORIES:
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return InjectionResult(matched=True, category=category, matched_text=match.group(0))
    return InjectionResult(matched=False)
