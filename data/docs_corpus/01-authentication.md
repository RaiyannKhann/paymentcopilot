# Authentication & API Keys

## Overview

Every request to the Payment Copilot API must be authenticated using an API key pair: a **key ID** and a **key secret**. These are generated from the merchant dashboard under Settings → API Keys. Each merchant account can hold up to five active key pairs at a time, which makes it possible to rotate keys without downtime.

## Test mode vs. live mode keys

Key pairs are mode-specific. Test mode keys are prefixed `key_test_` and live mode keys are prefixed `key_live_`. Requests made with a test key are always routed to the sandbox environment, regardless of any other request parameters — there is no way to accidentally move money with a test key. See [Test Mode vs. Live Mode](10-test-vs-live-mode.md) for details on sandbox behavior.

## Making an authenticated request

Include your key ID and key secret as HTTP Basic Auth credentials on every request:

```
curl https://api.paymentcopilot.dev/v1/payments \
  -u key_test_ABC123:secret_XYZ789
```

Requests without valid credentials receive a `401 authentication_error` response. Requests with a syntactically valid but revoked or expired key receive a `403 key_revoked` response.

## Key rotation

To rotate a key without downtime:

1. Generate a new key pair in the dashboard.
2. Deploy the new key pair to your servers.
3. Confirm traffic is flowing on the new key pair (visible in the dashboard's "Key usage" panel).
4. Revoke the old key pair.

Revoked keys stop working immediately. There is no grace period, so do not revoke a key until you've confirmed the new one is live in production.

## Key scoping

Keys can optionally be scoped to a restricted set of permissions (read-only, payments-only, webhooks-only) when generated. Scoped keys are recommended for any server that only needs a subset of API access — for example, a reporting service that only reads transaction data should use a read-only key, not a full-access key.

## Best practices

- Never embed API key secrets in client-side code (mobile apps, browser JavaScript). Secrets must only live on your backend.
- Store secrets in an environment variable or secrets manager, not in source control.
- Rotate keys immediately if you suspect a leak, and check the "Key usage" panel for anomalous request volume or unfamiliar IP ranges.
- Use separate key pairs per environment (staging, production) so a leaked staging key cannot be used against production.
