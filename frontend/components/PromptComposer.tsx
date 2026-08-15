"use client";

import type { FormEvent, KeyboardEvent } from "react";
import { ArrowUp, CircleNotch } from "@phosphor-icons/react/dist/ssr";

interface PromptComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  loading: boolean;
  placeholder?: string;
}

export function PromptComposer({
  value,
  onChange,
  onSubmit,
  loading,
  placeholder = "Why did txn_28131 fail?",
}: PromptComposerProps) {
  const canSubmit = value.trim().length > 0 && !loading;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (canSubmit) onSubmit();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSubmit) onSubmit();
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="glass group relative rounded-2xl p-1 transition-shadow duration-200 focus-within:shadow-[var(--shadow-glow)]">
        <label htmlFor="query" className="sr-only">
          Ask about documentation, a transaction, or policy
        </label>
        <textarea
          id="query"
          name="query"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={3}
          aria-describedby="composer-hint"
          className="w-full resize-none bg-transparent px-4 pt-3.5 text-[15px] leading-relaxed text-ink placeholder:text-ink-faint focus:outline-none"
        />

        <div className="flex items-center justify-between gap-3 px-4 pb-3 pt-1">
          <p id="composer-hint" className="text-[11px] text-ink-faint">
            <kbd className="rounded border border-line-strong px-1 py-0.5 font-mono text-[10px]">Enter</kbd>{" "}
            to send ·{" "}
            <kbd className="rounded border border-line-strong px-1 py-0.5 font-mono text-[10px]">
              Shift↵
            </kbd>{" "}
            for a new line
          </p>

          <button
            type="submit"
            disabled={!canSubmit}
            aria-label={loading ? "Asking Copilot" : "Ask Copilot"}
            className="inline-flex h-11 w-11 shrink-0 cursor-pointer items-center justify-center rounded-full bg-violet text-on-violet shadow-[0_8px_24px_-8px_rgba(139,92,246,0.9)] transition-all duration-200 hover:bg-violet-bright disabled:cursor-not-allowed disabled:bg-white/8 disabled:text-ink-faint disabled:shadow-none"
          >
            {loading ? (
              <CircleNotch size={18} weight="bold" aria-hidden="true" className="animate-spin" />
            ) : (
              <ArrowUp size={18} weight="bold" aria-hidden="true" />
            )}
          </button>
        </div>
      </div>
    </form>
  );
}
