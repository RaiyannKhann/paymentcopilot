import { Info } from "@phosphor-icons/react/dist/ssr";

/** Required by frontendspec.md §13 — must stay visible on every surface and every
    breakpoint, so it lives in the main column rather than the desktop-only sidebar. */
export function DisclaimerBanner() {
  return (
    <div
      role="status"
      className="flex items-center justify-center gap-2 border-b border-white/6 bg-violet-deep/15 px-4 py-2 text-center"
    >
      <Info size={13} weight="fill" aria-hidden="true" className="shrink-0 text-violet-bright" />
      <p className="text-[11px] leading-snug text-ink-muted">
        Synthetic transaction and documentation data only — no real merchant, payment, or PII data.
      </p>
    </div>
  );
}
