# Decisions Log

Dated tradeoff decisions for Payment Copilot.

## 2026-08-13 — Phase 1 tech choices

- **Embeddings:** local `sentence-transformers/all-MiniLM-L6-v2` instead of OpenAI embeddings, to keep cost near zero during dev and avoid an extra API dependency.
- **LLM default:** `claude-haiku-4-5` for cost-effective iteration, swappable to `claude-sonnet-5` via `ANTHROPIC_MODEL` env var for higher-quality demo runs.
- **Dependency management:** plain `venv` + `requirements.txt` (via `pyproject.toml` dynamic dependencies for editable install) rather than Poetry — Poetry was broken in the dev environment (bad interpreter) and not worth repairing for a small Phase 1 dependency set.
- **Docs corpus:** 15 original, hand-authored markdown docs modeled after Razorpay/Stripe-style documentation, not scraped from any real provider — avoids ToS risk and keeps content clearly labeled as synthetic/original.
- **Multi-tenancy:** single Pinecone index with a `tenant_id` metadata field added to every vector from Phase 1 onward (even though unused until Phase 2's routing/filtering), to avoid a future re-ingestion migration.
- **Scope:** no FastAPI, LangGraph/LangChain, guardrails, Redis, or Docker in Phase 1 — CLI-only, with retrieval/generation written as plain typed functions so Phase 2's LangGraph router can wrap them as nodes without a rewrite.
