# Payment Links

## Overview

Payment links let you accept a payment without building a full checkout flow. You create a link via the API or dashboard, share the URL with a customer (email, SMS, chat), and the customer completes payment on a hosted page.

## Creating a payment link

```
POST /v1/payment_links
{
  "amount": 250000,
  "currency": "INR",
  "description": "Invoice #4521",
  "expire_by": 1735689600
}
```

The response includes a `short_url` you can share directly. Links are single-use by default — once a payment succeeds, the link is marked `paid` and further visits show a "this link has already been used" page rather than allowing a second payment.

## Reusable links

Set `reusable: true` at creation time to allow multiple customers to pay through the same link (useful for a shared donation page or a general "pay us" link not tied to one invoice). Reusable links do not auto-expire and must be manually disabled via `POST /v1/payment_links/{id}/deactivate`.

## Expiry

Set `expire_by` as a Unix timestamp to auto-expire a link. Attempting to pay an expired link shows the customer an "expired" page and no payment can be captured against it. If omitted, links default to a 15-day expiry from creation.

## Notifications

Set `notify.sms: true` or `notify.email: true` at creation time (with a corresponding `customer.contact` or `customer.email`) to have Payment Copilot automatically send the link to the customer, rather than you distributing it yourself.

## Partial payments

Set `partial_payment: true` with a `first_min_partial_amount` to allow a customer to pay less than the full amount as an initial installment. The link stays active (showing a reduced remaining balance) until the full amount has been collected across one or more payments, or until it expires.

## Reconciling payment links

A `payment_link.paid` webhook fires once a payment completes against the link. The webhook payload includes both the `payment_link_id` and the underlying `payment_id`, so you can look up the full payment lifecycle via the standard payments endpoints described in [Payment Lifecycle](03-payments-lifecycle.md).
