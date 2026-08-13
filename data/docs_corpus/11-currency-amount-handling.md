# Currency & Amount Handling

## Amounts are always in the smallest currency unit

All `amount` fields in the API are integers representing the **smallest unit** of the given currency — paise for INR, cents for USD, not decimal rupees or dollars. An amount of ₹1,500.00 is sent as `150000`. An amount of $19.99 is sent as `1999`. This avoids floating-point rounding errors that occur when doing arithmetic on decimal currency values.

## Zero-decimal currencies

A small number of supported currencies (e.g., JPY, KRW) have no minor unit at all — ¥500 is sent as `500`, not `50000`. Sending a zero-decimal currency amount as if it had two decimal places (e.g., `50000` for what you intended as ¥500) will overcharge the customer by 100x. Always check whether a currency is zero-decimal before constructing the amount field. The full zero-decimal currency list is available via `GET /v1/currencies`.

## Supported currencies

Payment Copilot supports settlement in INR and USD natively; other currencies (EUR, GBP, AED, SGD, JPY, and others) are supported for **collection** with automatic conversion to your settlement currency at the prevailing exchange rate at time of capture, plus a conversion fee disclosed in your pricing plan.

## Minimum and maximum amounts

Each currency has a platform-enforced minimum (typically equivalent to ~$0.50 USD) to prevent card-testing fraud via trivially small transactions, and a default maximum of ~$50,000 USD equivalent per transaction, which can be raised for verified merchants on request. Amounts outside this range return `400 amount_out_of_range`.

## Rounding in partial captures and refunds

When capturing or refunding a portion of an amount originally collected in a foreign currency, all internal calculations are performed in the smallest unit of the *original collection currency*, not the settlement currency, to avoid compounding rounding error across multiple partial operations against the same payment.

## Displaying amounts to customers

Because the API always works in minor units, your integration is responsible for formatting amounts for display (dividing by 100, or by 1 for zero-decimal currencies, and applying the correct currency symbol/locale formatting). The API does not return a pre-formatted display string.
