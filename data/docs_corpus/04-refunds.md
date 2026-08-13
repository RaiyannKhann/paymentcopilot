# Refunds

## Overview

Refunds return some or all of a captured payment's funds to the customer. Only `captured` payments can be refunded — you cannot refund an `authorized`-but-uncaptured payment (void it instead) or a `failed` payment.

## Creating a refund

```
POST /v1/payments/{payment_id}/refunds
{
  "amount": 50000,
  "reason": "requested_by_customer"
}
```

Omit `amount` to refund the full remaining captured amount. Partial refunds are supported and can be issued multiple times against the same payment as long as the cumulative refunded amount does not exceed the original captured amount.

## Refund reasons

The `reason` field accepts: `requested_by_customer`, `duplicate`, `fraudulent`, or `product_unavailable`. This field is required and is used for downstream dispute-defense reporting — if a chargeback is later filed on a payment you've already refunded for `requested_by_customer`, that refund record strengthens your dispute response.

## Refund timelines

Refunds are initiated immediately on the Payment Copilot side, but funds typically take 5–10 business days to appear back on the customer's statement, depending on their card issuer. This is standard across the card networks and is not something a merchant or Payment Copilot can accelerate.

## Refund states

A refund object has its own lifecycle: `pending` → `processed` or `failed`. A `refund.processed` webhook fires when the issuer confirms the refund; a `refund.failed` webhook fires if the issuer rejects it (rare, usually because the original card has been closed — in that case the refund is automatically redirected to the merchant's on-file bank account instead).

## Refund policy window

Payment Copilot's platform does not enforce a hard refund time window at the API level — refunds can technically be issued against a captured payment at any point after capture, subject to your own merchant account's refund policy. **Merchant-specific refund policy questions (e.g., "can I refund after 90 days?") are governed by your account's compliance policy document, not by API-level restrictions** — check your policy documentation for the applicable window before relying on this API to permit or block a late refund.

## Partial refunds and multiple refunds

You can issue several partial refunds against the same payment. The API tracks `amount_refunded` on the payment object, incrementing with each successful refund. Attempting to refund more than the remaining unrefunded amount returns a `400 refund_amount_exceeds_captured` error.
