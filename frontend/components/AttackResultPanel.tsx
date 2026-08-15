import {
  ArrowRight,
  ClockCounterClockwise,
  Prohibit,
  ShieldCheck,
  WarningDiamond,
} from "@phosphor-icons/react/dist/ssr";
import type { AttackRunResult } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

interface AttackResultPanelProps {
  result: AttackRunResult;
  onRunSecondary?: () => void;
  secondaryLabel?: string;
}

/** A pipeline step is "negative" when it records something the system refused to do —
    those read struck-through so "no Claude call" doesn't look like a step that ran. */
function stepTone(step: string): "block" | "negative" | "normal" {
  const trimmed = step.trim();
  // Only the bare verdict token is the stop marker — a descriptive step that merely
  // mentions redaction ("Redacted text only reaches downstream steps") is not.
  if (/^(BLOCK|BLOCKED|REDACT|REDACTED)$/i.test(trimmed)) return "block";
  const upper = trimmed.toUpperCase();
  if (upper.startsWith("NO ") || upper.includes("NOT CALLED") || upper.includes("SKIPPED")) {
    return "negative";
  }
  return "normal";
}

export function AttackResultPanel({ result, onRunSecondary, secondaryLabel }: AttackResultPanelProps) {
  const held = result.blocked;

  return (
    <section
      className={`glass animate-rise overflow-hidden rounded-panel ${
        held ? "" : "border-warn/30"
      }`}
    >
      <header
        className={`flex flex-wrap items-center gap-3 border-b px-5 py-4 ${
          held ? "border-ok/20 bg-ok-dim/60" : "border-warn/25 bg-warn-dim/60"
        }`}
      >
        <span
          className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl border ${
            held ? "border-ok/35 bg-ok/15 text-ok" : "border-warn/35 bg-warn/15 text-warn"
          }`}
        >
          {held ? (
            <ShieldCheck size={20} weight="fill" aria-hidden="true" />
          ) : (
            <WarningDiamond size={20} weight="fill" aria-hidden="true" />
          )}
        </span>
        <span className="min-w-0">
          <span
            className={`block text-base font-semibold ${held ? "text-ok" : "text-warn"}`}
          >
            {held ? "Attack blocked" : "Guardrail did not block this test"}
          </span>
          <span className="block font-mono text-[11px] text-ink-faint">{result.category}</span>
        </span>
        {result.mode === "recorded" && (
          <span className="ml-auto inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/4 px-2.5 py-1 text-[11px] text-ink-muted">
            <ClockCounterClockwise size={12} weight="bold" aria-hidden="true" />
            Recorded — not executed live
          </span>
        )}
      </header>

      <div className="grid gap-5 px-5 py-5 sm:px-6 md:grid-cols-[1fr_auto] md:gap-8">
        <div className="min-w-0">
          <dl className="space-y-3">
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-[0.12em] text-ink-faint">
                Guardrail
              </dt>
              <dd className="mt-1 font-mono text-sm text-ink">{result.guardrail}</dd>
            </div>
            <div>
              <dt className="text-[10px] font-semibold uppercase tracking-[0.12em] text-ink-faint">
                Action
              </dt>
              <dd className="mt-1 text-sm text-ink">{result.action}</dd>
            </div>
          </dl>

          <p className="mt-4 text-sm leading-relaxed text-ink-muted">{result.detail}</p>

          {result.entities_found.length > 0 && (
            <div className="mt-4 rounded-xl border border-warn/20 bg-warn-dim/50 px-3.5 py-3">
              {/* The backend's `action`/`detail` already narrate what happened, so this
                  block stays to the entity types themselves. */}
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-ink-faint">
                Entity types detected
              </p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {result.entities_found.map((entity) => (
                  <StatusBadge key={entity} tone="warning">
                    {entity}
                  </StatusBadge>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="md:w-52">
          <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-ink-faint">
            Pipeline
          </p>
          <ol className="mt-3 space-y-0">
            {result.pipeline.map((step, i) => {
              const tone = stepTone(step);
              const isLast = i === result.pipeline.length - 1;
              return (
                <li key={`${step}-${i}`} className="relative pl-6">
                  {!isLast && (
                    <span
                      aria-hidden="true"
                      className="absolute left-[5px] top-5 h-[calc(100%-0.75rem)] w-px bg-line-strong"
                    />
                  )}
                  <span
                    aria-hidden="true"
                    className={`absolute left-0 top-2 grid h-[11px] w-[11px] place-items-center rounded-full border ${
                      tone === "block"
                        ? "border-bad bg-bad/30"
                        : tone === "negative"
                          ? "border-line-strong bg-panel"
                          : "border-violet/60 bg-violet/25"
                    }`}
                  />
                  <span
                    className={`block pb-3 font-mono text-[11px] leading-5 ${
                      tone === "block"
                        ? "font-semibold text-bad"
                        : tone === "negative"
                          ? "text-ink-faint line-through decoration-ink-faint/50"
                          : "text-ink-muted"
                    }`}
                  >
                    {step}
                  </span>
                </li>
              );
            })}
          </ol>
        </div>
      </div>

      <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-white/6 bg-white/2 px-5 py-3.5 sm:px-6">
        <span className="inline-flex items-center gap-1.5 text-[11px] text-ink-faint">
          <Prohibit size={13} weight="bold" aria-hidden="true" />
          Curated server-side payload — the public Attack Lab never invokes Claude.
        </span>
        {onRunSecondary && (
          <button
            type="button"
            onClick={onRunSecondary}
            className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-violet/35 bg-violet/12 px-3.5 py-2 text-sm font-medium text-violet-bright transition-colors hover:bg-violet/20"
          >
            Also test: {secondaryLabel}
            <ArrowRight size={14} weight="bold" aria-hidden="true" />
          </button>
        )}
      </footer>
    </section>
  );
}
