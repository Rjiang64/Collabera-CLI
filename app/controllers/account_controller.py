"""
Handles all HTTP routes for accounts AND transactions.

SECURITY (Phase 05): every route now requires a valid JWT. RBAC rules:
  - CUSTOMER        : sees/uses only their OWN accounts; can transfer from them.
  - TELLER          : can open accounts and deposit/withdraw for customers.
  - BRANCH_MANAGER  : can view all accounts/transactions.
  - ADMIN           : full access.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.models.account import AccountResponse, TransactionResponse
from app.security.dependencies import get_current_user, require_roles
from app.services.account_service import AccountService

router = APIRouter(prefix="/api/v1", tags=["Accounts & Transactions"])
service = AccountService()

STAFF = {"TELLER", "BRANCH_MANAGER", "ADMIN"}


def _is_staff(user: dict) -> bool:
    # True if the user holds any staff role
    return bool(STAFF & set(user["roles"]))


def _require_owns_account(user: dict, account: dict) -> None:
    # Staff may access any account; a CUSTOMER may only access their own.
    if _is_staff(user):
        return
    if account["customer_id"] != user.get("customer_id"):
        raise HTTPException(status_code=403, detail="You can only access your own accounts")


# ---- accounts ----
@router.post("/accounts", response_model=AccountResponse, status_code=201,
             dependencies=[Depends(require_roles("TELLER", "BRANCH_MANAGER", "ADMIN"))])
def open_account(customer_id: int, account_type: str, branch_id: int, initial_deposit: float = 0):
    # require_roles above blocks anyone who isn't staff (403) before we get here
    return service.open_account(customer_id, account_type, branch_id, initial_deposit)


@router.get("/accounts", response_model=list[AccountResponse])
def list_accounts(
    branch_id: Optional[int] = Query(default=None),
    min_balance: Optional[float] = Query(default=None),
    user: dict = Depends(get_current_user),
):
    accounts = service.get_all_accounts()

    # RBAC: a CUSTOMER only sees their own accounts
    if not _is_staff(user):
        accounts = [a for a in accounts if a["customer_id"] == user.get("customer_id")]

    # then apply the normal query-param filters
    if branch_id is not None:
        accounts = [a for a in accounts if a["branch_id"] == branch_id]
    if min_balance is not None:
        accounts = [a for a in accounts if a["balance"] >= min_balance]

    return accounts


@router.get("/accounts/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, user: dict = Depends(get_current_user)):
    account = service.get_account(account_id)
    if account is None:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    _require_owns_account(user, account)      # 403 unless staff or the owner
    return account


# ---- teller operations: deposit / withdraw ----
@router.post("/accounts/{account_id}/deposit", response_model=TransactionResponse, status_code=201,
             dependencies=[Depends(require_roles("TELLER", "BRANCH_MANAGER", "ADMIN"))])
def deposit(account_id: int, amount: float):
    result = service.deposit(account_id, amount)
    if result is None:
        raise HTTPException(status_code=400, detail="Deposit failed: check account id and amount")
    return result


@router.post("/accounts/{account_id}/withdraw", response_model=TransactionResponse, status_code=201,
             dependencies=[Depends(require_roles("TELLER", "BRANCH_MANAGER", "ADMIN"))])
def withdraw(account_id: int, amount: float):
    result = service.withdraw(account_id, amount)
    if result is None:
        raise HTTPException(status_code=400, detail="Withdrawal failed: check account id, amount, and balance")
    return result


# ---- transactions ----
@router.post("/transactions/transfer", response_model=TransactionResponse, status_code=201)
def transfer_money(
    from_account_id: int, to_account_id: int, amount: float,
    description: str = "", user: dict = Depends(get_current_user),
):
    # RBAC: a CUSTOMER may only transfer FROM an account they own
    source = service.get_account(from_account_id)
    if source is None:
        raise HTTPException(status_code=404, detail=f"Account {from_account_id} not found")
    _require_owns_account(user, source)

    result = service.transfer(from_account_id, to_account_id, amount, description)
    if result is None:
        raise HTTPException(status_code=400, detail="Transfer failed: check account ids and balance")
    return result


@router.get("/transactions", response_model=list[TransactionResponse])
def list_transactions(
    start_date: Optional[datetime] = Query(default=None),
    type: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user),
):
    transactions = service.get_all_transactions()

    # RBAC: a CUSTOMER only sees transactions involving their own accounts
    if not _is_staff(user):
        my_ids = {a["id"] for a in service.get_all_accounts()
                  if a["customer_id"] == user.get("customer_id")}
        transactions = [t for t in transactions
                        if t.get("from_account_id") in my_ids or t.get("to_account_id") in my_ids]

    if start_date is not None:
        transactions = [t for t in transactions if t["timestamp"].date() >= start_date.date()]
    if type is not None:
        transactions = [t for t in transactions if t["type"].upper() == type.upper()]

    return transactions