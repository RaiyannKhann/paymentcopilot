"use client";

import {
  Database,
  IdentificationBadge,
  IdentificationCard,
  MaskHappy,
  SealQuestion,
  TerminalWindow,
  UsersThree,
  Warning,
} from "@phosphor-icons/react/dist/ssr";
import type { AttackCase } from "@/lib/types";

type IconComponentType = typeof Warning;

const CATEGORY_ICON: Record<string, IconComponentType> = {
  instruction_override: TerminalWindow,
  jailbreak: MaskHappy,
  cross_tenant_exfiltration: UsersThree,
  structured_field_injection: Database,
  pii_in_query: IdentificationCard,
  pii_in_structured_field: IdentificationBadge,
  policy_gap: SealQuestion,
};

interface AttackCaseGridProps {
  cases: AttackCase[];
  selectedId: string | null;
  onSelect: (attackId: string) => void;
}

export function AttackCaseGrid({ cases, selectedId, onSelect }: AttackCaseGridProps) {
  return (
    <div role="group" aria-label="Attack categories" className="grid gap-2.5 sm:grid-cols-2">
      {cases.map((attackCase) => {
        const isSelected = attackCase.attack_id === selectedId;
        const IconComponent = CATEGORY_ICON[attackCase.category] ?? Warning;

        return (
          <button
            key={attackCase.attack_id}
            type="button"
            aria-pressed={isSelected}
            onClick={() => onSelect(attackCase.attack_id)}
            className={`group flex cursor-pointer items-start gap-3 rounded-xl border p-3.5 text-left transition-all duration-200 ${
              isSelected
                ? "border-violet/50 bg-violet/12 shadow-[var(--shadow-glow)]"
                : "border-white/8 bg-white/3 hover:border-white/16 hover:bg-white/6"
            }`}
          >
            <span
              className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg border transition-colors ${
                isSelected
                  ? "border-violet/45 bg-violet/20 text-violet-bright"
                  : "border-white/8 bg-white/4 text-ink-faint group-hover:text-ink-muted"
              }`}
            >
              <IconComponent size={16} weight="fill" aria-hidden="true" />
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-medium text-ink">{attackCase.label}</span>
              <span className="mt-0.5 block text-xs leading-relaxed text-ink-muted">
                {attackCase.description}
              </span>
              <span className="mt-1.5 block font-mono text-[10px] text-ink-faint">
                {attackCase.category}
              </span>
            </span>
          </button>
        );
      })}
    </div>
  );
}
