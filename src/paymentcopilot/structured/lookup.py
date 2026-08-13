"""Query the mock transactions table by txn_id, scoped to a merchant tenant."""

from paymentcopilot.models import Transaction
from paymentcopilot.structured.db import get_connection


def lookup_transaction(txn_id: str, merchant_id: str) -> Transaction | None:
    """Look up a transaction by ID, scoped to merchant_id.

    Scoping by merchant_id (not just txn_id) is the actual multi-tenant boundary
    for structured data: a txn_id that exists but belongs to a different merchant
    returns None rather than leaking cross-tenant data.
    """
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT txn_id, merchant_id, status, error_code, amount, currency, description, created_at
            FROM transactions
            WHERE txn_id = %s AND merchant_id = %s
            """,
            (txn_id, merchant_id),
        )
        row = cur.fetchone()

    if row is None:
        return None

    return Transaction(
        txn_id=row["txn_id"],
        merchant_id=row["merchant_id"],
        status=row["status"],
        error_code=row["error_code"],
        amount=row["amount"],
        currency=row["currency"],
        description=row["description"],
        created_at=row["created_at"].isoformat(),
    )
