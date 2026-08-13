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
    )


settings = load_settings()
