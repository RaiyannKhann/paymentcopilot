"""Environment configuration for Payment Copilot."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

_REQUIRED = ["ANTHROPIC_API_KEY", "PINECONE_API_KEY"]


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str
    anthropic_model: str
    pinecone_api_key: str
    pinecone_index_name: str
    pinecone_cloud: str
    pinecone_region: str
    embedding_model: str
    database_url: str
    uc3_confidence_threshold: float
    uc1_confidence_threshold: float
    redis_url: str
    semantic_cache_similarity_threshold: float
    semantic_cache_ttl_seconds: int
    semantic_cache_max_entries_per_tenant: int
    rate_limit_window_seconds: int
    rate_limit_max_requests: int
    session_ttl_seconds: int
    enable_evals_endpoint: bool


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Copy .env.example to .env and fill in your API keys."
        )
    return value


def load_settings() -> Settings:
    for name in _REQUIRED:
        _require(name)
    return Settings(
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
        anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5"),
        pinecone_api_key=os.environ["PINECONE_API_KEY"],
        pinecone_index_name=os.environ.get("PINECONE_INDEX_NAME", "payment-copilot-docs"),
        pinecone_cloud=os.environ.get("PINECONE_CLOUD", "aws"),
        pinecone_region=os.environ.get("PINECONE_REGION", "us-east-1"),
        embedding_model=os.environ.get(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        ),
        database_url=os.environ.get(
            "DATABASE_URL", "postgresql://localhost/paymentcopilot"
        ),
        uc3_confidence_threshold=float(os.environ.get("UC3_CONFIDENCE_THRESHOLD", "0.45")),
        uc1_confidence_threshold=float(os.environ.get("UC1_CONFIDENCE_THRESHOLD", "0.40")),
        redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        semantic_cache_similarity_threshold=float(
            os.environ.get("SEMANTIC_CACHE_SIMILARITY_THRESHOLD", "0.94")
        ),
        semantic_cache_ttl_seconds=int(os.environ.get("SEMANTIC_CACHE_TTL_SECONDS", "3600")),
        semantic_cache_max_entries_per_tenant=int(
            os.environ.get("SEMANTIC_CACHE_MAX_ENTRIES_PER_TENANT", "50")
        ),
        rate_limit_window_seconds=int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60")),
        rate_limit_max_requests=int(os.environ.get("RATE_LIMIT_MAX_REQUESTS", "20")),
        session_ttl_seconds=int(os.environ.get("SESSION_TTL_SECONDS", "1800")),
        enable_evals_endpoint=os.environ.get("ENABLE_EVALS_ENDPOINT", "false").lower() == "true",
    )


settings = load_settings()
