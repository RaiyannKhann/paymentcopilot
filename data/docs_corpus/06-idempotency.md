# Idempotency Keys

## Why idempotency matters

Network failures happen. If your server sends a `POST /v1/payments` request and the connection drops before you receive a response, you don't know whether the payment was created or not. Retrying blindly risks creating a duplicate payment and double-charging the customer. Idempotency keys solve this.

## Using an idempotency key

Pass an `Idempotency-Key` header with any `POST` or `PATCH` request:

```
curl https://api.paymentcopilot.dev/v1/payments \
  -u key_test_ABC123:secret_XYZ789 \
  -H "Idempotency-Key: order_4521_attempt_1" \
  -d amount=150000 -d currency=INR
```

If a request with the same idempotency key is received again within 24 hours, Payment Copilot returns the original response (same status code, same body) instead of creating a new resource — even if the request parameters differ on the retry. The API does not attempt to merge or reconcile differing parameters; the first request "wins" for a given key.

## Choosing a good key

Use a value that uniquely identifies the *logical operation*, not the HTTP request itself — for example, an internal order ID plus an attempt counter (`order_4521_attempt_1`). Do not generate a new random key on every retry; that defeats the purpose, since a new key is treated as a brand-new operation.

## Idempotency key scope

Keys are scoped per API key pair (test and live mode keys have entirely separate idempotency namespaces) and expire after 24 hours. After expiry, reusing the same key value starts a fresh operation.

## What is NOT idempotent by default

`GET` requests are naturally idempotent and don't need a key. Endpoints that are inherently non-repeatable in effect — like `POST /v1/payment_links/{id}/deactivate` — still benefit from idempotency keys to guard against duplicate-request race conditions during retries, even though "deactivate" is conceptually a one-time action.

## Concurrent requests with the same key

If two requests with the same idempotency key arrive concurrently (before the first has finished processing), the second request receives a `409 idempotency_key_in_progress` error rather than blocking. Your retry logic should back off and retry after a short delay in this case, not treat it as a hard failure.
