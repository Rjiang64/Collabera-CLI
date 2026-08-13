# app/models/account.py
"""
Pydantic models for accounts and transactions.

These are RESPONSE models -- they describe what leaves the API, and FastAPI
validates every response against them before it goes out. That is a safety net,
not a formality: if a query ever selected an extra column (say a password hash
or an MFA secret), a response_model would drop it rather than leak it.

WHY there is no AccountCreate model: opening an account is done with query
parameters on POST /accounts (customer_id, account_type, branch_id,
initial_deposit) rather than a JSON body, so FastAPI validates those directly
from the function signature and no body model is needed.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AccountResponse(BaseModel):
    """One bank account as returned by the /accounts routes."""
    id: int
    customer_id: int          # who owns it -- the RBAC checks compare against this
    account_type: str         # "Checking" / "Savings"
    balance: float
    # WHY float here but Decimal in the service layer: the database column is
    # NUMERIC and AccountService does its money math in Decimal so cents can
    # never drift. We only widen to float at the very edge, for JSON, because
    # JSON has no decimal type. Arithmetic must not happen at this layer.
    branch_id: int
    created_at: datetime
    is_active: bool           # soft-delete flag; closed accounts stay on record


class TransactionResponse(BaseModel):
    """
    One ledger entry. The two account ids are optional because the same table
    stores three different kinds of movement:
        TRANSFER   -> both ids set (money moved between two accounts)
        DEPOSIT    -> from_account_id is None (money entered the bank)
        WITHDRAWAL -> to_account_id is None (money left the bank)
    Reading a None tells you which kind it was, which is why the UI prints "-"
    for the missing side rather than treating it as an error.
    """
    id: int
    from_account_id: Optional[int] = None   # None for deposits
    to_account_id: Optional[int] = None      # None for withdrawals
    amount: float
    type: str                                # TRANSFER / DEPOSIT / WITHDRAWAL
    status: str                              # SUCCESS / (room for FAILED, PENDING)
    description: Optional[str] = None
    timestamp: datetime
