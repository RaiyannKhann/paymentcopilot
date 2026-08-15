"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, TreeStructure } from "@phosphor-icons/react/dist/ssr";
import { readRecentTraces } from "@/lib/traceStore";
import { formatLatency, routeCode, routeLabel } from "@/lib/format";
import type { TraceResponse } from "@/lib/types";
import { PageHeader } from "@/components/PageHeader";
import { StatusBadge } from "@/components/StatusBadge";

export default function TraceIndexPage() {
  const [traces, setTraces] = useState<TraceResponse[]>([]);

  useEffect(() => {
    // sessionStorage is only available post-mount — reading it during render would
    // desync the server-rendered (empty) markup from the client's first paint.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTraces(readRecentTraces());
  }, []);

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10 pb-20 sm:px-6">
      <PageHeader
        eyebrow="Observability"
        title="Request Trace"
        description="Every Support Console query records what the system actually did — rate limit, semantic cache, router, guardrails, retrieval, and generation. Not model reasoning: real execution."
      />

      {traces.length === 0 ? (
        <div className="mt-8 flex flex-col items-center gap-4 rounded-panel border border-dashed border-line px-6 py-16 text-center">
          <span className="grid h-12 w-12 place-items-center rounded-full border border-violet/25 bg-violet/10">
            <TreeStructure size={22} weight="regular" aria-hidden="true" className="text-violet-bright" />
          </span>
          <div>
            <p className="text-sm font-medium text-ink">No traces yet this session</p>
            <p className="mt-1 text-sm text-ink-muted">
              Ask a question in the Support Console to generate one.
            </p>
          </div>
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 rounded-lg border border-violet/35 bg-violet/12 px-4 py-2.5 text-sm font-medium text-violet-bright transition-colors hover:bg-violet/20"
          >
            Open Support Console
            <ArrowRight size={15} weight="bold" aria-hidden="true" />
          </Link>
        </div>
      ) : (
        <ul className="mt-6 space-y-2">
          {traces.map((trace) => (
            <li key={trace.request_id}>
              <Link
                href={`/trace/${trace.request_id}`}
                className="glass-subtle group flex flex-wrap items-center justify-between gap-3 rounded-xl px-4 py-3.5 transition-all duration-200 hover:border-violet/35 hover:bg-violet/8"
              >
                <span className="flex min-w-0 flex-wrap items-center gap-2.5">
                  <span className="rounded-md bg-violet/20 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-violet-bright ring-1 ring-violet/30">
                    {routeCode(trace.route) ?? "—"}
                  </span>
                  <span className="text-sm font-medium text-ink">{routeLabel(trace.route)}</span>
                  <span className="truncate font-mono text-[11px] text-ink-faint">
                    {trace.request_id}
                  </span>
                </span>
                <span className="flex items-center gap-2">
                  {trace.cache_hit && (
                    <StatusBadge tone="muted" bare>
                      cache hit
                    </StatusBadge>
                  )}
                  {trace.escalated && <StatusBadge tone="warning">Escalated</StatusBadge>}
                  <span className="font-mono text-[11px] text-ink-faint">
                    {formatLatency(trace.latency_ms)}
                  </span>
                  <ArrowRight
                    size={14}
                    weight="bold"
                    aria-hidden="true"
                    className="text-ink-faint transition-transform duration-200 group-hover:translate-x-0.5 group-hover:text-violet-bright"
                  />
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
