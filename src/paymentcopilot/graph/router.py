"""LangGraph router: classify a query, dispatch to the UC1/UC2/UC3/out-of-scope node.

Per PRD §4.1/FR2, this makes the route taken explicit and inspectable (each node
run is a distinct, loggable step) rather than a single opaque LLM call deciding
everything at once.
"""

from typing import TypedDict

from langgraph.graph import END, StateGraph

from paymentcopilot.generation.generator import (
    generate_answer,
    generate_policy_answer,
    generate_transaction_answer,
)
from paymentcopilot.graph.classify import TXN_ID_RE, classify_query
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


def _classify_node(state: RouterState) -> dict:
    route, reason = classify_query(state["query"])
    return {"route": route, "route_reason": reason}


def _uc1_node(state: RouterState) -> dict:
    chunks = retrieve(state["query"], top_k=5, doc_type="docs")
    answer = generate_answer(state["query"], chunks)
    return {
        "answer": answer.text,
        "escalated": not answer.grounded,
        "retrieved_chunks": answer.retrieved_chunks,
    }


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
    doc_chunks = []
    if transaction.error_code:
        doc_chunks = retrieve(f"explain error code {transaction.error_code}", top_k=2, doc_type="docs")

    answer = generate_transaction_answer(state["query"], transaction, error_explanation, doc_chunks)
    return {
        "answer": answer.text,
        "escalated": False,
        "retrieved_chunks": answer.retrieved_chunks,
        "transaction": transaction,
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


def _route_selector(state: RouterState) -> str:
    return state["route"]


def _build_graph():
    graph = StateGraph(RouterState)
    graph.add_node("classify", _classify_node)
    graph.add_node("uc1_docs", _uc1_node)
    graph.add_node("uc2_transaction", _uc2_node)
    graph.add_node("uc3_policy", _uc3_node)
    graph.add_node("out_of_scope", _out_of_scope_node)

    graph.set_entry_point("classify")
    graph.add_conditional_edges(
        "classify",
        _route_selector,
        {
            "uc1_docs": "uc1_docs",
            "uc2_transaction": "uc2_transaction",
            "uc3_policy": "uc3_policy",
            "out_of_scope": "out_of_scope",
        },
    )
    graph.add_edge("uc1_docs", END)
    graph.add_edge("uc2_transaction", END)
    graph.add_edge("uc3_policy", END)
    graph.add_edge("out_of_scope", END)

    return graph.compile()


_graph = _build_graph()


def run_query(query: str, merchant_id: str = "demo-merchant") -> RouterResult:
    result = _graph.invoke({"query": query, "merchant_id": merchant_id})
    return RouterResult(
        query=query,
        route=result["route"],
        route_reason=result["route_reason"],
        answer=result["answer"],
        escalated=result["escalated"],
        retrieved_chunks=result.get("retrieved_chunks", []),
        transaction=result.get("transaction"),
    )
