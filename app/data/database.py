
import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Copy .env.example to .env.")


def connect():
    # open a fresh connection that returns rows as dicts
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def query_all(sql, params=None):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchall()


def query_one(sql, params=None):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone()


def execute(sql, params=None):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone() if cur.description else None
