"""Postgres connection helper."""

import psycopg
from psycopg.rows import dict_row

from paymentcopilot.config import settings


def get_connection() -> psycopg.Connection:
    return psycopg.connect(settings.database_url, row_factory=dict_row)
