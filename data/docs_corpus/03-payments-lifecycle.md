# Payment Lifecycle

## Overview

A payment moves through a well-defined sequence of states from creation to settlement. Understanding this lifecycle is essential for correctly handling webhooks and reconciling your records against the Payment Copilot dashboard.

## States

| State | Meaning |
|---|---|
| `created` | A payment object has been created but no payment method has been attached yet. |
| `authorized` | Funds have been reserved on the customer's payment method, but not yet captured. |
| `captured` | Funds have been captured and the payment is complete from the customer's perspective. |
| `failed` | The payment attempt failed (declined, insufficient funds, expired card, etc.). |
| `refunded` | A captured payment has been fully or partially refunded. |
| `disputed` | The cardholder has raised a chargeback; funds may be held pending resolution. |

## Authorize-then-capture flow

By default, payments are captured automatically at the moment of authorization (single-step flow). If you need to hold funds without capturing them immediately — for example, a hotel booking where the final amount isn't known until checkout — set `capture: manual` when creating the payment. Authorized-but-uncaptured payments must be captured within 7 days or the authorization automatically expires and funds are released back to the customer.

## Capturing a payment

```
POST /v1/payments/{payment_id}/capture
{
  "amount": 150000
}
```

You can capture less than the authorized amount (partial capture), but never more. Attempting to capture more than the authorized amount returns a `400 capture_amount_exceeds_authorized` error.

## Payment failures

A `failed` payment includes an `error_code` field describing why it failed. See [Error Codes Reference](07-error-codes.md) for the full list and plain-language explanations. Common causes include insufficient funds, an expired card, or the issuing bank declining the transaction for risk reasons.

## Timeouts

If a payment method requires additional customer action (e.g., 3D Secure authentication) and the customer does not complete it within 15 minutes, the payment automatically transitions to `failed` with `error_code: authentication_timeout`.

## Reconciliation

Every state transition emits a corresponding webhook event (`payment.authorized`, `payment.captured`, `payment.failed`, etc.). Your system should treat these webhooks, not the synchronous API response, as the source of truth for final payment state — network issues can cause a synchronous response to be lost even though the payment succeeded server-side.
