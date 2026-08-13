# Architecture

Living architecture reference for Payment Copilot. Updated as each build phase lands.

## Phase 1 — Bare RAG pipeline

```
docs corpus (data/docs_corpus/*.md)
  -> loader.load_docs
  -> chunker.chunk_documents (header-aware, ~400-word sections, 50-word overlap)
  -> embedder.embed (sentence-transformers/all-MiniLM-L6-v2, 384-dim)
  -> Pinecone upsert (single index, tenant_id metadata)

query -> embedder.embed_one -> Pinecone query (top-k, tenant_id filter)
      -> retriever.retrieve -> RetrievedChunk[]
      -> generator.generate_answer (Claude, grounded system prompt)
      -> Answer (text, retrieved_chunks, grounded)
```

No routing, guardrails, caching, or API layer yet — see `prd.md` §11 for the full phased plan.
