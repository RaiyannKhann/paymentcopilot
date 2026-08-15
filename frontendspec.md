# Payment Copilot — Frontend Specification

**Phase 7 — Frontend & Demo Experience**

**Frontend:** Next.js
**Deployment:** Vercel
**Backend:** FastAPI on Cloud Run

## 1. Goal

Build a polished frontend that demonstrates the depth of the Payment Copilot backend without turning it into a generic ChatGPT clone.

The frontend should make the backend's **routing, retrieval, transaction reasoning, guardrails, and execution flow visible**.

### Must-haves

The demo consists of exactly three core experiences:

1. **Support Console**
2. **Request Trace**
3. **Attack Lab**

Everything else is optional polish.

---

# 2. Support Console

The Support Console is the default landing experience and the normal user-facing interface.

Users can submit:

* **UC1:** Documentation questions
* **UC2:** Transaction questions
* **UC3:** Policy questions

Example:

```text
Payment Copilot

How can I help?

┌──────────────────────────────────────────────┐
│ Why did txn_88213 fail?                      │
└──────────────────────────────────────────────┘

                  [ Ask Copilot ]
```

### Response

```text
Transaction txn_88213 failed because the
payment authorization was rejected with ERR_402.

Status: Failed
Amount: ₹1,500

Sources
• Transaction Database
• Error Code Documentation

✓ Grounded
✓ Safety checks passed

[ View System Trace ]
```

The UI should clearly show:

* Answer
* Route / use case
* Grounding references
* Escalation status
* Guardrail status
* Link to Request Trace

The frontend does **not** implement routing, retrieval, guardrails, or generation itself. It calls the existing backend API.

---

# 3. Request Trace

The Request Trace is the primary mechanism for showing the engineering depth behind the simple support interface.

After every query, the user can open:

**View System Trace**

The trace visualizes **what the system did**, not model chain-of-thought.

Example:

```text
REQUEST
  │
  ▼
Rate Limit             ✓ Passed
  │
  ▼
Semantic Cache         MISS
  │
  ▼
Query Router           UC2
  │
  ▼
Input Guardrails       ✓ Passed
  │
  ▼
Postgres Lookup        ✓ Transaction found
  │
  ▼
Error Code Mapping     ✓ ERR_402
  │
  ▼
Pinecone Retrieval     3 chunks
  │
  ▼
Claude                 ✓ Generated
  │
  ▼
Faithfulness           ✓ Passed
  │
  ▼
PII Check              ✓ Passed
  │
  ▼
Response               ✓ Returned
```

Nodes should be expandable.

### Router

Show:

```text
Route: UC2 — Transaction Reasoning

Method: Deterministic classifier

Reason:
Transaction ID detected
```

### Retrieval

Show:

```text
Pinecone Retrieval

07-error-codes.md     0.842
04-api-errors.md      0.781
02-webhooks.md        0.731
```

Allow the user to expand a chunk to see a **sanitized source snippet**.

### Transaction Lookup

Show:

```text
Transaction
txn_88213

Status
FAILED

Error Code
ERR_402

Amount
₹1,500

Merchant scope
✓ Verified
```

### Guardrails

Show:

```text
INPUT

Prompt Injection      ✓ PASS
PII Detection         ✓ PASS

OUTPUT

Faithfulness          ✓ PASS
PII Leak Detection    ✓ PASS
```

For an escalation:

```text
Confidence Gate
⚠ ESCALATED

LLM generation skipped
```

For an attack:

```text
Injection Detection
✕ BLOCKED

Retrieval
○ SKIPPED

Claude
○ NOT CALLED
```

---

# 4. Trace Data Contract

The frontend should receive a safe trace object from the backend.

Conceptually:

```json
{
  "request_id": "req_8f21",
  "route": "uc2_transaction",
  "route_reason": "transaction ID detected",
  "cache_hit": false,

  "retrieval": {
    "chunks_retrieved": 3,
    "top_score": 0.82
  },

  "transaction_lookup": {
    "found": true
  },

  "guardrails": {
    "injection": "passed",
    "pii_input": "passed",
    "faithfulness": "passed",
    "pii_output": "passed"
  },

  "token_usage": {},
  "latency_ms": 1840
}
```

Exact implementation should follow the existing backend models.

Do **not** expose:

* API keys
* credentials
* raw PII
* secrets
* private prompts containing sensitive information
* model chain-of-thought
* other tenants' data

---

# 5. Attack Lab

The Attack Lab demonstrates the real security boundary of the system.

### Important security constraint

The public Attack Lab **must not accept arbitrary prompts that can reach Claude**.

There is uncapped LLM-cost exposure if a public user can repeatedly submit arbitrary attacks.

Instead, the public Attack Lab uses a **curated, server-side set of attack cases**.

```text
Frontend
   ↓
Attack ID
   ↓
Backend loads predefined payload
   ↓
Real input guardrail pipeline
   ↓
BLOCK → return result
```

The public Attack Lab must never automatically proceed to LLM generation.

If a guardrail unexpectedly allows an attack through:

```text
Guardrail
   ↓
PASS
   ↓
STOP
   ↓
Report:
"Guardrail did not block this test"
```

It must **not** continue to Claude.

Full end-to-end adversarial testing remains a private/local development capability.

---

# 6. Attack Categories

The public Attack Lab should include curated examples based on the existing attack log:

* Instruction override
* Jailbreak / role-play
* Cross-tenant exfiltration
* Structured-field injection
* PII in query
* PII in structured transaction fields
* Policy-gap / unsupported claim

Example interface:

```text
Guardrail Attack Lab

Test Payment Copilot's security controls.

[ Instruction Override ]
[ Jailbreak ]
[ Cross-Tenant ]
[ Structured Field ]
[ PII ]
[ Policy Gap ]

              [ Run Test ]
```

---

# 7. Attack Result

Example:

```text
RESULT

✕ ATTACK BLOCKED

Category
cross_tenant_exfiltration

Action
Request terminated before retrieval/generation.

Pipeline

Input
  ↓
Injection Detector
  ↓
BLOCK
  ↓
No Pinecone query
  ↓
No Claude call
```

For PII:

```text
PII Detection

Detected:
CREDIT_CARD

Action:
Redacted before downstream processing.

Raw value:
Never exposed
```

For structured-field injection:

```text
Transaction Description
        ↓
Injection Detection
        ↓
✕ BLOCKED
        ↓
Claude NOT CALLED
```

The Attack Lab should use the **real backend guardrail implementation**, not mocked frontend results.

---

# 8. Public Demo Safety

The public application must have backend-enforced protections.

### Attack Lab

* Curated attack IDs only
* Payloads stored server-side
* No arbitrary attack prompts
* No direct LLM invocation
* Rate limiting
* Sanitized trace responses
* No raw PII
* No cross-tenant access
* Full end-to-end attack testing remains private

### General Support Console

The normal `/query` endpoint remains protected by the existing backend rate limiting and guardrails.

The frontend is **not** a security boundary.

---

# 9. Frontend / Backend Architecture

```text
                         Vercel
                       Next.js UI
                           │
                           │ HTTPS
                           ▼
                     Cloud Run
                      FastAPI API
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Redis         LangGraph      Postgres
                           │
                    ┌──────┼──────┐
                    ▼      ▼      ▼
                   UC1    UC2    UC3
                    │      │      │
                Pinecone Postgres Pinecone
                    │      │      │
                    └──────┼──────┘
                           ▼
                         Claude
                           │
                     Guardrails
                           │
                           ▼
                        Response
```

The frontend never directly connects to Pinecone, Postgres, Redis, or Anthropic.

---

# 10. UI Design Direction

The UI should feel like a **modern developer/enterprise AI console**.

Priorities:

* Clean
* Professional
* Fast
* Technical but understandable
* Minimal animations
* Clear status indicators
* Expandable technical details
* Responsive

Avoid making it look like a generic ChatGPT clone.

The Support Console should be simple.

The Trace and Attack Lab should reveal the complexity underneath.

---

# 11. Demo Flow

The ideal portfolio demo should take roughly this path:

```text
1. Open Support Console
        ↓
2. Ask:
   "Why did txn_88213 fail?"
        ↓
3. Receive grounded UC2 answer
        ↓
4. Open Request Trace
        ↓
5. Show:
   Router → Postgres → Retrieval → Claude → Guardrails
        ↓
6. Open Attack Lab
        ↓
7. Run Cross-Tenant Attack
        ↓
8. Show:
   Injection detected → blocked → Claude never called
```

This trio is the core product demonstration.

---

# 12. Optional Polish

These are **not required for Phase 7 completion**:

* Evaluation Dashboard
* Architecture Explorer
* Evaluation history
* Conversation sidebar
* Dark/light themes
* Landing/about page
* Additional analytics
* Advanced visualization

They should only be added after the three core experiences are polished.

---

# 13. Phase 7 Success Criteria

Phase 7 is complete when:

* [ ] Next.js frontend deployed on Vercel
* [ ] Support Console works against Cloud Run
* [ ] UC1 / UC2 / UC3 queries work
* [ ] Grounding/source information is displayed
* [ ] Request Trace visualizes the actual backend execution
* [ ] Router, retrieval/database, cache, and guardrail information is visible
* [ ] Attack Lab executes real backend guardrail tests
* [ ] Attack Lab uses curated server-side attacks
* [ ] Public Attack Lab cannot invoke Claude arbitrarily
* [ ] No secrets or raw PII are exposed
* [ ] Synthetic-data disclaimer is visible
* [ ] UI is responsive and polished

## Core principle

> **Support Console shows what the system does.
> Request Trace shows how it did it.
> Attack Lab shows how it handles hostile inputs.**

This trio is the Phase 7 demo.
