"""LangGraph router: classify a query, dispatch to the UC1/UC2/UC3/out-of-scope node.

Per PRD §4.1/FR2, this makes the route taken explicit and inspectable (each node
run is a distinct, loggable step) rather than a single opaque LLM call deciding
everything at once.

Phase 3 adds guardrail nodes (input_guardrail, blocked, output_guardrail) to the same graph,
for the same inspectability reason (PRD FR2, §8 NFR "guardrail outcomes" in structured logs) —
see docs/01-architecture.md "Phase 3 — Guardrails" for the full topology diagram.
"""

import dataclasses
from typing import TypedDict

from langgraph.graph import END, StateGraph

from paymentcopilot.generation.generator import (
    generate_answer,
    generate_policy_answer,
    generate_transaction_answer,
)
from paymentcopilot.generation.prompts import build_transaction_record_text
from paymentcopilot.graph.classify import TXN_ID_RE, classify_query
from paymentcopilot.guardrails.faithfulness import check_faithfulness
from paymentcopilot.guardrails.injection import scan_injection
from paymentcopilot.guardrails.logging import log_guardrail_event
from paymentcopilot.guardrails.messages import (
    FAITHFULNESS_FAILURE_MESSAGE,
    INJECTION_BLOCKED_MESSAGE,
    TRANSACTION_DESCRIPTION_FLAGGED_NOTE,
)
from paymentcopilot.guardrails.pii import scan_and_redact
from paymentcopilot.models import RouterResult
from paymentcopilot.retrieval.retriever import retrieve
from paymentcopilot.structured.error_codes import explain_error_code
from paymentcopilot.structured.lookup import lookup_transaction

OUT_OF_SCOPE_MESSAGE = (
    "I can only help with questions about this payment platform's API, your transactions, "
    "or refund/compliance policy. This question is outside what I can answer — please "
    "contact general support for anything else."
)

TXN_NOT_FOUND_MESSAGE_TEMPLATE = (
    "I couldn't find transaction '{txn_id}' for this merchant account. Double-check the "
    "transaction ID, or note that transactions belonging to a different merchant are never "
    "visible here."
)


class RouterState(TypedDict, total=False):
    query: str
    merchant_id: str
    route: str
    route_reason: str
    answer: str
    escalated: bool
    retrieved_chunks: list
    transaction: object
    guardrail_status: str


def _append_status(current: str, tag: str) -> str:
    if not current or current == "passed":
        return tag
    return f"{current},{tag}"


def _classify_node(state: RouterState) -> dict:
    route, reason = classify_query(state["query"])
    return {"route": route, "route_reason": reason}


def _input_guardrail_node(state: RouterState) -> dict:
    query = state["query"]

    injection = scan_injection(query)
    if injection.matched:
        log_guardrail_event("input_blocked", state.get("route", "unknown"), f"injection:{injection.category}")
        return {"route": "blocked", "guardrail_status": f"input_blocked:injection:{injection.category}"}

    pii = scan_and_redact(query)
    if pii.had_pii:
        log_guardrail_event(
            "input_redacted", state.get("route", "unknown"), f"pii:{','.join(pii.found_entities)}"
        )
        return {"query": pii.redacted_text, "guardrail_status": "input_redacted:pii"}

    return {"guardrail_status": "passed"}


def _blocked_node(state: RouterState) -> dict:
    return {"answer": INJECTION_BLOCKED_MESSAGE, "escalated": True, "retrieved_chunks": []}


def _uc1_node(state: RouterState) -> dict:
    chunks = retrieve(state["query"], top_k=5, doc_type="docs")
    answer = generate_answer(state["query"], chunks)
    return {
        "answer": answer.text,
        "escalated": not answer.grounded,
        "retrieved_chunks": answer.retrieved_chunks,
    }


def _format_transaction_fallback(transaction, error_explanation: str | None) -> str:
    lines = [
        (
            f"Transaction {transaction.txn_id}: status={transaction.status}, "
            f"amount={transaction.amount} {transaction.currency}, created_at={transaction.created_at}."
        )
    ]
    if transaction.error_code:
        lines.append(f"Error code: {transaction.error_code}.")
        if error_explanation:
            lines.append(error_explanation)
    lines.append(TRANSACTION_DESCRIPTION_FLAGGED_NOTE)
    return " ".join(lines)


def _uc2_node(state: RouterState) -> dict:
    match = TXN_ID_RE.search(state["query"])
    txn_id = match.group(0)
    transaction = lookup_transaction(txn_id, state["merchant_id"])

    if transaction is None:
        return {
            "answer": TXN_NOT_FOUND_MESSAGE_TEMPLATE.format(txn_id=txn_id),
            "escalated": True,
            "retrieved_chunks": [],
            "transaction": None,
        }

    error_explanation = explain_error_code(transaction.error_code)
    description = transaction.description or ""

    injection = scan_injection(description) if description else None
    if injection and injection.matched:
        log_guardrail_event(
            "input_blocked", "uc2_transaction", f"description_injection:{injection.category}"
        )
        return {
            "answer": _format_transaction_fallback(transaction, error_explanation),
            "escalated": True,
            "retrieved_chunks": [],
            "transaction": transaction,
            "guardrail_status": _append_status(
                state.get("guardrail_status", "passed"), "input_blocked:description_injection"
            ),
        }

    safe_transaction = transaction
    status_update = {}
    if description:
        pii = scan_and_redact(description)
        if pii.had_pii:
            safe_transaction = dataclasses.replace(transaction, description=pii.redacted_text)
            log_guardrail_event(
                "input_redacted", "uc2_transaction", f"description_pii:{','.join(pii.found_entities)}"
            )
            status_update["guardrail_status"] = _append_status(
                state.get("guardrail_status", "passed"), "input_redacted:description_pii"
            )

    doc_chunks = []
    if transaction.error_code:
        doc_chunks = retrieve(f"explain error code {transaction.error_code}", top_k=2, doc_type="docs")

    answer = generate_transaction_answer(state["query"], safe_transaction, error_explanation, doc_chunks)
    return {
        "answer": answer.text,
        "escalated": False,
        "retrieved_chunks": answer.retrieved_chunks,
        "transaction": transaction,
        **status_update,
    }


def _uc3_node(state: RouterState) -> dict:
    chunks = retrieve(state["query"], top_k=5, doc_type="policy")
    answer = generate_policy_answer(state["query"], chunks)
    return {
        "answer": answer.text,
        "escalated": not answer.grounded,
        "retrieved_chunks": answer.retrieved_chunks,
    }


def _out_of_scope_node(state: RouterState) -> dict:
    return {"answer": OUT_OF_SCOPE_MESSAGE, "escalated": True, "retrieved_chunks": []}


def _build_grounding_text(state: RouterState) -> str:
    chunks = state.get("retrieved_chunks") or []
    parts = []

    if state["route"] == "uc2_transaction":
        transaction = state.get("transaction")
        if transaction:
            error_explanation = explain_error_code(transaction.error_code)
            parts.append(build_transaction_record_text(transaction))
            if error_explanation:
                parts.append(error_explanation)

    parts.extend(f"{rc.chunk.source_doc} — {rc.chunk.section}: {rc.chunk.text}" for rc in chunks)
    return "\n\n".join(parts)


def _output_guardrail_node(state: RouterState) -> dict:
    if state.get("escalated"):
        return {}

    route = state["route"]
    answer_text = state["answer"]

    grounding_text = _build_grounding_text(state)
    faithfulness = check_faithfulness(answer_text, grounding_text)
    if not faithfulness.passed:
        log_guardrail_event("output_blocked", route, f"faithfulness:{faithfulness.reason}")
        return {
            "answer": FAITHFULNESS_FAILURE_MESSAGE,
            "escalated": True,
            "guardrail_status": _append_status(
                state.get("guardrail_status", "passed"), "output_blocked:faithfulness"
            ),
        }

    pii = scan_and_redact(answer_text)
    if pii.had_pii:
        log_guardrail_event("output_redacted", route, f"pii:{','.join(pii.found_entities)}")
        return {
            "answer": pii.redacted_text,
            "guardrail_status": _append_status(state.get("guardrail_status", "passed"), "output_redacted:pii"),
        }

    return {}


def _route_selector(state: RouterState) -> str:
    return state["route"]


def _build_graph():
    graph = StateGraph(RouterState)
    graph.add_node("classify", _classify_node)
    graph.add_node("input_guardrail", _input_guardrail_node)
    graph.add_node("blocked", _blocked_node)
    graph.add_node("uc1_docs", _uc1_node)
    graph.add_node("uc2_transaction", _uc2_node)
    graph.add_node("uc3_policy", _uc3_node)
    graph.add_node("out_of_scope", _out_of_scope_node)
    graph.add_node("output_guardrail", _output_guardrail_node)

    graph.set_entry_point("classify")
    graph.add_edge("classify", "input_guardrail")
    graph.add_conditional_edges(
        "input_guardrail",
        _route_selector,
        {
            "uc1_docs": "uc1_docs",
            "uc2_transaction": "uc2_transaction",
            "uc3_policy": "uc3_policy",
            "out_of_scope": "out_of_scope",
            "blocked": "blocked",
        },
    )
    graph.add_edge("uc1_docs", "output_guardrail")
    graph.add_edge("uc2_transaction", "output_guardrail")
    graph.add_edge("uc3_policy", "output_guardrail")
    graph.add_edge("output_guardrail", END)
    graph.add_edge("out_of_scope", END)
    graph.add_edge("blocked", END)

    return graph.compile()


_graph = _build_graph()


def run_query(query: str, merchant_id: str = "demo-merchant") -> RouterResult:
    result = _graph.invoke({"query": query, "merchant_id": merchant_id})
    return RouterResult(
        query=result.get("query", query),
        route=result["route"],
        route_reason=result["route_reason"],
        answer=result["answer"],
        escalated=result["escalated"],
        retrieved_chunks=result.get("retrieved_chunks", []),
        transaction=result.get("transaction"),
        guardrail_status=result.get("guardrail_status", "passed"),
    )
