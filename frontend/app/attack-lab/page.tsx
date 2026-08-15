"use client";

import { useEffect, useMemo, useState } from "react";
import { CircleNotch, Play, WarningOctagon } from "@phosphor-icons/react/dist/ssr";
import { getAttackCases, runAttackCase, ApiError } from "@/lib/api";
import type { AttackCase, AttackRunResult } from "@/lib/types";
import { AttackCaseGrid } from "@/components/AttackCaseGrid";
import { AttackResultPanel } from "@/components/AttackResultPanel";
import { PageHeader } from "@/components/PageHeader";

export default function AttackLabPage() {
  const [cases, setCases] = useState<AttackCase[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [result, setResult] = useState<AttackRunResult | null>(null);
  const [loadingCases, setLoadingCases] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAttackCases()
      .then(({ cases: fetched }) => setCases(fetched))
      .catch(() => setError("Could not load Attack Lab cases. Is the backend running?"))
      .finally(() => setLoadingCases(false));
  }, []);

  const primaryCases = useMemo(() => cases.filter((c) => !c.secondary_of), [cases]);
  const secondaryCase = useMemo(
    () => cases.find((c) => c.secondary_of === selectedId) ?? null,
    [cases, selectedId]
  );
  const selectedCase = useMemo(
    () => cases.find((c) => c.attack_id === selectedId) ?? null,
    [cases, selectedId]
  );

  async function run(attackId: string) {
    setRunning(true);
    setError(null);
    try {
      const runResult = await runAttackCase(attackId);
      setResult(runResult);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong running this test.");
    } finally {
      setRunning(false);
    }
  }

  function handleSelect(attackId: string) {
    setSelectedId(attackId);
    setResult(null);
    setError(null);
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10 pb-20 sm:px-6">
      <PageHeader
        eyebrow="Security"
        title="Guardrail Attack Lab"
        description="Curated adversarial payloads, stored server-side, run through the real input guardrail pipeline. Nothing here reaches Claude — a passing guardrail stops the run and reports it."
      />

      {loadingCases ? (
        <div className="mt-8 flex items-center gap-2 text-sm text-ink-muted">
          <CircleNotch size={16} weight="bold" aria-hidden="true" className="animate-spin" />
          Loading attack cases…
        </div>
      ) : (
        <div className="mt-6">
          <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-ink-faint">
            Choose an attack
          </p>
          <AttackCaseGrid cases={primaryCases} selectedId={selectedId} onSelect={handleSelect} />
        </div>
      )}

      {!loadingCases && primaryCases.length > 0 && (
        <div className="glass-subtle mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl px-4 py-3">
          <p className="text-xs text-ink-muted">
            {selectedCase ? (
              <>
                Ready to run{" "}
                <span className="font-mono text-ink">{selectedCase.attack_id}</span> against the
                live guardrails.
              </>
            ) : (
              "Select an attack category to run it."
            )}
          </p>
          <button
            type="button"
            disabled={!selectedId || running}
            onClick={() => selectedId && run(selectedId)}
            className="inline-flex min-h-11 cursor-pointer items-center justify-center gap-2 rounded-lg bg-violet px-5 text-sm font-semibold text-on-violet shadow-[0_8px_24px_-8px_rgba(139,92,246,0.9)] transition-all duration-200 hover:bg-violet-bright disabled:cursor-not-allowed disabled:bg-white/8 disabled:text-ink-faint disabled:shadow-none"
          >
            {running ? (
              <>
                <CircleNotch size={15} weight="bold" aria-hidden="true" className="animate-spin" />
                Running…
              </>
            ) : (
              <>
                <Play size={15} weight="fill" aria-hidden="true" />
                Run test
              </>
            )}
          </button>
        </div>
      )}

      <div className="mt-6" aria-live="polite" aria-busy={running}>
        {error && (
          <div
            role="alert"
            className="flex items-start gap-3 rounded-panel border border-bad/25 bg-bad-dim px-5 py-4"
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
        {result && !error && (
          <AttackResultPanel
            result={result}
            onRunSecondary={secondaryCase ? () => run(secondaryCase.attack_id) : undefined}
            secondaryLabel={secondaryCase?.label}
          />
        )}
      </div>
    </div>
  );
}
