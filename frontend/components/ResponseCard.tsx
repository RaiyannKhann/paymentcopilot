import Link from "next/link";
import { ArrowRight, FileText, ShieldCheck } from "@phosphor-icons/react/dist/ssr";
import type { QueryResponse } from "@/lib/types";
import { ROUTE_META, formatLatency, routeCode, routeLabel } from "@/lib/format";
import { StatusBadge } from "./StatusBadge";
import { AnswerText } from "./AnswerText";

export function ResponseCard({ response }: { response: QueryResponse }) {
  const guardrailsPassed = response.guardrail_status === "passed";
  const meta = ROUTE_META[response.source_route];
  const code = routeCode(response.source_route);

  return (
    <article className="glass animate-rise overflow-hidden rounded-panel">
      {/* Route strip — the answer's provenance reads before the answer itself. */}
      <header className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-white/6 bg-violet-deep/12 px-5 py-3">
        <span className="inline-flex items-center gap-2">
          {code && code !== "—" && (
            <span className="rounded-md bg-violet/20 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-violet-bright ring-1 ring-violet/30">
              {code}
            </span>
          )}
          <span className="text-sm font-semibold text-ink">{routeLabel(response.source_route)}</span>
        </span>
        {meta && <span className="hidden text-xs text-ink-faint sm:inline">{meta.blurb}</span>}
        <span className="ml-auto font-mono text-[10px] text-ink-faint">{response.request_id}</span>
      </header>

      <div className="px-5 py-5 sm:px-6">
        <AnswerText text={response.answer} />

        <div className="mt-5 flex flex-wrap items-center gap-2">
          {response.escalated ? (
            <StatusBadge tone="warning">Escalated to a human</StatusBadge>
          ) : (
            <StatusBadge tone="success">Grounded in retrieved sources</StatusBadge>
          )}
          {guardrailsPassed ? (
            <StatusBadge tone="success">Safety checks passed</StatusBadge>
          ) : (
            <StatusBadge tone="warning">Guardrail action taken</StatusBadge>
          )}
          <StatusBadge tone="muted" bare>
            {formatLatency(response.trace.latency_ms)}
          </StatusBadge>
        </div>
      </div>

      {response.grounding_refs.length > 0 && (
        <div className="border-t border-white/6 px-5 py-4 sm:px-6">
          <h3 className="mb-2.5 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-[0.14em] text-ink-faint">
            <FileText size={13} weight="fill" aria-hidden="true" />
            Grounded in
          </h3>
          <ul className="flex flex-wrap gap-2">
            {response.grounding_refs.map((ref) => (
              <li
                key={ref}
                className="rounded-lg border border-white/8 bg-white/4 px-2.5 py-1.5 font-mono text-[11px] text-ink-muted"
              >
                {ref}
              </li>
            ))}
          </ul>
        </div>
      )}

      <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-white/6 bg-white/2 px-5 py-3.5 sm:px-6">
        <span className="inline-flex items-center gap-1.5 text-[11px] text-ink-faint">
          <ShieldCheck size={14} weight="fill" aria-hidden="true" className="text-ok" />
          Rate limit, cache, router, and guardrails all ran server-side
        </span>
        <Link
          href={`/trace/${response.request_id}`}
          className="inline-flex items-center gap-1.5 rounded-lg border border-violet/35 bg-violet/12 px-3.5 py-2 text-sm font-medium text-violet-bright transition-colors hover:bg-violet/20"
        >
          View system trace
          <ArrowRight size={15} weight="bold" aria-hidden="true" />
        </Link>
      </footer>
    </article>
  );
}
