"""PII detection and redaction via Presidio (PRD FR11/FR14).

Entity list is deliberately narrow and payments-domain relevant, and deliberately excludes
PERSON/LOCATION — those need the NLP model and are prone to false-positive redaction of
merchant/product names in this domain, whereas the chosen entities are pattern-based recognizers.
"""

from dataclasses import dataclass
from functools import lru_cache

PII_ENTITIES = [
    "CREDIT_CARD",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "IBAN_CODE",
    "US_SSN",
    "US_BANK_NUMBER",
]


@dataclass(frozen=True)
class PIIResult:
    redacted_text: str
    found_entities: list[str]
    had_pii: bool


@lru_cache(maxsize=1)
def _analyzer():
    from presidio_analyzer import AnalyzerEngine
    from presidio_analyzer.nlp_engine import NlpEngineProvider

    # Presidio's AnalyzerEngine() defaults to en_core_web_lg (400MB, downloaded on first
    # use) unless explicitly configured. Pinned to en_core_web_sm to match the small,
    # pattern-based-recognizer-only entity list this project actually uses (see module
    # docstring) and to keep runtime behavior network-independent once the model is
    # installed (README/Dockerfile both provision en_core_web_sm, not _lg).
    nlp_engine = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
    ).create_engine()
    return AnalyzerEngine(nlp_engine=nlp_engine)


@lru_cache(maxsize=1)
def _anonymizer():
    from presidio_anonymizer import AnonymizerEngine

    return AnonymizerEngine()


def scan_and_redact(text: str, entities: list[str] | None = None) -> PIIResult:
    if not text:
        return PIIResult(redacted_text=text, found_entities=[], had_pii=False)

    entities = entities if entities is not None else PII_ENTITIES
    results = _analyzer().analyze(text=text, entities=entities, language="en")

    if not results:
        return PIIResult(redacted_text=text, found_entities=[], had_pii=False)

    anonymized = _anonymizer().anonymize(text=text, analyzer_results=results)
    found = sorted({r.entity_type for r in results})
    return PIIResult(redacted_text=anonymized.text, found_entities=found, had_pii=True)
