"""Plain-language explanations for transaction error codes.

Canonical source; kept in sync with data/docs_corpus/07-error-codes.md.
"""

ERROR_CODE_EXPLANATIONS: dict[str, str] = {
    "insufficient_funds": (
        "The customer's account or card did not have enough available balance "
        "to cover the payment."
    ),
    "card_expired": "The card's expiry date has passed.",
    "card_declined": (
        "The issuing bank declined the transaction without a more specific reason "
        "(generic risk decline)."
    ),
    "authentication_failed": (
        "3D Secure / OTP authentication was attempted but the customer entered the "
        "wrong code or cancelled."
    ),
    "authentication_timeout": (
        "The customer did not complete required authentication within the "
        "15-minute window."
    ),
    "invalid_card_number": (
        "The card number failed basic format/checksum validation before even "
        "reaching the issuer."
    ),
    "issuer_unavailable": (
        "The card issuer's systems did not respond in time. This is transient "
        "and safe to retry."
    ),
    "risk_blocked": (
        "Payment Copilot's fraud engine blocked the transaction due to risk signals "
        "(unusual velocity, mismatched billing details, etc.)."
    ),
}


def explain_error_code(error_code: str | None) -> str | None:
    if error_code is None:
        return None
    return ERROR_CODE_EXPLANATIONS.get(error_code, "No explanation available for this error code.")
