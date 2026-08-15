"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";
import type { HealthResponse } from "@/lib/types";

type State = { kind: "loading" } | { kind: "unreachable" } | { kind: "ready"; health: HealthResponse };

const DOT_CLASS: Record<string, string> = {
  ok: "bg-ok shadow-[0_0_8px_var(--color-ok)]",
  degraded: "bg-warn shadow-[0_0_8px_var(--color-warn)]",
  offline: "bg-bad shadow-[0_0_8px_var(--color-bad)]",
  loading: "bg-ink-faint",
};

/** Live backend dependency health from GET /health — the console's "is the system up"
    readout, not a decorative badge. */
export function SystemStatus() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;

    function poll() {
      getHealth()
        .then((health) => !cancelled && setState({ kind: "ready", health }))
        .catch(() => !cancelled && setState({ kind: "unreachable" }));
    }

    poll();
    const timer = window.setInterval(poll, 30_000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  const overall =
    state.kind === "loading" ? "loading" : state.kind === "unreachable" ? "offline" : state.health.status;

  const label =
    state.kind === "loading"
      ? "Checking backend…"
      : state.kind === "unreachable"
        ? "Backend unreachable"
        : state.health.status === "ok"
          ? "All systems operational"
          : "Degraded";

  return (
    <div className="glass-subtle rounded-xl px-3 py-2.5">
      <div className="flex items-center gap-2">
        <span
          aria-hidden="true"
          className={`h-1.5 w-1.5 shrink-0 rounded-full ${DOT_CLASS[overall] ?? DOT_CLASS.loading}`}
        />
        <span className="truncate text-[11px] font-medium text-ink-muted">{label}</span>
      </div>

      {state.kind === "ready" && (
        <dl className="mt-2 space-y-1">
          {Object.entries(state.health.checks).map(([name, value]) => (
            <div key={name} className="flex items-center justify-between gap-2">
              <dt className="font-mono text-[10px] uppercase tracking-wider text-ink-faint">{name}</dt>
              <dd
                className={`font-mono text-[10px] ${value === "ok" ? "text-ok" : "text-bad"}`}
              >
                {value}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}
