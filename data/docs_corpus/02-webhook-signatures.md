# Webhook Signature Verification

## Why verify signatures

Payment Copilot sends webhook events (e.g. `payment.captured`, `payment.failed`, `refund.processed`) to a URL you configure in the dashboard. Because this endpoint is publicly reachable, anyone could send a forged request that looks like a legitimate webhook. Signature verification proves that a webhook payload actually originated from Payment Copilot and was not tampered with in transit.

## How signing works

Every webhook request includes an `X-PC-Signature` header. The signature is an HMAC-SHA256 hash of the raw request body, computed using a **webhook secret** that you generate in the dashboard under Settings → Webhooks. Each webhook endpoint you configure has its own independent secret.

## Verifying a webhook signature

1. Read the raw, unparsed request body as bytes. Do not use a body that has already been parsed and re-serialized to JSON — even whitespace differences will change the computed hash.
2. Compute `HMAC-SHA256(webhook_secret, raw_body)` and hex-encode the result.
3. Compare the computed signature to the `X-PC-Signature` header value using a constant-time comparison function (e.g. `hmac.compare_digest` in Python) to avoid timing attacks.
4. If the signatures don't match, reject the request with a `400` response and do not process the event.

Example (Python):

```python
import hmac
import hashlib

def verify_signature(raw_body: bytes, signature_header: str, webhook_secret: str) -> bool:
    expected = hmac.new(webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)
```

## Handling replay attacks

Every webhook payload also includes a `timestamp` field. Reject any webhook whose timestamp is more than 5 minutes old, even if the signature is valid — this prevents a captured, valid webhook from being replayed later.

## Idempotent event handling

Webhooks may be delivered more than once for the same event (at-least-once delivery). Each event carries a unique `event_id`. Store processed `event_id` values and skip processing if you've already seen one — do not assume a webhook arrives exactly once.

## Retry behavior

If your endpoint doesn't return a `2xx` status within 10 seconds, the webhook is retried with exponential backoff: 1 min, 5 min, 30 min, 2 hr, 6 hr, then once every 12 hours for up to 3 days. After 3 days of consecutive failures, the endpoint is automatically disabled and you'll receive an email notification.

## Common mistakes

- Verifying against a JSON-parsed and re-serialized body instead of the raw bytes — this is the single most common cause of "signature mismatch" errors.
- Using `==` instead of a constant-time comparison for the signature check.
- Forgetting to handle duplicate deliveries, leading to double-processing of the same event (e.g., crediting a refund twice).
