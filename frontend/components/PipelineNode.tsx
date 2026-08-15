import { CaretDown } from "@phosphor-icons/react/dist/ssr";
import { StatusBadge, type StatusTone } from "./StatusBadge";

interface PipelineNodeProps {
  title: string;
  tone: StatusTone;
  summary: string;
  /** Ordinal shown on the rail — makes the execution order explicit at a glance. */
  index: number;
  isLast: boolean;
  children?: React.ReactNode;
}

const DOT_TONE: Record<StatusTone, string> = {
  success: "border-ok/60 bg-ok/20 text-ok",
  danger: "border-bad/60 bg-bad/20 text-bad",
  warning: "border-warn/60 bg-warn/20 text-warn",
  info: "border-info/60 bg-info/20 text-info",
  brand: "border-violet/60 bg-violet/20 text-violet-bright",
  muted: "border-line-strong bg-panel text-ink-faint",
  loading: "border-violet/60 bg-violet/20 text-violet-bright",
};

export function PipelineNode({ title, tone, summary, index, isLast, children }: PipelineNodeProps) {
  const hasDetail = Boolean(children);

  return (
    <li className="relative pl-11">
      {!isLast && (
        <span
          aria-hidden="true"
          className="absolute left-[13px] top-7 bottom-0 w-px bg-gradient-to-b from-line-strong to-line"
        />
      )}
      <span
        aria-hidden="true"
        className={`absolute left-0 top-2 grid h-[27px] w-[27px] place-items-center rounded-full border font-mono text-[10px] font-semibold ${DOT_TONE[tone]}`}
      >
        {index + 1}
      </span>

      <details className="glass-subtle group mb-2.5 overflow-hidden rounded-xl transition-colors open:bg-white/6">
        <summary
          className={`flex list-none items-center justify-between gap-3 px-4 py-2.5 ${
            hasDetail ? "cursor-pointer hover:bg-white/4" : "cursor-default"
          }`}
        >
          <span className="flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1.5">
            <span className="font-mono text-[13px] font-medium text-ink">{title}</span>
            <StatusBadge tone={tone}>{summary}</StatusBadge>
          </span>
          {hasDetail && (
            <CaretDown
              size={14}
              weight="bold"
              aria-hidden="true"
              className="shrink-0 text-ink-faint transition-transform duration-200 group-open:rotate-180"
            />
          )}
        </summary>
        {hasDetail && (
          <div className="border-t border-white/6 px-4 py-3 text-[13px] leading-relaxed text-ink-muted">
            {children}
          </div>
        )}
      </details>
    </li>
  );
}
