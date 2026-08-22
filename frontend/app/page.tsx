"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowCounterClockwise, Brain } from "@phosphor-icons/react/dist/ssr";
import { postQuery, ApiError } from "@/lib/api";
import { saveTrace } from "@/lib/traceStore";
import { ConversationTurn, type ChatTurn } from "@/components/ConversationTurn";
import { PromptComposer } from "@/components/PromptComposer";
import { CapabilityCards } from "@/components/CapabilityCards";
import { Orb } from "@/components/Orb";
import { VoxelBackdrop } from "@/components/VoxelBackdrop";

const TENANT_ID = process.env.NEXT_PUBLIC_DEMO_TENANT_ID ?? "demo-merchant";

// Mirrors MAX_HISTORY_TURNS in src/paymentcopilot/api/app.py — the number of prior
// turns the backend actually threads into the prompt. Shown, not enforced, here.
const MEMORY_WINDOW_TURNS = 5;

export default function SupportConsolePage() {
  const [query, setQuery] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [loading, setLoading] = useState(false);
  const transcriptEndRef = useRef<HTMLDivElement>(null);

  // Each new turn scrolls itself into view; a transcript that silently grows below the
  // fold reads as a dead composer.
  useEffect(() => {
    if (turns.length === 0) return;
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    transcriptEndRef.current?.scrollIntoView({
      behavior: reduceMotion ? "auto" : "smooth",
      block: "end",
    });
  }, [turns.length]);

  async function runQuery(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;

    // Only answered turns reached the backend's session memory — a failed request
    // (rate limit, unreachable API) never appended one.
    const rememberedTurns = Math.min(
      turns.filter((turn) => turn.response !== null).length,
      MEMORY_WINDOW_TURNS
    );
    const turnId = crypto.randomUUID();

    setTurns((previous) => [
      ...previous,
      {
        id: turnId,
        query: trimmed,
        response: null,
        error: null,
        pending: true,
        contextTurns: rememberedTurns,
      },
    ]);
    setQuery("");
    setLoading(true);

    try {
      const result = await postQuery({
        tenant_id: TENANT_ID,
        query: trimmed,
        session_id: sessionId,
      });
      setSessionId(result.session_id);
      saveTrace(result.trace);
      setTurns((previous) =>
        previous.map((turn) =>
          turn.id === turnId ? { ...turn, response: result, pending: false } : turn
        )
      );
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
      setTurns((previous) =>
        previous.map((turn) => (turn.id === turnId ? { ...turn, error: message, pending: false } : turn))
      );
    } finally {
      setLoading(false);
    }
  }

  /** Dropping the transcript also drops the session id, so the backend starts a fresh
      memory key — otherwise the model would keep answering against turns the merchant
      can no longer see. */
  function startNewConversation() {
    setTurns([]);
    setSessionId(undefined);
    setQuery("");
  }

  const isLanding = turns.length === 0;
  const rememberedTurns = Math.min(
    turns.filter((turn) => turn.response !== null).length,
    MEMORY_WINDOW_TURNS
  );

  return (
    <div className="relative mx-auto flex min-h-dvh w-full max-w-3xl flex-col px-4 pb-6 sm:px-6">
      <VoxelBackdrop />

      {isLanding && (
        <section className="flex flex-col items-center pt-14 text-center sm:pt-20">
          <Orb size={104} />
          <h1 className="text-gradient mt-8 text-3xl font-semibold tracking-tight sm:text-[2.6rem] sm:leading-[1.1]">
            How can I help?
          </h1>
          <p className="mt-3 max-w-md text-sm leading-relaxed text-ink-muted">
            Ask about your integration, a specific transaction, or platform policy. Every answer is
            grounded, guardrailed, and fully traceable — and follow-up questions remember the turns
            before them.
          </p>
        </section>
      )}

      {!isLanding && (
        <section
          aria-live="polite"
          aria-busy={loading}
          aria-label="Conversation"
          className="flex flex-col gap-8 pt-8"
        >
          {turns.map((turn, index) => (
            <ConversationTurn key={turn.id} turn={turn} index={index} />
          ))}
        </section>
      )}

      <div ref={transcriptEndRef} aria-hidden="true" />

      {/* Sticky so the composer — and the memory controls under it — stay reachable
          however long the transcript gets. */}
      <div
        className={
          isLanding
            ? "mt-8"
            : "sticky bottom-0 z-10 mt-8 bg-gradient-to-t from-canvas via-canvas to-transparent pb-3 pt-6"
        }
      >
        <PromptComposer
          value={query}
          onChange={setQuery}
          onSubmit={() => void runQuery(query)}
          loading={loading}
          placeholder={isLanding ? "Why did txn_28131 fail?" : "Ask a follow-up — “why did that fail?”"}
        />

        {!isLanding && (
          <div className="mt-2.5 flex flex-wrap items-center justify-between gap-x-4 gap-y-2 px-1">
            <p className="inline-flex items-center gap-1.5 text-[11px] text-ink-faint">
              <Brain size={13} weight="fill" aria-hidden="true" className="text-violet-bright" />
              {rememberedTurns === 0
                ? "Session memory starts with your first answer"
                : `Session memory · last ${rememberedTurns} of ${MEMORY_WINDOW_TURNS} turns go into the next answer`}
            </p>
            <button
              type="button"
              onClick={startNewConversation}
              className="inline-flex shrink-0 cursor-pointer items-center gap-1.5 rounded-lg border border-white/10 px-2.5 py-1.5 text-[11px] text-ink-muted transition-colors hover:bg-white/5 hover:text-ink"
            >
              <ArrowCounterClockwise size={12} weight="bold" aria-hidden="true" />
              New conversation
            </button>
          </div>
        )}
      </div>

      {isLanding && (
        <div className="mt-4">
          <CapabilityCards onPick={setQuery} />
        </div>
      )}
    </div>
  );
}
