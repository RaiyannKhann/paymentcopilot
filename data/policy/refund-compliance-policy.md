# Refund & Compliance Policy

*Effective 2026-01-01, version 1.2. This is an original, hand-authored policy document written specifically for the Payment Copilot portfolio project. It does not represent the policy of any real company.*

## Clause 1 — Standard Refund Window

Refunds may be issued against a captured payment for up to **180 days** from the original capture date without any special approval. Refund requests submitted after the 180-day window has elapsed are not automatically approved or denied by this system — they must be escalated to a human compliance reviewer, who will evaluate the request on a case-by-case basis.

## Clause 2 — Full and Partial Refunds

Both full and partial refunds are permitted within the standard refund window, subject to the API-level constraint that cumulative refunds cannot exceed the originally captured amount. There is no policy-level restriction on the number of partial refunds issued against a single payment, provided each is within the 180-day window.

## Clause 3 — Refunds on Disputed Transactions

If a chargeback has already been opened on a payment, a separate refund must **not** be issued for the same amount while the dispute is active. Instead, the merchant should submit dispute evidence through the standard dispute-resolution process. Issuing a refund on a payment that later results in a lost dispute constitutes a double reimbursement to the cardholder and is against policy. If a refund is genuinely warranted on a disputed transaction, it must go through compliance escalation, not the standard refund path.

## Clause 4 — Refunds During a KYC or Compliance Hold

Merchant accounts under an active KYC (know-your-customer) or compliance review hold may still submit refund requests, but those requests are queued rather than processed immediately. Queued refunds are released automatically once the hold is cleared. Refund requests are never silently rejected due to a hold — they remain pending until resolution.

## Clause 5 — Refunds on Fraud-Flagged Transactions

A transaction flagged by the risk engine (`risk_blocked` or a high `risk_score`) requires compliance sign-off before any refund is processed, regardless of how recently the transaction occurred. This review may take up to 14 business days. This clause exists to prevent refund-based fraud patterns (e.g., a fraudulent charge being "refunded" back to a different account than the original payment method).

## Clause 6 — Refunds After Account Closure

A merchant whose account has been closed may still request refunds on transactions processed while the account was active, for up to **12 months** after closure. Such requests must be submitted in writing to the compliance team and cannot be processed through the standard refund API, since account closure revokes API key access.

## Clause 7 — Currency of Refund

Refunds must be issued in the original transaction currency. Substituting a different currency, or refunding a foreign-currency transaction in the merchant's settlement currency instead of the original collection currency, is not permitted under this policy.

## Clause 8 — Minimum Refundable Amount

If a partial refund would leave a remaining captured balance below the platform's per-currency minimum transaction amount (see the API documentation's currency handling reference), the refund must instead be issued in full. Partial refunds that would strand a sub-minimum balance are not permitted.

## Clause 9 — Goodwill and Discretionary Refunds

Merchants may issue goodwill refunds at their own discretion for reasons outside the standard eligibility criteria (e.g., customer satisfaction, minor service issues), provided the refund is still within the 180-day standard window and does not exceed the originally captured amount. Discretionary refunds do not themselves require compliance approval, unless another clause in this policy (e.g., Clause 3, 4, or 5) independently applies to the transaction in question.

## Clause 10 — Subscription Cancellation Refunds

This policy does not mandate a prorated refund for the unused portion of a subscription billing cycle upon cancellation, except where required by consumer protection law in the cardholder's jurisdiction. Whether proration is owed in a specific case depends on applicable local law, which this system cannot determine — such requests should be escalated to compliance for a jurisdiction-specific determination.

## Clause 11 — Duplicate Charge Refunds

A confirmed duplicate charge (the same transaction accidentally captured twice) must be refunded in full within 5 business days of confirmed detection. This is an expedited path: it does not require compliance approval and is not subject to the 180-day standard window, since a duplicate charge is a processing error rather than a customer-requested refund.

## Clause 12 — Escalation to Compliance

Any refund request that does not clearly fall within Clauses 1–11 as written — including requests outside the 180-day window without a qualifying exception, cross-border regulatory questions, or any scenario not explicitly addressed by this document — must be escalated to a human compliance reviewer. This system must never approve, deny, or estimate an outcome for such a request on its own.

## Clause 13 — Policy Versioning

This document is versioned; the effective version and date are stated at the top of this file. Only the current version in force governs live decisions. Historical versions are retained for audit purposes but must not be used to answer live merchant queries.
