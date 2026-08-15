interface PageHeaderProps {
  eyebrow: string;
  title: string;
  description: string;
  actions?: React.ReactNode;
}

export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-4 border-b border-white/6 pb-6">
      <div className="min-w-0">
        <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-violet-bright">
          {eyebrow}
        </p>
        <h1 className="text-gradient mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
          {title}
        </h1>
        <p className="mt-2 max-w-xl text-sm leading-relaxed text-ink-muted">{description}</p>
      </div>
      {actions}
    </header>
  );
}

/** Compact key/value tiles used for the trace summary strip. */
export function StatTile({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: React.ReactNode;
  tone?: "default" | "brand" | "ok" | "warn" | "bad";
}) {
  const valueTone = {
    default: "text-ink",
    brand: "text-violet-bright",
    ok: "text-ok",
    warn: "text-warn",
    bad: "text-bad",
  }[tone];

  return (
    <div className="glass-subtle rounded-xl px-3.5 py-3">
      <p className="text-[10px] font-medium uppercase tracking-[0.12em] text-ink-faint">{label}</p>
      <p className={`mt-1 truncate font-mono text-sm font-medium ${valueTone}`}>{value}</p>
    </div>
  );
}
