# Payment Copilot

Payments Support Copilot — a multi-tenant, production-styled RAG gateway that answers merchant support queries for a payment API platform (Razorpay/Stripe-style). See [prd.md](prd.md) for the full product requirements and phased build plan.

This repo is being built in phases (see `prd.md` §11). **Phase 1** (current): a bare RAG pipeline — ingest docs, embed, retrieve, generate a grounded answer — no guardrails, routing, evals, caching, or deployment yet.

All documentation, transaction, and policy data in this repo is original and/or synthetic, generated for portfolio/demo purposes. No real merchant, transaction, or PII data is used anywhere.

## Setup

1. Create and activate a virtual environment:
   ```
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your API keys:
   ```
   cp .env.example .env
   ```
   - **Anthropic**: sign up at platform.claude.com, add billing, create an API key under Settings → API Keys.
   - **Pinecone**: sign up at app.pinecone.io (free Starter tier), create a project and API key. The index is created automatically on first ingestion run.
4. Verify setup:
   ```
   python scripts/verify_setup.py
   ```

## Usage

Ingest the docs corpus into Pinecone:
```
python -m paymentcopilot.cli ingest
```

Ask a question:
```
python -m paymentcopilot.cli ask "How do I verify a webhook signature?"
```

Add `--show-chunks` to see the raw retrieved chunks and similarity scores.
