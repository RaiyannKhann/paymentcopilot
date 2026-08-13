#!/usr/bin/env python
"""Generate a reproducible synthetic mock transactions dataset.

Deterministic (fixed seed) so the CSV can be regenerated identically if the
schema changes. All data is synthetic — no real merchants, transactions, or
PII. See data/docs_corpus/07-error-codes.md for the error_code vocabulary.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42
NUM_TRANSACTIONS = 40
MERCHANTS = ["demo-merchant", "acme-retail", "globex-travel"]
CURRENCIES = ["INR", "INR", "INR", "USD"]  # weighted toward INR
STATUSES = ["success", "success", "success", "failed", "failed", "pending", "refunded"]
ERROR_CODES = [
    "insufficient_funds",
    "card_expired",
    "card_declined",
    "authentication_failed",
    "authentication_timeout",
    "invalid_card_number",
    "issuer_unavailable",
    "risk_blocked",
]
WINDOW_START = datetime(2026, 7, 1)
WINDOW_END = datetime(2026, 8, 13)

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "transactions" / "transactions.csv"


def generate() -> list[dict]:
    rng = random.Random(SEED)
    used_ids = set()
    rows = []

    for _ in range(NUM_TRANSACTIONS):
        while True:
            txn_id = f"txn_{rng.randint(10000, 99999)}"
            if txn_id not in used_ids:
                used_ids.add(txn_id)
                break

        status = rng.choice(STATUSES)
        error_code = rng.choice(ERROR_CODES) if status == "failed" else None
        currency = rng.choice(CURRENCIES)
        amount = rng.randint(500, 250000) if currency == "INR" else rng.randint(100, 50000)
        merchant_id = rng.choice(MERCHANTS)

        offset_seconds = rng.randint(0, int((WINDOW_END - WINDOW_START).total_seconds()))
        created_at = WINDOW_START + timedelta(seconds=offset_seconds)

        description = "" if rng.random() < 0.7 else rng.choice(
            [
                "Order payment",
                "Subscription renewal",
                "Invoice settlement",
                "Customer checkout",
            ]
        )

        rows.append(
            {
                "txn_id": txn_id,
                "merchant_id": merchant_id,
                "status": status,
                "error_code": error_code or "",
                "amount": amount,
                "currency": currency,
                "description": description,
                "created_at": created_at.isoformat(),
            }
        )

    rows.sort(key=lambda r: r["created_at"])
    return rows


def main():
    rows = generate()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "txn_id",
                "merchant_id",
                "status",
                "error_code",
                "amount",
                "currency",
                "description",
                "created_at",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {len(rows)} synthetic transactions -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
