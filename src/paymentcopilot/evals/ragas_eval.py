"""RAGAS scoring (FR17, §7.2): faithfulness, answer relevancy, context precision/recall —
computed offline over the golden set's ragas_eligible/happy-path subset only. Independent of
`guardrails/faithfulness.py`'s live per-request PASS/FAIL judge — see docs/01-architecture.md
"Phase 4" for why these stay separate.
"""

import math

from paymentcopilot.config import settings
from paymentcopilot.evals.runner import EvalRecord
from paymentcopilot.generation.prompts import build_transaction_record_text
from paymentcopilot.structured.error_codes import explain_error_code


def _grounding_contexts(record: EvalRecord) -> list[str]:
    contexts = []
    if record.item.category == "uc2_happy" and record.transaction is not None:
        contexts.append(build_transaction_record_text(record.transaction))
        error_explanation = explain_error_code(record.transaction.error_code)
        if error_explanation:
            contexts.append(error_explanation)
    contexts.extend(rc.chunk.text for rc in record.retrieved_chunks)
    return contexts


def build_ragas_dataset(records: list[EvalRecord]) -> list[dict]:
    eligible = [r for r in records if r.item.ragas_eligible and r.error is None and r.answer]
    return [
        {
            "user_input": r.item.query,
            "response": r.answer,
            "retrieved_contexts": _grounding_contexts(r) or [""],
            "reference": r.item.reference_answer,
        }
        for r in eligible
    ]


def _mean(values: list[float]) -> float | None:
    clean = [v for v in values if v is not None and not math.isnan(v)]
    return sum(clean) / len(clean) if clean else None


def run_ragas(records: list[EvalRecord]) -> dict[str, float] | None:
    samples = build_ragas_dataset(records)
    if not samples:
        return None

    from langchain_anthropic import ChatAnthropic
    from langchain_huggingface import HuggingFaceEmbeddings
    from ragas import EvaluationDataset, evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import (
        Faithfulness,
        LLMContextPrecisionWithReference,
        LLMContextRecall,
        ResponseRelevancy,
    )

    llm = LangchainLLMWrapper(
        ChatAnthropic(model=settings.anthropic_model, api_key=settings.anthropic_api_key)
    )
    embeddings = LangchainEmbeddingsWrapper(HuggingFaceEmbeddings(model_name=settings.embedding_model))

    dataset = EvaluationDataset.from_list(samples)
    metrics = [
        Faithfulness(),
        ResponseRelevancy(),
        LLMContextPrecisionWithReference(),
        LLMContextRecall(),
    ]
    result = evaluate(dataset=dataset, metrics=metrics, llm=llm, embeddings=embeddings)

    scores = {}
    for metric in metrics:
        mean = _mean(result[metric.name])
        if mean is not None:
            scores[metric.name] = mean
    return scores
