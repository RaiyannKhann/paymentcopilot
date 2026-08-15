export interface RouteMeta {
  label: string;
  /** Use-case code as the backend names it — shown alongside the human label so the
      demo makes the UC1/UC2/UC3 routing in frontendspec.md legible. */
  code: string;
  blurb: string;
}

export const ROUTE_META: Record<string, RouteMeta> = {
  uc1_docs: {
    label: "Documentation",
    code: "UC1",
    blurb: "Answered from the indexed integration docs.",
  },
  uc2_transaction: {
    label: "Transaction",
    code: "UC2",
    blurb: "Answered from a verified transaction record plus error-code docs.",
  },
  uc3_policy: {
    label: "Policy",
    code: "UC3",
    blurb: "Checked against platform policy; refuses where policy has no support.",
  },
  out_of_scope: {
    label: "Out of scope",
    code: "—",
    blurb: "Outside docs, transactions, and policy — escalated instead of guessed.",
  },
  blocked: {
    label: "Blocked",
    code: "—",
    blurb: "Stopped by an input guardrail before retrieval or generation.",
  },
};

export function routeLabel(route: string): string {
  return ROUTE_META[route]?.label ?? route;
}

export function routeCode(route: string): string | null {
  return ROUTE_META[route]?.code ?? null;
}

// Amounts are stored in the smallest currency unit (PRD convention — e.g. paise, cents).
export function formatAmount(amount: number, currency: string): string {
  try {
    return new Intl.NumberFormat("en-IN", { style: "currency", currency }).format(amount / 100);
  } catch {
    return `${(amount / 100).toFixed(2)} ${currency}`;
  }
}

export function formatLatency(ms: number): string {
  return ms < 1000 ? `${Math.round(ms)}ms` : `${(ms / 1000).toFixed(2)}s`;
}
