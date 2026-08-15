"""
Account + transaction business logic - now backed by PostgreSQL (Neon).
Methods still return plain dicts so the controllers did not have to change.

WHY this layer exists at all, separate from the controllers:
the controllers deal with HTTP (status codes, request shapes, who is allowed to
call what). This file deals with what the bank actually DOES. Keeping them apart
means the money rules can be read, tested, and changed without touching routing
-- and the same rule cannot drift between two endpoints that both need it.

WHY this file imports 'pool' when the others only need the query helpers:
transfer() has to run several statements as ONE unit of work, which means
holding a single connection across all of them. query_all/query_one/execute each
borrow and return their own connection, so they cannot be combined into one
atomic transaction. See transfer() below.
"""

from decimal import Decimal

from app.data.database import execute, pool, query_all, query_one


class AccountService:

    # ---- accounts ----
    def open_account(self, customer_id, account_type, branch_id, initial_deposit=0):
        # RETURNING * hands back the newly created row (including the id the
        # database generated) in the SAME round trip, so we don't need a second
        # SELECT to find out what we just inserted.
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
        # Returns EVERY account. The RBAC filtering ("customers see only their
        # own") deliberately happens in the controller, not here -- see
        # account_controller.list_accounts. Keeping the raw read unfiltered is
        # what lets the manager Analytics endpoint reuse this same method.
        return query_all("SELECT * FROM accounts ORDER BY id")

    # ---- transactions ----
    def transfer(self, from_account_id, to_account_id, amount, description=""):
        # WHY Decimal(str(amount)) and not float(amount):
        # floats cannot represent most decimal fractions exactly -- 0.1 + 0.2 is
        # 0.30000000000000004 in binary floating point. On money that error
        # compounds into missing cents. Decimal does base-10 arithmetic exactly,
        # and matches the NUMERIC type of the balance column.
        # We convert via str() because Decimal(0.1) would inherit the float's
        # error, while Decimal("0.1") is exactly one tenth.
        amount = Decimal(str(amount))

        # Everything below runs in ONE database transaction: either all of it
        # commits, or none of it does (so money can't vanish mid-transfer).
        #
        # WHY that is non-negotiable here: a transfer is a debit AND a credit. If
        # the process died between the two UPDATEs, money would leave one account
        # without arriving in the other. Wrapping both in a single transaction
        # means a crash rolls the debit back rather than destroying funds.
        #
        # KNOWN LIMITATION: the balance is read with a plain SELECT, not
        # "SELECT ... FOR UPDATE", so the rows are not locked. Two transfers
        # running at the same instant could both read the same starting balance,
        # both decide there are enough funds, and together overdraw the account.
        # Fixing it means adding FOR UPDATE to the two SELECTs below so the
        # second transfer waits for the first to commit. Left as-is for now, but
        # it is a real race, not a theoretical one.
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM accounts WHERE id = %s", (from_account_id,))
                from_acct = cur.fetchone()
                cur.execute("SELECT * FROM accounts WHERE id = %s", (to_account_id,))
                to_acct = cur.fetchone()

                # Both guards return None rather than raising. WHY: this layer
                # has no idea it is being called over HTTP, so it must not pick
                # a status code. The controller turns None into the right 4xx.
                if from_acct is None or to_acct is None:
                    return None  # one of the accounts doesn't exist
                if from_acct["balance"] < amount:
                    return None  # not enough money -- refuse before touching anything

                # WHY "balance = balance - %s" instead of computing the new
                # total in Python and writing it back: the arithmetic happens
                # inside the database, on the value as it stands at write time.
                # Sending a precomputed total would overwrite any change made
                # since we read the row a moment ago.
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
        # Like get_all_accounts, this is unfiltered on purpose -- the caller
        # decides who is allowed to see what.
        return query_all("SELECT * FROM transactions ORDER BY id")


    def deposit(self, account_id, amount):
        # reject non-positive amounts or a missing account.
        # WHY amount <= 0 is blocked: without it, a "deposit" of -500 would
        # quietly become a withdrawal that skips the insufficient-funds check.
        if amount <= 0 or self.get_account(account_id) is None:
            return None
        # add the money to the account balance
        execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", (amount, account_id))
        # record it as a DEPOSIT transaction (money comes IN -> to_account_id set, from is NULL)
        return execute(
            """INSERT INTO transactions (from_account_id, to_account_id, amount, type, status, description, timestamp)
               VALUES (NULL, %s, %s, 'DEPOSIT', 'SUCCESS', 'Teller deposit', now())
               RETURNING * ;""",
            (account_id, amount),
        )

    def withdraw(self, account_id, amount):
        acct = self.get_account(account_id)
        # reject non-positive amounts, a missing account, or insufficient funds.
        # Mirror of the deposit guard: a negative withdrawal would otherwise be
        # a deposit with no upper bound.
        # NOTE: deposit and withdraw are NOT wrapped in an explicit transaction
        # the way transfer() is. Each does a balance UPDATE and then an INSERT,
        # so a crash between the two would move the money without recording the
        # ledger entry. transfer() shows the pattern that fixes it.
        if amount <= 0 or acct is None or acct["balance"] < amount:
            return None
        # subtract the money from the account balance
        execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", (amount, account_id))
        # record it as a WITHDRAWAL transaction (money goes OUT -> from_account_id set, to is NULL)
        return execute(
            """INSERT INTO transactions (from_account_id, to_account_id, amount, type, status, description, timestamp)
               VALUES (%s, NULL, %s, 'WITHDRAWAL', 'SUCCESS', 'Teller withdrawal', now())
               RETURNING *;""",
            (account_id, amount),
        )