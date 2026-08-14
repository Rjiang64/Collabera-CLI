"""
(MULTIFACTOR AUTHENTICATION CODE)
One-off migration: add the multi-factor auth columns to the users table.

Run from the project root:
    venv\\Scripts\\python.exe scripts\\migrate_mfa.py

Safe to run more than once -- every statement uses IF NOT EXISTS, so a second
run is a no-op rather than an error.

WHY each column:
  mfa_secret          the user's TOTP secret (base32). Set when they START
                      enrolling; the authenticator app holds the same value and
                      both sides derive the same 6-digit code from it + the clock.
  mfa_enabled         only flips to TRUE once the user has typed a correct code
                      back to us. Enrolling without confirming must NOT lock them
                      out, so the secret existing is not enough on its own.
  mfa_last_step       the last 30-second time-step we accepted. A TOTP code stays
                      valid for up to ~90s, so without this a code sniffed once
                      could be replayed. We refuse any step <= this value.
  mfa_failed_attempts consecutive bad codes, reset to 0 on success.
  mfa_locked_until    set when failed attempts cross the limit; blocks brute
                      forcing the 6-digit space (only 1,000,000 combinations).
"""

import sys
from pathlib import Path

# Make "app.*" importable when this file is run directly from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.database import execute, query_all  # noqa: E402

STATEMENTS = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_secret TEXT",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_last_step BIGINT",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_failed_attempts INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_locked_until TIMESTAMPTZ",
]


def main():
    for sql in STATEMENTS:
        execute(sql)
        print("  ok:", sql)

    print("\nusers table now has:")
    rows = query_all(
        """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'users'
        ORDER BY ordinal_position
        """
    )
    for r in rows:
        marker = "  <-- new" if r["column_name"].startswith("mfa_") else ""
        print(
            "   {:22} {:26} null={}{}".format(
                r["column_name"], r["data_type"], r["is_nullable"], marker
            )
        )


if __name__ == "__main__":
    main()
    print("\nMigration complete.")
