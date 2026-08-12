"""Creates the users table (identity + roles). Run once against the database."""
from app.data.database import execute

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name     TEXT,
    roles         TEXT[] NOT NULL DEFAULT ARRAY['CUSTOMER'],
    customer_id   INTEGER,                       -- links a CUSTOMER user to customers(id)
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
"""

if __name__ == "__main__":
    for stmt in [s.strip() for s in SCHEMA.split(";") if s.strip()]:
        execute(stmt + ";")
    print("users table ready")