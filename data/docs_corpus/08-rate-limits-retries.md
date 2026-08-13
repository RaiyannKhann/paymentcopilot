# Rate Limits & Retries

## Default limits

API requests are rate-limited per API key pair, not per merchant account (so test and live keys have independent limits):

| Plan | Sustained rate | Burst |
|---|---|---|
| Starter | 10 requests/second | up to 30 requests in a 1-second burst |
| Growth | 50 requests/second | up to 150 requests in a 1-second burst |
| Enterprise | Custom, contact sales | Custom |

## Rate limit headers

Every response includes headers describing your current limit status:

```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1735689600
```

`X-RateLimit-Reset` is a Unix timestamp indicating when the current window resets.

## Handling 429 responses

When the limit is exceeded, the API returns `429 rate_limit_exceeded` with a `Retry-After` header (in seconds). Do not retry immediately — respect `Retry-After`, and layer exponential backoff with jitter on top of it for repeated 429s to avoid thundering-herd retries against your own limit.

Example backoff schedule: `Retry-After` value, then 2x, 4x, 8x on subsequent 429s, capped at 60 seconds between attempts, up to 5 total attempts before surfacing an error to your own caller.

## What counts against the limit

All authenticated API calls count, including read-only `GET` requests. Webhook deliveries sent *to* your server do not count against your API rate limit (that's a separate delivery system), but any API calls your webhook handler makes back to Payment Copilot do count.

## Requesting a limit increase

Sustained high-volume usage should upgrade to the Growth or Enterprise plan rather than relying on aggressive retry logic — retrying through a persistent 429 is both slow and unreliable, since your reset window resets every second and there is no queueing on the server side.

## Idempotency during retries

When retrying a `POST`/`PATCH` request after a `429` or transient failure, always reuse the same `Idempotency-Key` from the original attempt. See [Idempotency Keys](06-idempotency.md) for why this matters — without it, a retried request after an ambiguous timeout could create a duplicate payment.
