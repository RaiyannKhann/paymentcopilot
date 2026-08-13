# Multi-Currency / International Payments

## Overview

Payment Copilot can collect payments in a customer's local currency even if your settlement account is in a different currency, letting you present familiar pricing to international customers without maintaining bank accounts in every currency.

## How currency conversion works

When a customer pays in a currency other than your settlement currency, Payment Copilot converts the collected amount to your settlement currency at the exchange rate in effect at the moment of **capture** (not at authorization, if the two are separated in time). The applied rate and conversion fee are itemized on both the payment object (`exchange_rate`, `conversion_fee`) and the corresponding settlement batch report.

## Presenting local pricing

You can either let Payment Copilot auto-convert a single base-currency price into the customer's local currency at checkout (dynamic currency conversion), or set your own fixed price per currency for more predictable customer-facing pricing. Auto-conversion is simpler to maintain but exposes customers to daily rate fluctuations; fixed per-currency pricing requires you to update prices manually as rates drift significantly.

## International card acceptance

Cards issued outside your primary market are accepted by default, but are subject to a higher scrutiny tier in the risk engine — expect a somewhat higher `risk_blocked` rate on first-time international cards from a given cardholder until a payment history is established. This is a fraud-prevention measure, not a hard restriction.

## Cross-border fees

International transactions (card issuing country differs from your settlement country) incur an additional cross-border fee on top of the standard processing fee, disclosed in your merchant pricing plan. This is separate from and additive to the currency conversion fee described above, which only applies if the transaction currency also differs from your settlement currency.

## Regulatory considerations

Some currencies and countries are subject to additional local regulatory requirements (e.g., mandatory 3D Secure-equivalent authentication in certain regions). These are enforced automatically at the API level — a payment attempted without the required authentication step for a regulated corridor will return `authentication_failed` rather than completing without it, protecting you from a payment that would later be non-compliant.

## Refunding cross-border payments

Refunds on cross-border payments are issued in the original transaction currency and are subject to the same conversion mechanics in reverse; because exchange rates move between capture and refund, the amount debited from your settlement balance for the refund may differ slightly from the amount originally credited. This variance is itemized separately in the settlement report as an `fx_variance` line item.
