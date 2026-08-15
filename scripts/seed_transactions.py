#!/usr/bin/env python
"""Create the transactions table and load it from data/transactions/transactions.csv.

Idempotent: drops and recreates the table each run, so it's safe to re-run
after regenerating the CSV.
"""

import csv
from pathlib import Path

import psycopg

from paymentcopilot.config import settings

CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "transactions" / "transactions.csv"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS transactions (
    txn_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL,
    status TEXT NOT NULL,
    error_code TEXT,
    amount BIGINT NOT NULL,
    currency TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL
);
"""


def main():
    rows = list(csv.DictReader(CSV_PATH.open()))

    with (
        psycopg.connect(settings.database_url, autocommit=True) as conn,
        conn.cursor() as cur,
    ):
        cur.execute("DROP TABLE IF EXISTS transactions;")
        cur.execute(CREATE_TABLE_SQL)
        cur.execute("CREATE INDEX idx_transactions_merchant ON transactions (merchant_id);")

        for row in rows:
            cur.execute(
                """
                INSERT INTO transactions
                    (txn_id, merchant_id, status, error_code, amount, currency, description, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row["txn_id"],
                    row["merchant_id"],
                    row["status"],
                    row["error_code"] or None,
                    int(row["amount"]),
                    row["currency"],
                    row["description"] or None,
                    row["created_at"],
                ),
            )

    print(f"Seeded {len(rows)} transactions into '{settings.database_url}'.")


if __name__ == "__main__":
    main()
