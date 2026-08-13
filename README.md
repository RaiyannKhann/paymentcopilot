# Payment Copilot

Payments Support Copilot — a multi-tenant, production-styled RAG gateway that answers merchant support queries for a payment API platform (Razorpay/Stripe-style). See [prd.md](prd.md) for the full product requirements and phased build plan.

This repo is being built in phases (see `prd.md` §11). **Phase 2** (current): UC1 docs Q&A, UC2 structured transaction lookup, and UC3 policy-grounded refusal logic, dispatched by a deterministic LangGraph router. No guardrails, evals, caching, or deployment yet.

All documentation, transaction, and policy data in this repo is original and/or synthetic, generated for portfolio/demo purposes. No real merchant, transaction, or PII data is used anywhere.

## Setup

1. Create and activate a virtual environment:
   ```
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```
2. Install the project (editable install, pulls in `requirements.txt`):
   ```
   pip install -e .
   ```
3. Copy `.env.example` to `.env` and fill in your API keys:
   ```
   cp .env.example .env
   ```
   - **Anthropic**: sign up at platform.claude.com, add billing, create an API key under Settings → API Keys.
   - **Pinecone**: sign up at app.pinecone.io (free Starter tier), create a project and API key. The index is created automatically on first ingestion run.
   - **Postgres**: needs a local Postgres server reachable at `DATABASE_URL` (default `postgresql://localhost/paymentcopilot`). Install via Homebrew if you don't have one: `brew install postgresql@16 && brew services start postgresql@16`, then `createdb paymentcopilot`.
4. Verify setup:
   ```
   python scripts/verify_setup.py
   ```

## Usage

Ingest the docs (UC1) and policy (UC3) corpora into Pinecone:
```
python -m paymentcopilot.cli ingest
```
Pass `--reset` to delete and recreate the Pinecone index first (needed if the chunk/metadata schema changes).

Generate and load the synthetic transactions table (UC2):
```
python scripts/generate_transactions.py
python scripts/seed_transactions.py
```

Ask a question — routed automatically to UC1 docs, UC2 transaction lookup, UC3 policy, or refused as out-of-scope:
```
python -m paymentcopilot.cli ask "How do I verify a webhook signature?"
python -m paymentcopilot.cli ask "Why did txn_71348 fail?" --merchant-id globex-travel
python -m paymentcopilot.cli ask "Can I refund this transaction after 90 days?"
```

Flags: `--show-route` prints the classified route and reasoning; `--show-chunks` prints raw retrieved chunks and similarity scores; `--merchant-id` scopes transaction lookups (UC2) to a tenant (default `demo-merchant`).
