"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CircleNotch, WarningOctagon } from "@phosphor-icons/react/dist/ssr";
import { getTrace, ApiError } from "@/lib/api";
import { readTrace, saveTrace } from "@/lib/traceStore";
import { ROUTE_META, formatLatency, routeLabel } from "@/lib/format";
import type { TraceResponse } from "@/lib/types";
import { PipelineTrace } from "@/components/PipelineTrace";
import { StatTile } from "@/components/PageHeader";
import { VoxelBackdrop } from "@/components/VoxelBackdrop";

export default function TraceDetailPage() {
  const params = useParams<{ requestId: string }>();
  const requestId = params.requestId;

  const [trace, setTrace] = useState<TraceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // sessionStorage is only available post-mount — reading it during render would
    // desync the server-rendered (empty) markup from the client's first paint.
    const local = readTrace(requestId);
    if (local) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setTrace(local);
      setLoading(false);
      return;
    }

    let cancelled = false;
    getTrace(requestId)
      .then((remote) => {
        if (cancelled) return;
        setTrace(remote);
        saveTrace(remote);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(
          err instanceof ApiError && err.status === 404
            ? "This trace is no longer available. Traces are kept for a short window after each request."
            : "Could not load this trace."
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [requestId]);

  const guardrailsClean =
    trace?.guardrails &&
    trace.guardrails.injection === "passed" &&
    trace.guardrails.pii_input === "passed" &&
    trace.guardrails.faithfulness !== "failed" &&
    trace.guardrails.pii_output !== "redacted";

  return (
    <div className="relative mx-auto w-full max-w-3xl px-4 py-10 pb-20 sm:px-6">
      <VoxelBackdrop />
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-xs text-ink-faint transition-colors hover:text-ink"
      >
        <ArrowLeft size={13} weight="bold" aria-hidden="true" />
        Back to Support Console
      </Link>

      <div className="mt-4 border-b border-white/6 pb-6">
        <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-violet-bright">
          Request Trace
        </p>
        <h1 className="mt-2 font-mono text-2xl font-semibold tracking-tight text-ink">
          {requestId}
        </h1>
        {trace && (
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-ink-muted">
            {ROUTE_META[trace.route]?.blurb ??
              "What the backend actually executed for this request."}
          </p>
        )}
      </div>

      {loading && (
        <div className="mt-8 flex items-center gap-2 text-sm text-ink-muted">
          <CircleNotch size={16} weight="bold" aria-hidden="true" className="animate-spin" />
          Loading trace…
        </div>
      )}

      {!loading && error && (
        <div
          role="alert"
          className="mt-8 flex items-start gap-3 rounded-panel border border-bad/25 bg-bad-dim px-5 py-4"
        >
          <WarningOctagon
            size={18}
            weight="fill"
            aria-hidden="true"
            className="mt-0.5 shrink-0 text-bad"
          />
          <p className="text-sm leading-relaxed text-ink-muted">{error}</p>
        </div>
      )}

      {!loading && !error && trace && (
        <>
          <div className="mt-6 grid grid-cols-2 gap-2.5 sm:grid-cols-4">
            <StatTile label="Route" value={routeLabel(trace.route)} tone="brand" />
            <StatTile label="Latency" value={formatLatency(trace.latency_ms)} />
            <StatTile label="Cache" value={trace.cache_hit ? "HIT" : "MISS"} />
            <StatTile
              label="Guardrails"
              value={guardrailsClean ? "All passed" : "Action taken"}
              tone={guardrailsClean ? "ok" : "warn"}
            />
          </div>

          <p className="mt-8 mb-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-ink-faint">
            Execution path — expand any stage
          </p>
          <PipelineTrace trace={trace} />
        </>
      )}
    </div>
  );
}
