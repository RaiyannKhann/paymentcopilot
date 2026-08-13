# Test Mode vs. Live Mode

## Overview

Every Payment Copilot account has two fully isolated environments: **test mode** and **live mode**. They share the same API surface and dashboard UI, but no data — payments, customers, payment links, webhooks configuration — crosses between them.

## Switching modes

The dashboard has a mode toggle (top-right corner) that switches the entire UI between test and live data. At the API level, mode is determined entirely by which key pair you authenticate with — there is no separate "mode" request parameter. A request authenticated with a `key_test_` credential is always a test-mode operation, full stop.

## Test card numbers

Use these card numbers in test mode to simulate specific outcomes:

| Card number | Simulated result |
|---|---|
| `4111 1111 1111 1111` | Successful payment |
| `4000 0000 0000 0002` | Declined — `card_declined` |
| `4000 0000 0000 9995` | Declined — `insufficient_funds` |
| `4000 0000 0000 0069` | Declined — `card_expired` |
| `4000 0000 0000 3220` | Requires 3D Secure authentication |

Any CVV and any future expiry date are accepted for test cards. These numbers only work against `key_test_` credentials — using them against a live key returns `invalid_card_number`.

## Test webhooks

Webhook endpoints are configured separately for test and live mode. You can trigger a test webhook delivery manually from the dashboard (Settings → Webhooks → Send test event) without needing to create a real test payment, useful for verifying your signature verification logic (see [Webhook Signature Verification](02-webhook-signatures.md)) before going live.

## Going live

Before switching production traffic to live keys, Payment Copilot requires: a completed KYC/business verification, a live bank account on file, and at least one successful test-mode integration test run within the last 30 days. Accounts that haven't sent live traffic within 14 days of activation are automatically reverted to a "pending" live state and must re-verify bank details before live keys start working again.

## Data isolation guarantees

Test mode data is never included in live-mode reporting, settlement batches, or the golden production analytics exports. It's safe to generate large volumes of synthetic test traffic without polluting real business metrics.
