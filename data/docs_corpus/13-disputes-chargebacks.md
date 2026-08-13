# Disputes & Chargebacks Overview

## What a dispute is

A dispute (chargeback) occurs when a cardholder contacts their issuing bank to reverse a charge, rather than seeking a refund directly from you. The issuer provisionally debits the disputed amount and gives you an opportunity to contest it with evidence before the outcome is finalized.

## Dispute lifecycle

| State | Meaning |
|---|---|
| `opened` | The issuer has notified Payment Copilot of a new dispute; funds are held pending resolution. |
| `evidence_required` | You must submit supporting evidence before the deadline (see below). |
| `under_review` | Evidence has been submitted and is being evaluated by the issuer/card network. |
| `won` | The dispute was resolved in your favor; held funds are released back to you. |
| `lost` | The dispute was resolved in the cardholder's favor; the disputed amount plus a dispute fee is deducted from your next settlement (see [Settlements & Payout Schedule](09-settlements.md)). |

## Evidence submission

When a dispute enters `evidence_required`, you have **7 days** to submit evidence via `POST /v1/disputes/{id}/evidence`. Strong evidence typically includes: proof of delivery/service fulfillment, customer communication showing the charge was authorized, and — if applicable — a prior refund record showing the charge was already resolved through the normal refund flow rather than a chargeback. Missing the deadline results in an automatic loss.

## Dispute reason codes

Card networks classify disputes by reason, most commonly: `fraudulent` (cardholder claims they didn't authorize the charge), `product_not_received`, `product_unacceptable`, `duplicate_processing`, and `subscription_cancelled` (charged after the cardholder believed they'd cancelled). The reason code shapes what evidence is most persuasive — a `fraudulent` dispute benefits most from AVS/CVV match records and device/IP history, while `product_not_received` benefits most from shipment tracking.

## Prevention

Common preventable causes of disputes: unclear billing descriptors (customer doesn't recognize the charge on their statement), slow refund turnaround (customer disputes instead of waiting), and failure to cancel a subscription promptly on request. Keeping your billing descriptor recognizable and refund/cancellation flows fast measurably reduces dispute rates.

## Dispute fees

A non-refundable dispute fee is charged per opened dispute regardless of outcome, to cover card-network processing costs. This fee amount is disclosed in your merchant pricing plan and is separate from the disputed transaction amount itself.
