# Settlements & Payout Schedule

## What settlement means

Settlement is the process of moving captured payment funds from Payment Copilot's holding account into your merchant bank account. A payment being `captured` does not mean the money is in your bank account yet — it means the customer has been charged and the funds are now owed to you, pending settlement.

## Default settlement schedule

By default, funds settle on a **T+3 rolling basis**: a payment captured on day T is included in the settlement batch that pays out on day T+3 (business days, excluding bank holidays). Enterprise accounts can request T+1 settlement after a risk review.

## Settlement batches

Each settlement batch corresponds to a single bank transfer and includes every payment captured within the batch's cutoff window, minus fees and any refunds processed against those payments in the same window. A `settlement.processed` webhook fires when a batch is transferred, with a `settlement_id` you can use to fetch the full batch breakdown via `GET /v1/settlements/{settlement_id}`.

## Settlement holds

New merchant accounts may be placed on an initial rolling reserve (a percentage of each batch withheld for a fixed period, typically 90 days) as a risk mitigation measure while payment history is established. This is disclosed at account creation and reduces automatically as an account builds a clean transaction history. A hold is not the same as a dispute-related freeze (see below).

## Disputes and settlement impact

If a payment is disputed (chargeback filed) after it has already settled, the disputed amount plus a dispute fee is deducted from your **next** settlement batch, not clawed back from the bank transfer that already occurred. If this would take a settlement negative, the shortfall carries forward to the following batch.

## Reconciliation

Each settlement batch report includes, per payment: the gross captured amount, the processing fee, any refund deductions, and the net amount contributing to the batch total. This report is the authoritative source for accounting reconciliation — the sum of `payment.captured` webhook amounts alone will not match your bank deposits, because fees and refunds are netted out at settlement time, not at capture time.

## Delayed settlements

If a settlement fails (e.g., invalid bank account details on file), you'll receive a `settlement.failed` webhook and the funds roll into the next scheduled batch once the underlying bank account issue is resolved in the dashboard. Settlement failures do not expire or get discarded.
