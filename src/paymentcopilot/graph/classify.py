"""Deterministic, rule-based query classification into UC1/UC2/UC3/out-of-scope.

Per PRD FR2, routing must be deterministic and inspectable — not a single black-box
LLM call. Every classification returns a human-readable reason so the decision is
visible in logs/traces (see graph/router.py's RouterResult.route_reason).
"""

import re

TXN_ID_RE = re.compile(r"\btxn_[a-zA-Z0-9]+\b")

# Phrases that signal "is this permitted / what's the rule" rather than "how do I use the API".
POLICY_PHRASES = [
    "can i",
    "am i allowed",
    "is it allowed",
    "is it permitted",
    "allowed to",
    "policy",
    "compliant",
    "compliance",
    "permitted",
    "eligible",
    "am i eligible",
]

# Topics the policy/compliance phrasing above needs to be paired with to count as UC3 —
# without this pairing, "can I..." questions about e.g. API usage would be misrouted.
POLICY_TOPICS = [
    "refund",
    "dispute",
    "chargeback",
    "subscription",
    "kyc",
    "compliance hold",
    "cancel",
]

# Broad payment-domain vocabulary; presence of any of these (without a stronger UC2/UC3
# signal) routes to UC1 docs Q&A. Absence of all of these routes to out-of-scope.
PAYMENT_DOMAIN_KEYWORDS = [
    "payment",
    "refund",
    "webhook",
    "api",
    "key",
    "idempotency",
    "subscription",
    "dispute",
    "chargeback",
    "settlement",
    "currency",
    "transaction",
    "error",
    "rate limit",
    "security",
    "pci",
    "token",
    "card",
    "kyc",
    "compliance",
    "policy",
    "merchant",
    "checkout",
    "capture",
    "authoriz",  # matches authorize/authorization/authorized
    "webhooks",
    "test mode",
    "live mode",
]


def classify_query(query: str) -> tuple[str, str]:
    """Return (route, reason). route is one of: uc2_transaction, uc3_policy, uc1_docs, out_of_scope."""
    q = query.lower()

    txn_match = TXN_ID_RE.search(query)
    if txn_match:
        return "uc2_transaction", f"matched transaction id pattern '{txn_match.group(0)}'"

    has_policy_phrase = any(p in q for p in POLICY_PHRASES)
    has_policy_topic = any(t in q for t in POLICY_TOPICS)
    if has_policy_phrase and has_policy_topic:
        return "uc3_policy", "matched policy/permission phrasing combined with a policy topic keyword"

    if any(kw in q for kw in PAYMENT_DOMAIN_KEYWORDS):
        return "uc1_docs", "matched payment-domain vocabulary; defaulting to docs Q&A"

    return "out_of_scope", "no recognized payment-domain terms matched"
