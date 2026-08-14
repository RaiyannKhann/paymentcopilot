"""Optional Claude token-usage accumulator for per-request observability.

A no-op unless reset_usage_tracking() was called first, so existing callers of
call_claude() (CLI, evals, guardrails, and every test that mocks call_claude
wholesale) are unaffected. Callers that want totals must reset/call/read within
the same thread/context - ContextVar state set inside asyncio.to_thread does not
propagate back to the calling coroutine.
"""

from contextvars import ContextVar

_usage_accumulator: ContextVar[list[dict] | None] = ContextVar("usage_accumulator", default=None)


def reset_usage_tracking() -> None:
    _usage_accumulator.set([])


def record_usage(input_tokens: int, output_tokens: int) -> None:
    accumulator = _usage_accumulator.get()
    if accumulator is not None:
        accumulator.append({"input_tokens": input_tokens, "output_tokens": output_tokens})


def get_usage_totals() -> dict:
    accumulator = _usage_accumulator.get() or []
    return {
        "input_tokens": sum(u["input_tokens"] for u in accumulator),
        "output_tokens": sum(u["output_tokens"] for u in accumulator),
        "calls": len(accumulator),
    }
