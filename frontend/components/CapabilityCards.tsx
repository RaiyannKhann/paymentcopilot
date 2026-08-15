"use client";

import { BookOpen, Receipt, Scales } from "@phosphor-icons/react/dist/ssr";

interface Capability {
  code: string;
  title: string;
  description: string;
  example: string;
  icon: typeof BookOpen;
}

const CAPABILITIES: Capability[] = [
  {
    code: "UC1",
    title: "Documentation",
    description: "Integration questions answered from the indexed docs, with the sources cited.",
    example: "How do I verify a webhook signature?",
    icon: BookOpen,
  },
  {
    code: "UC2",
    title: "Transactions",
    description: "Looks up the real record, maps the error code, and explains the failure.",
    example: "Why did txn_28131 fail?",
    icon: Receipt,
  },
  {
    code: "UC3",
    title: "Policy",
    description: "Answers what policy supports — and refuses, rather than guessing, when it doesn't.",
    example: "Can I refund this transaction after 90 days?",
    icon: Scales,
  },
];

/** The three routes the backend can take, presented as the way in. Picking one fills
    the composer, so the demo path is one click from the landing state. */
export function CapabilityCards({ onPick }: { onPick: (query: string) => void }) {
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {CAPABILITIES.map(({ code, title, description, example, icon: IconComponent }) => (
        <button
          key={code}
          type="button"
          onClick={() => onPick(example)}
          className="glass-subtle group flex cursor-pointer flex-col gap-2 rounded-xl p-4 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-violet/40 hover:bg-violet/8"
        >
          <span className="flex items-center gap-2">
            <IconComponent
              size={16}
              weight="fill"
              aria-hidden="true"
              className="text-violet-bright"
            />
            <span className="text-sm font-semibold text-ink">{title}</span>
            <span className="ml-auto font-mono text-[10px] text-ink-faint">{code}</span>
          </span>
          <span className="text-xs leading-relaxed text-ink-muted">{description}</span>
          <span className="mt-auto truncate pt-1 font-mono text-[11px] text-ink-faint transition-colors group-hover:text-violet-bright">
            “{example}”
          </span>
        </button>
      ))}
    </div>
  );
}

export { CAPABILITIES };
