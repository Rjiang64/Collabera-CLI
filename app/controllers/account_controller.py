"""
Handles all HTTP routes for accounts AND transactions.
Both live here because they share one AccountService instance
(a transfer needs to read/update account balances directly).
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from app.models.account import AccountResponse, TransactionResponse
from app.services.account_service import AccountService

router = APIRouter(prefix="/api/v1", tags=["Accounts & Transactions"])

# one shared service so account balances stay in sync across requests
service = AccountService()


# ---- accounts ----
@router.post("/accounts", response_model=AccountResponse, status_code=201)
def open_account(customer_id: int, account_type: str, branch_id: int, initial_deposit: float = 0):
    return service.open_account(customer_id, account_type, branch_id, initial_deposit)


@router.get("/accounts", response_model=list[AccountResponse])
def list_accounts(branch_id: Optional[int] = Query(default=None), min_balance: Optional[float] = Query(default=None)):
    accounts = service.get_all_accounts()

    # filter down if query params were given
    if branch_id is not None:
        accounts = [a for a in accounts if a["branch_id"] == branch_id]
    if min_balance is not None:
        accounts = [a for a in accounts if a["balance"] >= min_balance]

    return accounts


@router.get("/accounts/{account_id}",response_model=AccountResponse)
def get_account(account_id: int):
    account = service.get_account(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    return account


# ---- transactions ----
@router.post("/transactions/transfer", response_model=TransactionResponse, status_code=201)
def transfer_money(from_account_id: int, to_account_id: int, amount: float, description: str = ""):
    result = service.transfer(from_account_id, to_account_id, amount, description)
    if result is None:
        raise HTTPException(status_code=400, detail="Transfer failed: check account ids and balance")
    return result


@router.get("/transactions", response_model=list[TransactionResponse])
def list_transactions(start_date: Optional[datetime] = Query(default=None), type: Optional[str] = Query(default=None)):
    transactions = service.get_all_transactions()

    if start_date is not None:
        transactions = [t for t in transactions if t["timestamp"] >= start_date]
    if type is not None:
        transactions = [t for t in transactions if t["type"].upper() == type.upper()]

    return transactions