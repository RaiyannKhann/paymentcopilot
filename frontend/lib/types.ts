// Mirrors src/paymentcopilot/api/schemas.py — keep in sync with the backend.

export interface QueryRequest {
  tenant_id: string;
  query: string;
  session_id?: string;
}

export interface TraceRetrievalChunk {
  source_doc: string;
  section: string;
  score: number;
  snippet: string;
}

export interface TraceRetrieval {
  chunks_retrieved: number;
  top_score: number | null;
  chunks: TraceRetrievalChunk[];
}

export interface TraceTransaction {
  found: boolean;
  txn_id: string | null;
  status: string | null;
  error_code: string | null;
  amount: number | null;
  currency: string | null;
  merchant_scope_verified: boolean | null;
}

export interface TraceGuardrails {
  injection: "passed" | "blocked";
  injection_category: string | null;
  pii_input: "passed" | "redacted";
  pii_input_entities: string[];
  faithfulness: "passed" | "failed" | null;
  pii_output: "passed" | "redacted" | null;
  pii_output_entities: string[];
}

export interface TraceResponse {
  request_id: string;
  route: string;
  route_reason: string;
  cache_hit: boolean;
  rate_limit_status: string;
  retrieval: TraceRetrieval | null;
  transaction_lookup: TraceTransaction | null;
  guardrails: TraceGuardrails | null;
  confidence_gate: "passed" | "escalated";
  escalated: boolean;
  token_usage: Record<string, unknown>;
  latency_ms: number;
}

export interface QueryResponse {
  answer: string;
  source_route: string;
  grounding_refs: string[];
  guardrail_status: string;
  escalated: boolean;
  session_id: string;
  request_id: string;
  trace: TraceResponse;
}

export interface AttackCase {
  attack_id: string;
  category: string;
  label: string;
  description: string;
  mode: "live" | "recorded";
  secondary_of: string | null;
}

export interface AttackRunResult {
  attack_id: string;
  category: string;
  label: string;
  mode: "live" | "recorded";
  blocked: boolean;
  guardrail: string;
  action: string;
  detail: string;
  entities_found: string[];
  pipeline: string[];
}

export interface ApiErrorDetail {
  detail: string;
  retry_after_seconds?: number;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  checks: Record<string, string>;
}
