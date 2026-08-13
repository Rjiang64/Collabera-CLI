"""
Database connection layer (Neon / PostgreSQL).

Reads DATABASE_URL from the .env file, opens a small connection pool, and
exposes tiny helpers so the services can run SQL and get back dicts -
the same shape they used to get from the in-memory sample data.
"""

import os

from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

# Load variables from the .env file into the environment.
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and paste your "
        "Neon connection string."
    )

# One shared pool for the whole app. Each query borrows a connection and
# returns it. row_factory=dict_row makes every row come back as a dict.
pool = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=1,
    max_size=5,
    kwargs={"row_factory": dict_row},
    open=True,
)


def query_all(sql: str, params=None) -> list[dict]:
    """Run a SELECT and return all rows as a list of dicts."""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()


def query_one(sql: str, params=None) -> dict | None:
    """Run a SELECT and return the first row as a dict (or None)."""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()


def execute(sql: str, params=None) -> dict | None:
    """
    Run an INSERT/UPDATE/DELETE. If the statement has a RETURNING clause,
    the affected row is returned as a dict. The change is committed.
    """
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            row = cur.fetchone() if cur.description else None
        # committed automatically when the "with pool.connection()" block exits
        return row
