# Decisions Log

Dated tradeoff decisions for Payment Copilot.

## 2026-08-13 — Phase 1 tech choices

- **Embeddings:** local `sentence-transformers/all-MiniLM-L6-v2` instead of OpenAI embeddings, to keep cost near zero during dev and avoid an extra API dependency.
- **LLM default:** `claude-haiku-4-5` for cost-effective iteration, swappable to `claude-sonnet-5` via `ANTHROPIC_MODEL` env var for higher-quality demo runs.
- **Dependency management:** plain `venv` + `requirements.txt` (via `pyproject.toml` dynamic dependencies for editable install) rather than Poetry — Poetry was broken in the dev environment (bad interpreter) and not worth repairing for a small Phase 1 dependency set.
- **Docs corpus:** 15 original, hand-authored markdown docs modeled after Razorpay/Stripe-style documentation, not scraped from any real provider — avoids ToS risk and keeps content clearly labeled as synthetic/original.
- **Multi-tenancy:** single Pinecone index with a `tenant_id` metadata field added to every vector from Phase 1 onward (even though unused until Phase 2's routing/filtering), to avoid a future re-ingestion migration.
- **Scope:** no FastAPI, LangGraph/LangChain, guardrails, Redis, or Docker in Phase 1 — CLI-only, with retrieval/generation written as plain typed functions so Phase 2's LangGraph router can wrap them as nodes without a rewrite.

## 2026-08-13 — Phase 2 tech choices

- **Postgres setup:** used the local Postgres 14 service already running on this machine (via Homebrew, pre-existing from another project) rather than installing a second version or introducing Docker early — created an isolated `paymentcopilot` database, left the other project's `eduai_db` untouched. Docker remains deferred to Phase 5 as originally planned.
- **Routing method:** deterministic regex/keyword heuristics (`graph/classify.py`), not a dedicated LLM classifier call — matches FR2's wording most literally ("deterministic and inspectable... not a black-box single LLM call"), and avoids adding latency/cost to every query just for routing.
- **Tenant scoping fix:** Phase 1 filtered ALL Pinecone retrieval by `tenant_id`, which only worked because there was a single implicit tenant. Corrected in Phase 2: docs/policy content is platform-wide (shared across all merchants), so retrieval now filters by `doc_type` ("docs" vs "policy") instead. `tenant_id` metadata is retained on vectors but no longer filtered by default. The real multi-tenant boundary (FR19) is the transactions table — `structured/lookup.py` scopes every query by `(txn_id, merchant_id)`, confirmed to return "not found" rather than leaking data across merchants.
- **Pinecone re-ingestion:** chunk IDs are now hashed from `(doc_type, source_doc, chunk_index)` instead of `(source_doc, chunk_index)`, since docs and policy corpora could otherwise collide. This changed all vector IDs, so the index was reset (`ingest --reset`) rather than left with orphaned Phase-1-era vectors.
- **UC3 confidence threshold:** set to `0.45` (cosine similarity, top-1 chunk) as a provisional default — PRD §14 explicitly flags this as something to tune empirically against the golden eval set in Phase 4, not fix arbitrarily. Configurable via `UC3_CONFIDENCE_THRESHOLD` env var.
- **UC3 escalation wording:** the model is instructed to emit a fixed sentinel token (`NEEDS_ESCALATION`) rather than freely phrasing its own refusal, which the code then maps to the exact PRD §6.3 escalation message. This guarantees the non-evasive, compliance-safe wording regardless of model phrasing drift.
- **Synthetic transactions:** 40 transactions across 3 merchants (`demo-merchant`, `acme-retail`, `globex-travel`), generated deterministically (fixed seed 42) by `scripts/generate_transactions.py` into a version-controlled CSV, then loaded via `scripts/seed_transactions.py` — per PRD §5.3, generation is scripted and reproducible, not hand-edited.
