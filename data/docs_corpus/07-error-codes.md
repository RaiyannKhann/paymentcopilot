# Error Codes Reference

## Overview

Every failed payment, refund, or API request includes a machine-readable `error_code`. This page maps each code to a plain-language explanation and recommended next step. Error codes are stable identifiers — safe to match on in code — unlike the human-readable `error_description`, which may change wording over time.

## Payment failure codes

| error_code | Plain-language explanation | Recommended action |
|---|---|---|
| `insufficient_funds` | The customer's account or card did not have enough available balance to cover the payment. | Ask the customer to use a different payment method or top up their account. |
| `card_expired` | The card's expiry date has passed. | Ask the customer to update their card details. |
| `card_declined` | The issuing bank declined the transaction without a more specific reason (generic risk decline). | Ask the customer to contact their bank, or try a different payment method. |
| `authentication_failed` | 3D Secure / OTP authentication was attempted but the customer entered the wrong code or cancelled. | Ask the customer to retry the payment and complete authentication. |
| `authentication_timeout` | The customer did not complete required authentication within the 15-minute window. | Ask the customer to retry; the payment session has expired. |
| `invalid_card_number` | The card number failed basic format/checksum validation before even reaching the issuer. | Ask the customer to re-check the card number for typos. |
| `issuer_unavailable` | The card issuer's systems did not respond in time. This is transient. | Safe to retry automatically after a short delay. |
| `risk_blocked` | Payment Copilot's fraud engine blocked the transaction due to risk signals (unusual velocity, mismatched billing details, etc.). | Not eligible for automatic retry; ask the customer to contact support if they believe this is an error. |
| `capture_amount_exceeds_authorized` | An attempt was made to capture more than the originally authorized amount. | Fix the capture request to be ≤ the authorized amount. |
| `refund_amount_exceeds_captured` | An attempt was made to refund more than the remaining captured, unrefunded amount. | Fix the refund request amount. |

## API-level error codes

| error_code | Plain-language explanation | Recommended action |
|---|---|---|
| `authentication_error` | Missing or invalid API credentials. | Check that the correct key ID/secret pair is being sent. |
| `key_revoked` | The API key used has been revoked or expired. | Generate and deploy a new key pair; see [Authentication & API Keys](01-authentication.md). |
| `rate_limit_exceeded` | Too many requests sent in a short window for this account. | Back off and retry with exponential delay; see [Rate Limits & Retries](08-rate-limits-retries.md). |
| `idempotency_key_in_progress` | A request with the same idempotency key is still being processed. | Retry after a short delay rather than treating this as a hard failure. |
| `invalid_request_error` | A required parameter was missing or malformed. | Check the `error_description` field for the specific parameter at fault. |

## Retryability

Codes fall into two broad categories:
- **Transient / retryable**: `issuer_unavailable`, `rate_limit_exceeded`, `idempotency_key_in_progress`. Safe to retry with backoff.
- **Terminal / non-retryable**: `insufficient_funds`, `card_expired`, `risk_blocked`, `invalid_card_number`. Retrying without changing the underlying issue (e.g., asking for a new card) will fail again.

Automated retry logic should only retry the transient category; retrying a terminal failure wastes API calls and provides a poor customer experience (repeated declines look like a broken checkout, not a card issue).
