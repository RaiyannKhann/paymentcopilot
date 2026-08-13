# Security Best Practices

## PCI DSS scope

Payment Copilot's hosted checkout and payment links keep raw card data off your servers entirely, which minimizes your PCI DSS compliance scope to the lightest tier (SAQ A). If you instead collect raw card details on your own page and forward them to the API directly, your PCI scope increases substantially (SAQ A-EP or higher) and requires additional controls: encrypted transmission, no persistent storage of card data, and annual self-assessment. Most integrations should use hosted checkout or client-side tokenization specifically to avoid this larger compliance burden.

## Tokenization

Rather than passing raw card numbers to your backend, use the client-side SDK to convert card details into a single-use `token` in the customer's browser or app. Your backend then creates the payment using the token, never touching the underlying PAN (primary account number). Tokens are single-use and expire after 15 minutes if unused.

## Storing payment methods for later use

To charge a customer again later (e.g., subscriptions, one-click repeat purchase), do not store card details yourself — create a `saved_payment_method` via the API, which returns an opaque `payment_method_id` referencing a card securely vaulted by Payment Copilot. This ID can be reused indefinitely for future charges and carries no PCI scope on your side.

## Webhook endpoint security

Beyond signature verification (see [Webhook Signature Verification](02-webhook-signatures.md)), webhook endpoints should: run over HTTPS only, not be publicly guessable (avoid predictable URLs like `/webhook`), and reject any request whose signature doesn't verify before doing any business logic — including database writes — to avoid a forged request triggering side effects even if you plan to no-op on the result.

## API key hygiene

See [Authentication & API Keys](01-authentication.md) for key rotation and scoping guidance. In addition: never log full API key secrets, even to internal logs — log only the key ID (which is not sensitive) or a redacted/truncated form of the secret if you need to distinguish which key made a given call.

## Handling customer PII

Fields like `customer.email`, `customer.contact`, and billing address are considered PII and should be handled per your organization's data retention policy — Payment Copilot retains this data as long as your account is active for support/dispute purposes, but you are responsible for redacting or purging it from your own systems' logs and analytics pipelines according to applicable privacy regulations (e.g., GDPR, DPDP).

## Fraud signals in the API response

Every payment response includes a `risk_score` (0–100, opaque scale) even for approved payments. A high `risk_score` on an approved payment doesn't require action, but consistently high scores from a given customer or IP range are worth monitoring even when transactions aren't outright blocked — the risk engine's threshold for `risk_blocked` and your own business threshold for "worth investigating" don't have to be the same value.
