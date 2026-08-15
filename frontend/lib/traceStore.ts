// Client-side cache of recent traces, keyed by request_id. Populated right after a
// /query response so "View System Trace" navigates instantly without a round trip.
// The Trace page falls back to GET /trace/{id} (backend-persisted, ~15 min TTL) when
// a trace isn't in this session's cache — e.g. a direct link or a page refresh.
import type { TraceResponse } from "./types";

const STORAGE_KEY = "paymentcopilot:traces";
const MAX_ENTRIES = 20;

// sessionStorage fires no event in the tab that wrote it, so the sidebar's session list
// would go stale after a query answered on the page it's already on.
export const TRACES_CHANGED_EVENT = "paymentcopilot:traces-changed";

function readAll(): Record<string, TraceResponse> {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Record<string, TraceResponse>) : {};
  } catch {
    return {};
  }
}

export function saveTrace(trace: TraceResponse): void {
  if (typeof window === "undefined") return;
  const all = readAll();
  all[trace.request_id] = trace;
  const entries = Object.entries(all);
  const trimmed =
    entries.length > MAX_ENTRIES ? entries.slice(entries.length - MAX_ENTRIES) : entries;
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(Object.fromEntries(trimmed)));
  } catch {
    // sessionStorage full/unavailable — trace is still recoverable via GET /trace/{id}
  }
  window.dispatchEvent(new Event(TRACES_CHANGED_EVENT));
}

export function readTrace(requestId: string): TraceResponse | null {
  return readAll()[requestId] ?? null;
}

export function readRecentTraces(): TraceResponse[] {
  return Object.values(readAll()).reverse();
}
