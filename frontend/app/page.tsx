"use client";

import { useState } from "react";
import { ArrowCounterClockwise, WarningOctagon } from "@phosphor-icons/react/dist/ssr";
import { postQuery, ApiError } from "@/lib/api";
import { saveTrace } from "@/lib/traceStore";
import type { QueryResponse } from "@/lib/types";
import { ResponseCard } from "@/components/ResponseCard";
import { PromptComposer } from "@/components/PromptComposer";
import { CapabilityCards } from "@/components/CapabilityCards";
import { Orb } from "@/components/Orb";

const TENANT_ID = process.env.NEXT_PUBLIC_DEMO_TENANT_ID ?? "demo-merchant";

export default function SupportConsolePage() {
  const [query, setQuery] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [asked, setAsked] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runQuery(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setError(null);
    setAsked(trimmed);
    try {
      const result = await postQuery({
        tenant_id: TENANT_ID,
        query: trimmed,
        session_id: sessionId,
      });
      setResponse(result);
      setSessionId(result.session_id);
      saveTrace(result.trace);
      setQuery("");
    } catch (err) {
      setResponse(null);
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  // Once there's a result, the hero steps aside so the answer owns the viewport.
  const isLanding = !response && !error && !loading;

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-20 sm:px-6">
      {isLanding ? (
        <section className="flex flex-col items-center pt-14 text-center sm:pt-20">
          <Orb size={104} />
          <h1 className="text-gradient mt-8 text-3xl font-semibold tracking-tight sm:text-[2.6rem] sm:leading-[1.1]">
            How can I help?
          </h1>
          <p className="mt-3 max-w-md text-sm leading-relaxed text-ink-muted">
            Ask about your integration, a specific transaction, or platform policy. Every answer is
            grounded, guardrailed, and fully traceable.
          </p>
        </section>
      ) : (
        <section className="flex items-center gap-3 pt-8">
          <Orb size={40} active={loading} />
          <div className="min-w-0">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-ink-faint">
              {loading ? "Running the pipeline" : "You asked"}
            </p>
            <p className="truncate text-sm text-ink">{asked}</p>
          </div>
          <button
            type="button"
            onClick={() => {
              setResponse(null);
              setError(null);
              setAsked(null);
              setQuery("");
            }}
            className="ml-auto inline-flex shrink-0 cursor-pointer items-center gap-1.5 rounded-lg border border-white/10 px-3 py-2 text-xs text-ink-muted transition-colors hover:bg-white/5 hover:text-ink"
          >
            <ArrowCounterClockwise size={13} weight="bold" aria-hidden="true" />
            New question
          </button>
        </section>
      )}

      <div className="mt-8">
        <PromptComposer
          value={query}
          onChange={setQuery}
          onSubmit={() => void runQuery(query)}
          loading={loading}
        />
      </div>

      {isLanding && (
        <div className="mt-4">
          <CapabilityCards onPick={setQuery} />
        </div>
      )}

      <div className="mt-6" aria-live="polite" aria-busy={loading}>
        {loading && <PipelineSkeleton />}

        {!loading && error && (
          <div
            role="alert"
            className="animate-rise flex items-start gap-3 rounded-panel border border-bad/25 bg-bad-dim px-5 py-4"
          >
            <WarningOctagon
              size={18}
              weight="fill"
              aria-hidden="true"
              className="mt-0.5 shrink-0 text-bad"
            />
            <div>
              <p className="text-sm font-medium text-bad">Request failed</p>
              <p className="mt-1 text-sm leading-relaxed text-ink-muted">{error}</p>
            </div>
          </div>
        )}

        {!loading && !error && response && <ResponseCard response={response} />}
      </div>
    </div>
  );
}

const PIPELINE_STAGES = [
  "Rate limit",
  "Semantic cache",
  "Query router",
  "Input guardrails",
  "Retrieval",
  "Generation",
];

/** Names the stages actually running rather than showing an anonymous spinner — the
    wait is where the backend's depth is most worth advertising. */
function PipelineSkeleton() {
  return (
    <div className="glass animate-rise rounded-panel px-5 py-5 sm:px-6">
      <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-ink-faint">
        Executing
      </p>
      <ul className="mt-3 flex flex-wrap gap-x-2 gap-y-2">
        {PIPELINE_STAGES.map((stage, index) => (
          <li key={stage} className="flex items-center gap-2">
            <span
              className="rounded-lg border border-white/8 bg-white/4 px-2.5 py-1.5 font-mono text-[11px] text-ink-muted"
              style={{ animation: `rise 0.4s var(--ease-out-soft) ${index * 0.08}s both` }}
            >
              {stage}
            </span>
            {index < PIPELINE_STAGES.length - 1 && (
              <span aria-hidden="true" className="text-ink-faint">
                ›
              </span>
            )}
          </li>
        ))}
      </ul>
      <div className="mt-4 h-1 overflow-hidden rounded-full bg-white/6">
        <div className="h-full w-1/3 animate-pulse rounded-full bg-violet" />
      </div>
    </div>
  );
}
