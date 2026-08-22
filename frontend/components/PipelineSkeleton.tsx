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
export function PipelineSkeleton() {
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
