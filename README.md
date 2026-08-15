# Payment Copilot

Payments Support Copilot — a multi-tenant, production-styled RAG gateway that answers merchant support queries for a payment API platform (Razorpay/Stripe-style). See [prd.md](prd.md) for the full product requirements and phased build plan.

This repo is being built in phases (see `prd.md` §11). **Phases 1-5 complete:** bare RAG pipeline (UC1 docs, UC2 structured transaction lookup, UC3 policy-grounded refusal), dispatched by a deterministic LangGraph router; input/output guardrails (prompt-injection detection, PII redaction, LLM-as-judge faithfulness, confidence-gated escalation); an offline evaluation harness (golden dataset, RAGAS metrics, custom refusal-correctness scoring); and a FastAPI gateway with Redis-backed semantic caching, per-tenant rate limiting, session memory, and a Docker Compose local stack. No CI/CD or cloud deployment yet — see `docs/01-architecture.md` for details on each phase.

**Phase 7 (frontend):** a Next.js frontend (`frontend/`) implementing the three experiences in `frontendspec.md` — a Support Console, a Request Trace viewer, and a curated Attack Lab — backed by additive FastAPI endpoints (`GET /trace/{request_id}`, `GET /attack-lab/cases`, `POST /attack-lab/run`) and a per-request trace object attached to `POST /query`. See `frontend/README.md` for local dev and deploy notes.

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
   python -m spacy download en_core_web_sm
   ```
   The spaCy model is required by Presidio (PII detection/redaction guardrails).
3. (Optional) Install eval-only dependencies (RAGAS + golden-set scoring — not needed at live-request runtime, only for `paymentcopilot evals ...`):
   ```
   pip install -r requirements-eval.txt
   ```
4. Copy `.env.example` to `.env` and fill in your API keys:
   ```
   cp .env.example .env
   ```
   - **Anthropic**: sign up at platform.claude.com, add billing, create an API key under Settings → API Keys.
   - **Pinecone**: sign up at app.pinecone.io (free Starter tier), create a project and API key. The index is created automatically on first ingestion run.
   - **Postgres**: needs a local Postgres server reachable at `DATABASE_URL` (default `postgresql://localhost/paymentcopilot`). Install via Homebrew if you don't have one: `brew install postgresql@16 && brew services start postgresql@16`, then `createdb paymentcopilot`.
5. Verify setup:
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

Run the golden-set eval suite (requires `requirements-eval.txt`; writes a Markdown + JSON report pair to `docs/03-eval-results/`):
```
python -m paymentcopilot.cli evals run
python -m paymentcopilot.cli evals run --skip-ragas   # fast iteration: refusal-correctness + routing accuracy only, no RAGAS LLM-judge calls
```

Manually sweep `UC1_CONFIDENCE_THRESHOLD`/`UC3_CONFIDENCE_THRESHOLD` candidates against the golden set (occasional-run tool, not part of CI):
```
python -m paymentcopilot.cli evals sweep-thresholds
```

## API (Phase 5)

Requires a running Redis instance (`REDIS_URL`, default `redis://localhost:6379/0`) in addition to Postgres and Pinecone. Run locally:
```
uvicorn paymentcopilot.api.app:app --reload
```
- `POST /query` — `{tenant_id, query, session_id?}` → `{answer, source_route, grounding_refs, guardrail_status, escalated, session_id}`. Rate-limited per tenant (`RATE_LIMIT_MAX_REQUESTS` per `RATE_LIMIT_WINDOW_SECONDS`, 429 on exceed) and semantic-cache-accelerated (near-duplicate queries short-circuit `run_query()`).
- `GET /health` — checks Redis and Postgres reachability.
- `POST /evals/run` — internal/dev only, disabled (`404`) unless `ENABLE_EVALS_ENDPOINT=true`.

Or via Docker Compose (containerizes Redis, Postgres, and a one-shot seed step alongside the API):
```
cp .env.example .env   # fill in ANTHROPIC_API_KEY and PINECONE_API_KEY
docker-compose up --build
```
The API is then reachable at `http://localhost:8000`. See `docs/01-architecture.md`'s Phase 5 section for the full request-path design.
