import type { ReactNode } from "react";
import type { TraceResponse } from "@/lib/types";
import { formatAmount, routeLabel } from "@/lib/format";
import { PipelineNode } from "./PipelineNode";
import type { StatusTone } from "./StatusBadge";

interface Step {
  id: string;
  title: string;
  tone: StatusTone;
  summary: string;
  detail?: ReactNode;
}

function DetailRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-white/5 py-1.5 last:border-0">
      <dt className="text-ink-faint">{label}</dt>
      <dd className="text-right font-mono text-ink">{value}</dd>
    </div>
  );
}

function CheckRow({ label, pass, verdict }: { label: string; pass: boolean; verdict: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-white/5 py-1.5 last:border-0">
      <dt className="text-ink-faint">{label}</dt>
      <dd className={`font-mono text-xs ${pass ? "text-ok" : "text-bad"}`}>{verdict}</dd>
    </div>
  );
}

/** Similarity score as a bar — the relative gap between chunk 1 and chunk 3 is the
    point of showing scores at all, and a bar carries that faster than three decimals. */
function ScoreBar({ score }: { score: number }) {
  return (
    <span className="flex items-center gap-2">
      <span aria-hidden="true" className="h-1 w-16 overflow-hidden rounded-full bg-white/8">
        <span
          className="block h-full rounded-full bg-violet-bright"
          style={{ width: `${Math.max(0, Math.min(1, score)) * 100}%` }}
        />
      </span>
      <span className="font-mono text-[11px] text-ink-muted">{score.toFixed(3)}</span>
    </span>
  );
}

function buildSteps(trace: TraceResponse): Step[] {
  const steps: Step[] = [
    { id: "rate_limit", title: "Rate Limit", tone: "success", summary: "Passed" },
    {
      id: "cache",
      title: "Semantic Cache",
      tone: trace.cache_hit ? "success" : "muted",
      summary: trace.cache_hit ? "HIT" : "MISS",
    },
  ];

  if (trace.cache_hit) {
    steps.push({
      id: "response",
      title: "Response",
      tone: "success",
      summary: "Returned from cache",
      detail:
        "This answer matched a near-duplicate query served recently, so routing/retrieval/guardrails were not re-run.",
    });
    return steps;
  }

  steps.push({
    id: "router",
    title: "Query Router",
    tone: "brand",
    summary: routeLabel(trace.route),
    detail: (
      <dl>
        <DetailRow label="Route" value={trace.route} />
        <DetailRow label="Method" value="Deterministic classifier" />
        <DetailRow label="Reason" value={trace.route_reason} />
      </dl>
    ),
  });

  const g = trace.guardrails;
  const injectionBlocked = g?.injection === "blocked";

  steps.push({
    id: "input_guardrails",
    title: "Input Guardrails",
    tone: injectionBlocked ? "danger" : g?.pii_input === "redacted" ? "warning" : "success",
    summary: injectionBlocked
      ? `BLOCKED — ${g?.injection_category ?? "injection"}`
      : g?.pii_input === "redacted"
        ? "PII redacted"
        : "Passed",
    detail: (
      <dl>
        <CheckRow
          label="Prompt injection"
          pass={!injectionBlocked}
          verdict={injectionBlocked ? "✕ BLOCKED" : "✓ PASS"}
        />
        <CheckRow
          label="PII detection"
          pass={g?.pii_input !== "redacted"}
          verdict={g?.pii_input === "redacted" ? "⚠ REDACTED" : "✓ PASS"}
        />
        {g && g.pii_input_entities.length > 0 && (
          <DetailRow label="Entities" value={g.pii_input_entities.join(", ")} />
        )}
      </dl>
    ),
  });

  if (trace.route === "blocked") {
    steps.push({ id: "retrieval", title: "Retrieval", tone: "muted", summary: "SKIPPED" });
    steps.push({ id: "generation", title: "Claude", tone: "muted", summary: "NOT CALLED" });
    steps.push({
      id: "response",
      title: "Response",
      tone: "danger",
      summary: "Blocked",
      detail: "Request terminated before retrieval/generation. No Pinecone query, no Claude call.",
    });
    return steps;
  }

  if (trace.route === "uc2_transaction") {
    const txn = trace.transaction_lookup;
    steps.push({
      id: "txn_lookup",
      title: "Postgres Lookup",
      tone: txn?.found ? "success" : "danger",
      summary: txn?.found ? "Transaction found" : "Not found",
      detail: txn?.found ? (
        <dl>
          <DetailRow label="Transaction" value={txn.txn_id} />
          <DetailRow label="Status" value={txn.status} />
          {txn.error_code && <DetailRow label="Error code" value={txn.error_code} />}
          {txn.amount !== null && txn.currency && (
            <DetailRow label="Amount" value={formatAmount(txn.amount, txn.currency)} />
          )}
          <DetailRow
            label="Merchant scope"
            value={
              txn.merchant_scope_verified ? (
                <span className="text-ok">✓ Verified</span>
              ) : (
                "—"
              )
            }
          />
        </dl>
      ) : (
        "No transaction matched this ID for the current merchant scope."
      ),
    });

    if (injectionBlocked) {
      steps.push({
        id: "retrieval",
        title: "Retrieval",
        tone: "muted",
        summary: "SKIPPED",
        detail: "Answered from verified DB columns only.",
      });
      steps.push({
        id: "generation",
        title: "Claude",
        tone: "muted",
        summary: "NOT CALLED",
        detail:
          "Structured-field injection detected in the transaction description — the tainted text never reached the model.",
      });
      steps.push({
        id: "response",
        title: "Response",
        tone: "warning",
        summary: "Returned (DB fallback)",
      });
      return steps;
    }

    if (!txn?.found) {
      steps.push({ id: "generation", title: "Claude", tone: "muted", summary: "NOT CALLED" });
      steps.push({ id: "response", title: "Response", tone: "warning", summary: "Escalated" });
      return steps;
    }

    if (txn.error_code) {
      steps.push({
        id: "error_code",
        title: "Error Code Mapping",
        tone: "info",
        summary: txn.error_code,
      });
    }
  }

  if (trace.route === "out_of_scope") {
    steps.push({
      id: "generation",
      title: "Claude",
      tone: "muted",
      summary: "NOT CALLED",
      detail: "Query classified as outside this platform's docs/transactions/policy scope.",
    });
    steps.push({ id: "response", title: "Response", tone: "warning", summary: "Escalated" });
    return steps;
  }

  if (trace.retrieval) {
    const r = trace.retrieval;
    steps.push({
      id: "retrieval",
      title: "Pinecone Retrieval",
      tone: "info",
      summary: `${r.chunks_retrieved} chunk${r.chunks_retrieved === 1 ? "" : "s"}`,
      detail: r.chunks.length > 0 && (
        <ul className="space-y-1.5">
          {r.chunks.map((chunk, i) => (
            <li key={`${chunk.source_doc}-${i}`}>
              <details className="group/chunk rounded-lg border border-white/6 bg-white/3">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-3 py-2">
                  <span className="min-w-0">
                    <span className="block truncate font-mono text-xs text-ink">
                      {chunk.source_doc}
                    </span>
                    <span className="block truncate text-[11px] text-ink-faint">{chunk.section}</span>
                  </span>
                  <ScoreBar score={chunk.score} />
                </summary>
                <p className="border-t border-white/6 px-3 py-2.5 text-[12px] leading-relaxed text-ink-muted">
                  {chunk.snippet}
                  {chunk.snippet.length >= 280 ? "…" : ""}
                </p>
              </details>
            </li>
          ))}
        </ul>
      ),
    });
  }

  steps.push({ id: "generation", title: "Claude", tone: "success", summary: "Generated" });

  if (g?.faithfulness) {
    steps.push({
      id: "faithfulness",
      title: "Faithfulness",
      tone: g.faithfulness === "passed" ? "success" : "danger",
      summary: g.faithfulness === "passed" ? "Passed" : "Failed",
      detail:
        g.faithfulness === "passed"
          ? "Every claim in the answer was checked back against the retrieved context."
          : "At least one claim could not be traced to the retrieved context, so the answer was escalated instead of returned as grounded.",
    });
  }

  if (g?.pii_output) {
    steps.push({
      id: "pii_output",
      title: "PII Leak Detection",
      tone: g.pii_output === "passed" ? "success" : "warning",
      summary: g.pii_output === "passed" ? "Passed" : "Redacted",
      detail:
        g.pii_output_entities.length > 0 ? (
          <dl>
            <DetailRow label="Redacted" value={g.pii_output_entities.join(", ")} />
            <DetailRow label="Raw value" value="Never exposed" />
          </dl>
        ) : undefined,
    });
  }

  if (trace.confidence_gate === "escalated") {
    steps.push({
      id: "confidence_gate",
      title: "Confidence Gate",
      tone: "warning",
      summary: "ESCALATED",
      detail:
        "The model flagged its own answer as unsupported by retrieved context and declined to invent details.",
    });
  }

  steps.push({
    id: "response",
    title: "Response",
    tone: trace.escalated ? "warning" : "success",
    summary: trace.escalated ? "Escalated" : "Returned",
  });

  return steps;
}

export function PipelineTrace({ trace }: { trace: TraceResponse }) {
  const steps = buildSteps(trace);

  return (
    <ol>
      {steps.map((step, index) => (
        <PipelineNode
          key={step.id}
          index={index}
          isLast={index === steps.length - 1}
          title={step.title}
          tone={step.tone}
          summary={step.summary}
        >
          {step.detail}
        </PipelineNode>
      ))}
    </ol>
  );
}
