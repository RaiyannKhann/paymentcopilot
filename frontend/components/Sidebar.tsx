"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChatCenteredDots, ShieldWarning, TreeStructure } from "@phosphor-icons/react/dist/ssr";
import { TRACES_CHANGED_EVENT, readRecentTraces } from "@/lib/traceStore";
import { formatLatency, routeCode } from "@/lib/format";
import type { TraceResponse } from "@/lib/types";
import { BrandMark } from "./BrandMark";
import { SystemStatus } from "./SystemStatus";

const LINKS = [
  {
    href: "/",
    label: "Support Console",
    hint: "Ask a question",
    icon: ChatCenteredDots,
  },
  {
    href: "/trace",
    label: "Request Trace",
    hint: "What the system did",
    icon: TreeStructure,
  },
  {
    href: "/attack-lab",
    label: "Attack Lab",
    hint: "Guardrails under attack",
    icon: ShieldWarning,
  },
];

export function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const [traces, setTraces] = useState<TraceResponse[]>([]);

  useEffect(() => {
    // sessionStorage is only readable post-mount; reading during render would desync
    // the server-rendered markup from the client's first paint.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTraces(readRecentTraces().slice(0, 5));

    const refresh = () => setTraces(readRecentTraces().slice(0, 5));
    window.addEventListener(TRACES_CHANGED_EVENT, refresh);
    return () => window.removeEventListener(TRACES_CHANGED_EVENT, refresh);
  }, [pathname]);

  return (
    <div className="flex h-full flex-col gap-6 overflow-y-auto px-4 py-5">
      <Link
        href="/"
        onClick={onNavigate}
        className="flex items-center gap-3 rounded-xl px-1 py-1 transition-opacity hover:opacity-90"
      >
        <BrandMark size={34} />
        <span className="min-w-0">
          <span className="block truncate text-sm font-semibold tracking-tight text-ink">
            Payment Copilot
          </span>
          <span className="block truncate text-[11px] text-ink-faint">Merchant support · demo</span>
        </span>
      </Link>

      <nav aria-label="Primary" className="flex flex-col gap-1">
        <p className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-ink-faint">
          Surfaces
        </p>
        {LINKS.map(({ href, label, hint, icon: IconComponent }) => {
          const isActive = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              onClick={onNavigate}
              aria-current={isActive ? "page" : undefined}
              className={`group relative flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors duration-200 ${
                isActive
                  ? "bg-violet/15 text-ink ring-1 ring-violet/35"
                  : "text-ink-muted hover:bg-white/5 hover:text-ink"
              }`}
            >
              {isActive && (
                <span
                  aria-hidden="true"
                  className="absolute left-0 top-1/2 h-6 w-0.5 -translate-y-1/2 rounded-full bg-violet-bright shadow-[0_0_10px_var(--color-violet)]"
                />
              )}
              <IconComponent
                size={18}
                weight={isActive ? "fill" : "regular"}
                aria-hidden="true"
                className={isActive ? "text-violet-bright" : "text-ink-faint group-hover:text-ink-muted"}
              />
              <span className="min-w-0">
                <span className="block truncate text-sm font-medium">{label}</span>
                <span className="block truncate text-[11px] text-ink-faint">{hint}</span>
              </span>
            </Link>
          );
        })}
      </nav>

      <div className="flex min-h-0 flex-col">
        <p className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-ink-faint">
          This session
        </p>
        {traces.length === 0 ? (
          <p className="rounded-xl border border-dashed border-line px-3 py-3 text-[11px] leading-relaxed text-ink-faint">
            Traces from your queries appear here.
          </p>
        ) : (
          <ul className="flex flex-col gap-1">
            {traces.map((trace) => {
              const isActive = pathname === `/trace/${trace.request_id}`;
              return (
                <li key={trace.request_id}>
                  <Link
                    href={`/trace/${trace.request_id}`}
                    onClick={onNavigate}
                    aria-current={isActive ? "page" : undefined}
                    className={`flex items-center justify-between gap-2 rounded-lg px-3 py-2 transition-colors ${
                      isActive ? "bg-white/8 text-ink" : "text-ink-muted hover:bg-white/5 hover:text-ink"
                    }`}
                  >
                    <span className="flex min-w-0 items-center gap-2">
                      <span className="shrink-0 rounded border border-line-strong px-1 font-mono text-[9px] text-ink-faint">
                        {routeCode(trace.route) ?? "—"}
                      </span>
                      <span className="truncate font-mono text-[11px]">{trace.request_id}</span>
                    </span>
                    <span className="shrink-0 font-mono text-[10px] text-ink-faint">
                      {formatLatency(trace.latency_ms)}
                    </span>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
        {traces.length > 0 && (
          <Link
            href="/trace"
            onClick={onNavigate}
            className="mt-1 rounded-lg px-3 py-1.5 text-[11px] text-violet-bright transition-colors hover:bg-white/5"
          >
            View all traces →
          </Link>
        )}
      </div>

      <div className="mt-auto flex flex-col gap-3 pt-2">
        <SystemStatus />
        <p className="px-1 text-[10px] leading-relaxed text-ink-faint">
          Routing, retrieval, and guardrails all execute on the real backend — nothing here is mocked.
        </p>
      </div>
    </div>
  );
}

export { LINKS as SIDEBAR_LINKS };
