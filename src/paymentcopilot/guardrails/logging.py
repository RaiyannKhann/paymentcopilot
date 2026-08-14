"""Structured logging for triggered guardrails (PRD §8 NFR: guardrail outcomes in logs).

Only triggered guardrails are logged (not passes) to keep signal high.
"""

import json
import logging

_logger = logging.getLogger("paymentcopilot.guardrails")


def log_guardrail_event(event: str, route: str, detail: str) -> None:
    _logger.warning(json.dumps({"event": event, "route": route, "detail": detail}))
