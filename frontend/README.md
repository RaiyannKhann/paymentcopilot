# Payment Copilot — Frontend

Next.js frontend for Payment Copilot (`frontendspec.md`), Phase 7. Three experiences:

- **Support Console** (`/`) — a multi-turn conversation: ask UC1/UC2/UC3 questions, see the grounded answer, route, sources, and guardrail status for each turn. Follow-ups are answered against the backend's per-session memory (the last 5 turns), and "New conversation" starts a fresh `session_id`.
- **Request Trace** (`/trace/[requestId]`) — the pipeline the backend actually ran for a given request: rate limit, semantic cache, router, input guardrails, retrieval/lookup, generation, output guardrails.
- **Attack Lab** (`/attack-lab`) — curated, server-side attack cases run through the real guardrail functions. Never reaches Claude.

The frontend only ever talks to the FastAPI backend (`NEXT_PUBLIC_API_BASE_URL`) — never directly to Postgres, Redis, Pinecone, or Anthropic.

## Local development

```
cp .env.example .env.local
npm install
npm run dev
```

Requires the backend running locally (see the repo root README) at the URL in `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`), with `CORS_ALLOW_ORIGINS` on the backend including `http://localhost:3000`.

## Build

```
npm run build
npm run lint
```

## Deploying

Intended for Vercel, pointed at a Cloud Run–hosted backend (see `frontendspec.md` §9 for the architecture diagram). Set `NEXT_PUBLIC_API_BASE_URL` to the deployed backend's URL and `NEXT_PUBLIC_DEMO_TENANT_ID` to the demo tenant (default `demo-merchant`) in the Vercel project's environment variables, and set the backend's `CORS_ALLOW_ORIGINS` to the deployed Vercel origin. Deployment itself (Vercel project setup, Cloud Run service, DNS) is an infra step outside this repo.
