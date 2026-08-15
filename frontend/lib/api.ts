// Thin typed fetch wrapper. The frontend only ever talks to this FastAPI base — never
// directly to Pinecone, Postgres, Redis, or Anthropic (frontendspec.md §9).
import type {
  AttackCase,
  AttackRunResult,
  HealthResponse,
  QueryRequest,
  QueryResponse,
  TraceResponse,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  retryAfterSeconds?: number;

  constructor(message: string, status: number, retryAfterSeconds?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.retryAfterSeconds = retryAfterSeconds;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init?.headers,
      },
    });
  } catch {
    throw new ApiError(
      "Could not reach the Payment Copilot API. Is the backend running?",
      0
    );
  }

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    let retryAfterSeconds: number | undefined;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") {
        detail = body.detail;
      } else if (typeof body?.detail?.detail === "string") {
        detail = body.detail.detail;
        retryAfterSeconds = body.detail.retry_after_seconds;
      }
    } catch {
      // response wasn't JSON — keep the generic message
    }
    throw new ApiError(detail, response.status, retryAfterSeconds);
  }

  return response.json() as Promise<T>;
}

export function postQuery(payload: QueryRequest): Promise<QueryResponse> {
  return request<QueryResponse>("/query", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getTrace(requestId: string): Promise<TraceResponse> {
  return request<TraceResponse>(`/trace/${encodeURIComponent(requestId)}`);
}

export function getAttackCases(): Promise<{ cases: AttackCase[] }> {
  return request<{ cases: AttackCase[] }>("/attack-lab/cases");
}

export function runAttackCase(attackId: string): Promise<AttackRunResult> {
  return request<AttackRunResult>("/attack-lab/run", {
    method: "POST",
    body: JSON.stringify({ attack_id: attackId }),
  });
}

// /health answers 503 (not 200) when a dependency is down, and the degraded body is
// exactly what we want to display — so this bypasses the throw-on-!ok path above.
export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
  const body = (await response.json()) as HealthResponse;
  if (typeof body?.status !== "string") {
    throw new ApiError("Unexpected /health response", response.status);
  }
  return body;
}
