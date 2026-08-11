"""
Account + transaction business logic - now backed by PostgreSQL (Neon).
Methods still return plain dicts so the controllers did not have to change.
"""

from decimal import Decimal

from app.data.database import execute, pool, query_all, query_one


class AccountService:

    # ---- accounts ----
    def open_account(self, customer_id, account_type, branch_id, initial_deposit=0):
        return execute(
            """
            INSERT INTO accounts (customer_id, account_type, balance, branch_id)
            VALUES (%s, %s, %s, %s)
            RETURNING *
            """,
            (customer_id, account_type, initial_deposit, branch_id),
        )

    def get_account(self, account_id):
        return query_one("SELECT * FROM accounts WHERE id = %s", (account_id,))

    def get_all_accounts(self):
        return query_all("SELECT * FROM accounts ORDER BY id")

    # ---- transactions ----
    def transfer(self, from_account_id, to_account_id, amount, description=""):
        amount = Decimal(str(amount))  # exact money math, matches NUMERIC column

        # Everything below runs in ONE database transaction: either all of it
        # commits, or none of it does (so money can't vanish mid-transfer).
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM accounts WHERE id = %s", (from_account_id,))
                from_acct = cur.fetchone()
                cur.execute("SELECT * FROM accounts WHERE id = %s", (to_account_id,))
                to_acct = cur.fetchone()

                if from_acct is None or to_acct is None:
                    return None  # one of the accounts doesn't exist
                if from_acct["balance"] < amount:
                    return None  # not enough money

                cur.execute(
                    "UPDATE accounts SET balance = balance - %s WHERE id = %s",
                    (amount, from_account_id),
                )
                cur.execute(
                    "UPDATE accounts SET balance = balance + %s WHERE id = %s",
                    (amount, to_account_id),
                )
                cur.execute(
                    """
                    INSERT INTO transactions
                        (from_account_id, to_account_id, amount, type, status, description)
                    VALUES (%s, %s, %s, 'TRANSFER', 'SUCCESS', %s)
                    RETURNING *
                    """,
                    (from_account_id, to_account_id, amount, description),
                )
                return cur.fetchone()

    def get_all_transactions(self):
        return query_all("SELECT * FROM transactions ORDER BY id")