"""Structured JSON request logging (PRD §8 NFR: route, latency, token usage, guardrail outcomes).

One log line per request, covering every request regardless of outcome - distinct
from guardrails/logging.py's log_guardrail_event, which only logs when a guardrail
actually triggers (security-audit granularity, not full-lifecycle observability).
"""

import json
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware

_logger = logging.getLogger("paymentcopilot.requests")
_logger.setLevel(logging.INFO)
if not _logger.handlers:
    # Scoped to this logger only (not logging.basicConfig on the root logger) so
    # third-party libraries' own log verbosity is untouched.
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(_handler)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.monotonic()
        response = await call_next(request)
        latency_ms = (time.monotonic() - start) * 1000

        _logger.info(
            json.dumps(
                {
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "latency_ms": round(latency_ms, 1),
                    "tenant_id": getattr(request.state, "pc_tenant_id", None),
                    "route": getattr(request.state, "pc_route", None),
                    "guardrail_status": getattr(request.state, "pc_guardrail_status", None),
                    "escalated": getattr(request.state, "pc_escalated", None),
                    "cache_hit": getattr(request.state, "pc_cache_hit", None),
                    "token_usage": getattr(request.state, "pc_token_usage", None),
                }
            )
        )
        return response
