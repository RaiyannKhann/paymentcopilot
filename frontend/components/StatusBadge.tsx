import {
  CheckCircle,
  CircleDashed,
  CircleNotch,
  Info,
  WarningCircle,
  XCircle,
} from "@phosphor-icons/react/dist/ssr";

export type StatusTone = "success" | "danger" | "warning" | "info" | "muted" | "loading" | "brand";

type IconComponentType = typeof CheckCircle;

const TONE_STYLES: Record<StatusTone, string> = {
  success: "text-ok bg-ok-dim border-ok/25",
  danger: "text-bad bg-bad-dim border-bad/25",
  warning: "text-warn bg-warn-dim border-warn/25",
  info: "text-info bg-info-dim border-info/25",
  brand: "text-violet-bright bg-violet/12 border-violet/30",
  muted: "text-ink-muted bg-white/4 border-white/10",
  loading: "text-violet-bright bg-violet/12 border-violet/30",
};

const TONE_ICON: Record<StatusTone, IconComponentType> = {
  success: CheckCircle,
  danger: XCircle,
  warning: WarningCircle,
  info: Info,
  brand: Info,
  muted: CircleDashed,
  loading: CircleNotch,
};

interface StatusBadgeProps {
  tone: StatusTone;
  children: React.ReactNode;
  /** Drops the icon for dense rows where the label alone carries the meaning. */
  bare?: boolean;
  className?: string;
}

export function StatusBadge({ tone, children, bare = false, className = "" }: StatusBadgeProps) {
  const IconComponent = TONE_ICON[tone];

  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-1 text-[11px] font-medium ${TONE_STYLES[tone]} ${className}`}
    >
      {!bare && (
        <IconComponent
          size={13}
          weight={tone === "loading" ? "bold" : "fill"}
          aria-hidden="true"
          className={tone === "loading" ? "animate-spin" : ""}
        />
      )}
      {children}
    </span>
  );
}
