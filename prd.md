# Product Requirements Document
## Payments Support Copilot — Secure, Evaluated RAG Gateway

**Owner:** Raiyan Khan
**Status:** Draft v1
**Last updated:** 2026-08-13

---

## 1. Overview

### 1.1 Summary
Payments Support Copilot is a multi-tenant, production-styled RAG gateway that answers merchant support queries for a payment API platform (Razorpay/Stripe-style). It combines document retrieval, structured transaction lookups, and policy-grounded compliance answers behind an API guarded by input/output safety checks and validated by an automated evaluation pipeline.

The project is built to demonstrate the engineering judgment required to run an LLM system in a regulated, cost-sensitive, adversarial-input environment — not to demonstrate a RAG pipeline in isolation.

### 1.2 Problem statement
Payment platforms field a high volume of repetitive merchant support queries: integration errors, transaction failure explanations, and refund/compliance questions. Human support is slow and expensive to scale; a naive LLM chatbot is unacceptable in this domain because:
- Wrong answers on compliance/refund questions carry real financial and reputational risk.
- Support tooling often has user-controlled text fields (transaction notes, ticket descriptions) that are a live prompt-injection attack surface.
- LLM behavior drifts silently as prompts, models, or retrieval data change, with no test signal unless explicitly measured.

### 1.3 Goals
- Answer three categories of merchant queries with grounded, cited responses.
- Detect and block prompt injection and PII leakage on both input and output.
- Refuse or escalate low-confidence and out-of-scope queries instead of guessing.
- Maintain an automated eval suite that catches quality regressions before they ship.
- Demonstrate real system design: caching, rate limiting, multi-tenancy, containerization, and cloud deployment.

### 1.4 Non-goals
- Not a real payments company — all transaction and merchant data is synthetic.
- Not building a general-purpose chatbot; scope is limited to the three defined query types.
- Not optimizing for massive scale (millions of req/day) — optimizing for correctness, safety, and clear system-design storytelling at portfolio scale.
- Not implementing actual payment processing, auth, or money movement.

---

## 2. Users & Use Cases

### 2.1 Personas

| Persona | Description | Primary need |
|---|---|---|
| Merchant developer | Integrating the payment API into their app | Fast, accurate answers to integration/doc questions |
| Internal support agent | Handles merchant tickets | Drafted, grounded answers to review before sending; transaction-specific explanations |
| Compliance-adjacent user (simulated) | Asks refund/policy questions | Correct policy citation or clear escalation, never a guess |

### 2.2 Use case categories

**UC1 — Docs Q&A**
Natural language questions answered from the API documentation corpus.
Example: *"How do I verify a webhook signature?"*

**UC2 — Transaction/log reasoning**
Structured lookup against a mock transactions table, explained in plain language, optionally combined with doc context (e.g., linking an error code to the relevant doc section).
Example: *"Why did txn_88213 fail?"*

**UC3 — Policy / compliance judgment**
Answers grounded strictly in a written policy document; must refuse or escalate if the answer isn't explicitly supported by retrieved policy text.
Example: *"Can I refund this transaction after 90 days?"*

### 2.3 Out-of-scope query handling
Legal advice, unrelated topics, or requests for another merchant's data must be refused with a clear, non-evasive message, not silently ignored or hallucinated around.

---

## 3. Functional Requirements

### 3.1 Query routing
- FR1: System must classify incoming queries into UC1 / UC2 / UC3 / out-of-scope before generating a response.
- FR2: Routing must be deterministic and inspectable (LangGraph node path visible in logs), not a black-box single LLM call.

### 3.2 Retrieval (UC1, UC3)
- FR3: System must chunk and embed the docs/policy corpus and store vectors in Pinecone.
- FR4: Retrieval must return top-k chunks with similarity scores; scores are used downstream for confidence gating.
- FR5: (Stretch) Retrieved chunks are re-ranked by a cross-encoder or reranking API before being passed to the LLM.

### 3.3 Structured lookup (UC2)
- FR6: System must query a mock Postgres transactions table by `txn_id` and return status, error code, timestamp, and amount.
- FR7: Error codes must be mapped to plain-language explanations, optionally enriched with relevant doc chunks.

### 3.4 Response generation
- FR8: All UC1/UC2/UC3 responses must be grounded in retrieved context; the prompt must instruct the model to answer only from provided context.
- FR9: Responses must include which source chunks/policy clauses/transaction fields the answer is grounded in (for auditability and for the faithfulness check).

### 3.5 Guardrails — input
- FR10: All input must be scanned for prompt injection patterns before reaching the LLM, including text embedded in structured fields (e.g., a transaction "description" field).
- FR11: All input must be scanned for PII (card numbers, emails, etc.) via Presidio; detected PII is redacted before logging or forwarding to the LLM.
- FR12: Out-of-scope queries are classified and short-circuited before retrieval/generation.

### 3.6 Guardrails — output
- FR13: Every generated answer must pass a faithfulness check (claims traceable to retrieved context) before being returned.
- FR14: Every generated answer must pass a PII leak check before being returned.
- FR15: If retrieval confidence is below threshold, or the faithfulness check fails, the system returns an escalation message instead of the LLM's answer.

### 3.7 Evaluation
- FR16: A golden dataset of 30-50 labeled Q&A pairs (spanning UC1/UC2/UC3, adversarial inputs, and correct-refusal cases) drives automated scoring.
- FR17: Evals compute RAGAS metrics (faithfulness, answer relevancy, context precision/recall) plus a custom refusal-correctness metric.
- FR18: Eval suite runs on-demand locally (Phase 1-4) and in CI on every prompt/retrieval-affecting change (Phase 5+).

### 3.8 Multi-tenancy
- FR19: Requests are scoped by a `tenant_id` (simulated merchant ID); retrieval and rate limiting respect tenant boundaries via metadata filtering, not data mixing.

### 3.9 Caching & rate limiting
- FR20: Semantic-similarity cache in Redis short-circuits repeated/near-duplicate queries.
- FR21: Per-tenant rate limiting in Redis prevents any single tenant from exhausting shared LLM budget.
- FR22: Short-term session memory in Redis supports multi-turn conversations with a TTL.

### 3.10 API
- FR23: FastAPI service exposes endpoints for query submission, health check, and (optionally) eval trigger.
- FR24: All endpoints are async and support streaming responses where applicable.

---

## 4. System Architecture

### 4.1 High-level flow
```
Client → FastAPI Gateway → Input Guardrails → LangGraph Router
    ├─ UC1: Retriever (Pinecone) → LLM → Output Guardrails → Response
    ├─ UC2: Postgres lookup (+optional retrieval) → LLM → Output Guardrails → Response
    └─ UC3: Retriever (policy) → confidence gate → LLM or Escalation → Output Guardrails → Response

Redis: semantic cache (pre-LLM check) | rate limiter (pre-router) | session memory (post-response)
```

### 4.2 Components

| Component | Responsibility |
|---|---|
| FastAPI Gateway | Request handling, auth/tenant scoping, streaming |
| Input Guardrails | Injection detection, PII redaction, out-of-scope classification |
| LangGraph Router | Determines UC1/UC2/UC3 path |
| Retriever | Embedding + Pinecone similarity search (+ optional rerank) |
| Structured Lookup | Postgres query against mock transactions table |
| LLM Orchestrator | Primary + fallback model calls, prompt assembly |
| Output Guardrails | Faithfulness check, PII leak check, confidence gating |
| Eval Harness | RAGAS + custom metrics against golden set |
| Redis | Cache, rate limit, session memory |

### 4.3 Data flow notes
- Every response carries a trace object (route taken, retrieved chunk IDs, confidence scores, guardrail pass/fail) for logging and debugging — this is what makes eval and incident review possible after the fact.

---

## 5. Data

### 5.1 Sources
- **Docs corpus:** publicly available payment API documentation (Razorpay/Stripe-style), used as source text for chunking/embedding.
- **Policy doc:** ~10-15 hand-written, realistic refund/compliance policy clauses, authored specifically to give UC3 something concrete to ground against.
- **Mock transactions table:** synthetic data generated for the project — clearly labeled as synthetic everywhere it appears (code, docs, UI).

### 5.2 Mock transaction schema (indicative)
| Field | Type | Notes |
|---|---|---|
| txn_id | string | Primary key |
| merchant_id | string | Tenant scope |
| status | enum | success / failed / pending / refunded |
| error_code | string, nullable | Maps to explanation table |
| amount | decimal | |
| timestamp | datetime | |

### 5.3 Data handling
- No real PII or real financial data at any point.
- Synthetic data generation scripts are version-controlled and documented, not hand-edited ad hoc.

---

## 6. Guardrails Specification

### 6.1 Input checks
| Check | Method | Action on trigger |
|---|---|---|
| Prompt injection | Heuristic/regex initially, upgradeable to classifier | Block, log, return generic refusal |
| PII in input | Presidio | Redact before forwarding/logging |
| Out-of-scope topic | Classifier or LLM-as-judge | Short-circuit to refusal, skip retrieval |

### 6.2 Output checks
| Check | Method | Action on trigger |
|---|---|---|
| Faithfulness | RAGAS metric or LLM-as-judge at inference time | Suppress answer, return escalation |
| PII leak | Presidio on generated text | Redact or suppress |
| Low confidence | Retrieval similarity score threshold | Escalate instead of answer |

### 6.3 Escalation behavior
Escalation responses must be explicit and non-evasive (e.g., "I can't confirm this from available policy — this has been flagged for a human to review"), never a silent wrong answer.

---

## 7. Evaluation Specification

### 7.1 Golden dataset
30-50 entries covering:
- Straightforward UC1/UC2/UC3 questions with known-correct grounded answers.
- Adversarial inputs (injection attempts, PII-bearing inputs).
- Cases that should be refused or escalated (out-of-scope, low-confidence, missing-context).

### 7.2 Metrics
- **Faithfulness** (RAGAS) — are answer claims supported by retrieved context.
- **Answer relevancy** (RAGAS) — does the answer address the actual question.
- **Context precision/recall** (RAGAS) — retrieval quality.
- **Refusal correctness** (custom) — did the system correctly refuse/escalate exactly the cases it should have, and only those.

### 7.3 Process
- Manual script execution in early phases; wired into GitHub Actions CI once the API/deployment layer exists, running on any PR touching prompts, retrieval config, or guardrail logic.
- Results logged to the Obsidian vault (`docs/03-eval-results/`) per run for historical tracking.

---

## 8. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Latency | Non-cached response under ~5s p95 for local/demo scale |
| Cost | Stay within free/low-cost tiers (Pinecone Starter, Redis in-container, small LLM calls) during build; teardown cloud resources when not actively demoing |
| Security | No secrets in code; PII never persisted unredacted; tenant data isolation enforced at query time |
| Observability | Structured JSON logs per request: route, latency, token usage, guardrail outcomes |
| Portability | Runs identically via Docker Compose locally and as containers in Cloud Run/GKE |

---

## 9. Tech Stack

| Layer | Choice |
|---|---|
| LLM | Claude / GPT-4o-mini (+ fallback provider) |
| Embeddings | text-embedding-3-small or local sentence-transformers |
| Vector store | Pinecone (free Starter tier) |
| Structured data | Postgres (mock transactions) |
| Orchestration | LangGraph + LangChain |
| API | FastAPI (async) |
| Guardrails | Presidio, custom injection/faithfulness checks |
| Evals | RAGAS + custom refusal-correctness metric |
| Cache/rate-limit/session | Redis |
| Containers | Docker, Docker Compose (local) |
| Deployment | Cloud Run (always-on demo); K8s manifests/Helm chart kept in-repo for GKE Autopilot demo runs |
| CI/CD | GitHub Actions (build, test, eval regression) |
| Docs/knowledge base | Obsidian vault (`docs/`), maintained by Claude Code under supervision |

---

## 10. API Design (indicative)

| Endpoint | Method | Purpose |
|---|---|---|
| `/query` | POST | Submit a merchant query, returns grounded answer or escalation |
| `/health` | GET | Liveness/readiness check |
| `/evals/run` | POST (internal/dev only) | Trigger eval suite against golden set |

`/query` request shape (indicative): `{ tenant_id, query, session_id }`
`/query` response shape (indicative): `{ answer, source_route, grounding_refs, guardrail_status, escalated: bool }`

---

## 11. Phased Build Plan

| Phase | Scope |
|---|---|
| 1 | Bare RAG pipeline: ingest, embed, retrieve, generate — no guardrails |
| 2 | Add UC2 (structured lookup) and UC3 (policy path with refusal logic) |
| 3 | Guardrails: input injection/PII checks, output faithfulness/PII/confidence checks |
| 4 | Eval harness: golden set + RAGAS + custom refusal-correctness metric |
| 5 | Redis (cache/rate-limit/session), Docker Compose, FastAPI hardening |
| 6 | Deployment: Cloud Run for live demo, K8s manifests/Helm chart in-repo, CI/CD wiring |

---

## 12. Success Metrics

- Golden-set faithfulness and relevancy scores trend upward (or stay high) across iterations, tracked over time in the vault.
- Refusal-correctness metric at or near 100% on adversarial/out-of-scope test cases.
- Zero PII leakage across the full guardrail test log.
- End-to-end demo runs cleanly on Cloud Run with real Docker images built from the same code used in local dev.

---

## 13. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Pinecone free-tier limits on namespaces/indexes | Use single index with `tenant_id` metadata filtering instead of per-tenant namespaces |
| LLM API cost creep during iteration | Semantic caching, small/cheap models for dev iteration, teardown cloud infra when idle |
| Guardrails give false sense of security | Explicit adversarial test log (`04-guardrail-attack-log.md`) documenting real attempted bypasses, not just theoretical coverage |
| Scope creep beyond three use cases | PRD non-goals section enforced; new ideas go to a backlog note, not directly into scope |
| Synthetic data read as real by mistake | Clear "synthetic data" labeling in code, docs, and any demo UI |

---

## 14. Open Questions

- Reranking step (stretch goal) — include in v1 or defer to backlog?
- NeMo Guardrails vs. hand-rolled checks — decision to be logged in `docs/02-decisions-log.md` once made.
- Exact confidence threshold for escalation — to be tuned empirically against the golden set, not fixed arbitrarily upfront.

---

## 15. Appendix

### 15.1 Sample queries by use case
- UC1: "How do I handle a webhook signature verification failure?"
- UC1: "What's the retry policy for failed settlements?"
- UC2: "Why did txn_88213 fail?"
- UC3: "Can I refund this transaction after 90 days?"
- Adversarial: transaction description field containing injected instructions attempting to exfiltrate another merchant's data.

### 15.2 Related documents (in vault)
- `docs/01-architecture.md` — living architecture reference
- `docs/02-decisions-log.md` — dated tradeoff decisions
- `docs/03-eval-results/` — per-run eval scores
- `docs/04-guardrail-attack-log.md` — adversarial test log