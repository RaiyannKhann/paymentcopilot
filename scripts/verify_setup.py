#!/usr/bin/env python
"""Verify required env vars are set and API credentials are valid."""

import sys

from paymentcopilot.config import settings


def check_anthropic() -> bool:
    from anthropic import Anthropic

    try:
        client = Anthropic(api_key=settings.anthropic_api_key)
        client.messages.create(
            model=settings.anthropic_model,
            max_tokens=8,
            messages=[{"role": "user", "content": "Say OK."}],
        )
        print(f"[OK] Anthropic API reachable (model={settings.anthropic_model}).")
        return True
    except Exception as e:  # noqa: BLE001 - top-level diagnostic, any failure is reportable
        print(f"[FAIL] Anthropic API check failed: {e}")
        return False


def check_pinecone() -> bool:
    from pinecone import Pinecone

    try:
        pc = Pinecone(api_key=settings.pinecone_api_key)
        indexes = {idx["name"] for idx in pc.list_indexes()}
        if settings.pinecone_index_name in indexes:
            print(f"[OK] Pinecone reachable; index '{settings.pinecone_index_name}' exists.")
        else:
            print(
                f"[OK] Pinecone reachable; index '{settings.pinecone_index_name}' does not exist "
                f"yet — it will be created on first `ingest` run."
            )
        return True
    except Exception as e:  # noqa: BLE001 - top-level diagnostic, any failure is reportable
        print(f"[FAIL] Pinecone check failed: {e}")
        return False


def main():
    print("Checking Payment Copilot setup...\n")
    ok = check_anthropic() and check_pinecone()
    if not ok:
        sys.exit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
