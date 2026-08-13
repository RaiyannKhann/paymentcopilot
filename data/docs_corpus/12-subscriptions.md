# Subscriptions Basics

## Overview

Subscriptions automate recurring billing against a saved payment method. A subscription is built from a **plan** (defines amount, currency, and billing interval) and a **customer** with a payment method attached.

## Creating a plan

```
POST /v1/plans
{
  "period": "monthly",
  "interval": 1,
  "amount": 99900,
  "currency": "INR",
  "name": "Pro tier"
}
```

`period` accepts `daily`, `weekly`, `monthly`, or `yearly`; `interval` multiplies the period (e.g., `period: monthly, interval: 3` bills quarterly).

## Creating a subscription

```
POST /v1/subscriptions
{
  "plan_id": "plan_9F3ab2",
  "customer_id": "cust_7Kd21x",
  "total_count": 12
}
```

`total_count` is optional and caps the subscription at a fixed number of billing cycles (useful for a 12-month contract); omit it for an open-ended subscription that runs until cancelled.

## Billing cycle execution

On each billing date, Payment Copilot automatically attempts to charge the customer's saved payment method. A successful charge fires `subscription.charged`; a failed charge fires `subscription.payment_failed` and enters a **dunning** retry sequence: 3 additional attempts over 7 days before the subscription is marked `halted`.

## Handling failed renewal payments

During the dunning period, the subscription status is `past_due` but access should typically remain active until the retries are exhausted, to avoid disrupting a customer over a transient card issue (e.g. an `issuer_unavailable` decline). Once `halted`, treat the subscription as inactive and prompt the customer to update their payment method.

## Upgrades, downgrades, and proration

Changing a subscription's plan mid-cycle via `PATCH /v1/subscriptions/{id}` triggers proration by default: the customer is credited for unused time on the old plan and charged for the remaining time on the new plan, netted into a single adjustment on the next invoice. Set `prorate: false` to change plans without any mid-cycle adjustment (the new amount simply applies starting next cycle).

## Cancellation

`POST /v1/subscriptions/{id}/cancel` accepts a `cancel_at_cycle_end` boolean. If `true`, the subscription remains active through the end of the current paid period and then stops; if `false` (default), it cancels immediately and no further charges occur, but no automatic refund is issued for the unused portion of the current cycle unless you separately issue one.
