import { ArrowBendUpLeft, WarningOctagon } from "@phosphor-icons/react/dist/ssr";
import type { QueryResponse } from "@/lib/types";
import { PipelineSkeleton } from "./PipelineSkeleton";
import { ResponseCard } from "./ResponseCard";

export interface ChatTurn {
  id: string;
  query: string;
  response: QueryResponse | null;
  error: string | null;
  pending: boolean;
  /** Prior turns the backend threaded into this turn's prompt — 0 on the first turn,
      and capped at the backend's MAX_HISTORY_TURNS window. */
  contextTurns: number;
}

/** One question and whatever came back for it. Turns stay on screen so a follow-up
    reads against what it's following up on — the session memory the backend threads
    into the prompt (cache/session_memory.py) is only useful if the merchant can see
    the conversation it's built from. */
export function ConversationTurn({ turn, index }: { turn: ChatTurn; index: number }) {
  return (
    <article aria-label={`Turn ${index + 1}`} className="flex flex-col gap-4">
      <div className="flex flex-col items-end gap-1.5">
        {turn.contextTurns > 0 && (
          <span className="inline-flex items-center gap-1.5 pr-1 text-[10px] font-medium uppercase tracking-[0.12em] text-ink-faint">
            <ArrowBendUpLeft size={12} weight="bold" aria-hidden="true" />
            Follow-up · {turn.contextTurns} prior turn{turn.contextTurns === 1 ? "" : "s"} in
            context
          </span>
        )}
        <p className="glass-subtle animate-rise max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md px-4 py-3 text-[15px] leading-relaxed text-ink">
          {turn.query}
        </p>
      </div>

      {turn.pending && <PipelineSkeleton />}

      {turn.error && (
        <div
          role="alert"
          className="animate-rise flex items-start gap-3 rounded-panel border border-bad/25 bg-bad-dim px-5 py-4"
        >
          <WarningOctagon
            size={18}
            weight="fill"
            aria-hidden="true"
            className="mt-0.5 shrink-0 text-bad"
          />
          <div>
            <p className="text-sm font-medium text-bad">Request failed</p>
            <p className="mt-1 text-sm leading-relaxed text-ink-muted">{turn.error}</p>
          </div>
        </div>
      )}

      {turn.response && <ResponseCard response={turn.response} />}
    </article>
  );
}
