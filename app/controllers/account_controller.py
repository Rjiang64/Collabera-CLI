"""
Handles all HTTP routes for accounts AND transactions.

WHY accounts and transactions share one file: a money transfer has to read and
update account balances directly, so both live together and share a single
AccountService instance -- keeping that logic in one place.

SECURITY (Phase 05): every route now requires a valid JWT. RBAC rules:
  - CUSTOMER        : sees/uses only their OWN accounts; can transfer from them.
  - TELLER          : can open accounts and deposit/withdraw for customers.
  - BRANCH_MANAGER  : can view all accounts/transactions.
  - ADMIN           : full access.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

# Pydantic response models -- FastAPI validates every response against these.
from app.models.account import AccountResponse, TransactionResponse

# Security dependencies: get_current_user verifies the JWT and returns the user;
# require_roles is the RBAC gate that blocks users without an allowed role.
from app.security.dependencies import get_current_user, require_roles
from app.services.account_service import AccountService

# prefix -> every route below starts with /api/v1 (versioned base path).
# tags   -> groups these routes under one heading in the /docs (Swagger) page.
router = APIRouter(prefix="/api/v1", tags=["Accounts & Transactions"])

# One shared service instance so all routes work against the same data layer.
service = AccountService()

# The set of roles we treat as "staff". Kept as a constant so we define it once
# and reuse it in every check below -- if the list of staff roles ever changes,
# we edit it here in one place instead of hunting through every route.
STAFF = {"TELLER", "BRANCH_MANAGER", "ADMIN"}


def _is_staff(user: dict) -> bool:
     # Set intersection (&): is there any overlap between the user's roles and the
    # STAFF set? bool(...) turns the resulting set into True/False. This answers
    # "does this user hold at least one staff role?" in one expression.
    # True if the user holds any staff role
    return bool(STAFF & set(user["roles"]))


def _require_owns_account(user: dict, account: dict) -> None:
    # Shared ownership check, factored into a helper so we don't repeat it in
    # every route. This is the "customers see only their own data" rule.
    #
    # Staff (teller/manager/admin) may access ANY account -> allow immediately.
    # Staff may access any account; a CUSTOMER may only access their own.
    if _is_staff(user):
        return
    # Otherwise the caller is a CUSTOMER: the account's owner (customer_id) must
    # match the customer_id stored in THEIR token. If not, deny with 403.
    if account["customer_id"] != user.get("customer_id"):
        raise HTTPException(status_code=403, detail="You can only access your own accounts")


# ---- accounts ----
# WHY dependencies=[Depends(require_roles(...))]: this is a ROLE GATE that runs
# BEFORE the function. Only staff may open accounts; a customer trying this is
# rejected with 403 before open_account ever executes. (No token at all -> 401.)
@router.post("/accounts", response_model=AccountResponse, status_code=201,
             dependencies=[Depends(require_roles("TELLER", "BRANCH_MANAGER", "ADMIN"))])
def open_account(customer_id: int, account_type: str, branch_id: int, initial_deposit: float = 0):
     # By the time we're here, require_roles has already confirmed the caller is
    # staff, so we can safely just do the work.
    # require_roles above blocks anyone who isn't staff (403) before we get here
    return service.open_account(customer_id, account_type, branch_id, initial_deposit)


@router.get("/accounts", response_model=list[AccountResponse])
def list_accounts(
    branch_id: Optional[int] = Query(default=None),
    min_balance: Optional[float] = Query(default=None),
    # Depends(get_current_user) forces a valid token AND hands us the caller's
    # identity (id, roles, customer_id) so we can filter by who they are.
    user: dict = Depends(get_current_user),
):
    accounts = service.get_all_accounts()

    # RBAC: staff see every account, but a CUSTOMER must only see their own.
    # WHY here (not a role gate): we don't want to DENY customers this route --
    # we want to give them a FILTERED view, so the rule lives in the body.
    if not _is_staff(user):
        accounts = [a for a in accounts if a["customer_id"] == user.get("customer_id")]

    # then apply the normal query-param filters (branch, minimum balance).
    # These run AFTER the RBAC filter, so a customer filtering still only ever
    # searches within their own accounts.
    
    if branch_id is not None:
        accounts = [a for a in accounts if a["branch_id"] == branch_id]
    if min_balance is not None:
        accounts = [a for a in accounts if a["balance"] >= min_balance]

    return accounts


@router.get("/accounts/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, user: dict = Depends(get_current_user)):
    account = service.get_account(account_id)
        # 404 if the account simply doesn't exist (service returns None).
    if account is None:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    # Ownership check: 403 unless the caller is staff or the account's owner.
    # WHY a role gate wouldn't work here: the allowed answer depends on WHICH
    # account is requested, not just the caller's role -- so we check per-record.
    _require_owns_account(user, account)      # 403 unless staff or the owner
    return account


# ---- teller operations: deposit / withdraw ----
# Both are role-gated to staff: only a teller/manager/admin can move money on a
# customer's behalf. A customer cannot deposit/withdraw directly -> 403.
@router.post("/accounts/{account_id}/deposit", response_model=TransactionResponse, status_code=201,
             dependencies=[Depends(require_roles("TELLER", "BRANCH_MANAGER", "ADMIN"))])
def deposit(account_id: int, amount: float):
    result = service.deposit(account_id, amount)
     # service returns None on a bad request (missing account / non-positive
     # amount); we translate that into a 400 Bad Request.
    if result is None:
        raise HTTPException(status_code=400, detail="Deposit failed: check account id and amount")
    return result


@router.post("/accounts/{account_id}/withdraw", response_model=TransactionResponse, status_code=201,
             dependencies=[Depends(require_roles("TELLER", "BRANCH_MANAGER", "ADMIN"))])
def withdraw(account_id: int, amount: float):
    result = service.withdraw(account_id, amount)
    # None here also covers "insufficient funds" -> 400 Bad Request.
    if result is None:
        raise HTTPException(status_code=400, detail="Withdrawal failed: check account id, amount, and balance")
    return result


# ---- transactions ----
@router.post("/transactions/transfer", response_model=TransactionResponse, status_code=201)
def transfer_money(
    from_account_id: int, to_account_id: int, amount: float,
    description: str = "", user: dict = Depends(get_current_user),
):
     # WHY no role gate: customers ARE allowed to transfer -- but only FROM an
    # account they own. So we can't block by role; we check ownership of the
    # source account instead.
    # RBAC: a CUSTOMER may only transfer FROM an account they own
    source = service.get_account(from_account_id)
    if source is None:
        raise HTTPException(status_code=404, detail=f"Account {from_account_id} not found")
    # Ownership check on the SOURCE account: a customer can't spend from an
    # account that isn't theirs. Staff bypass this and can move any funds.
    _require_owns_account(user, source)
    
 # Only after auth + ownership pass do we actually move the money.
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
        # First find every account id the customer owns...
        my_ids = {a["id"] for a in service.get_all_accounts()
                  if a["customer_id"] == user.get("customer_id")}
        # ...then keep only transactions where their account is either the
        # sender OR the receiver. (Using a set for my_ids makes the 'in' check
        # fast even with many accounts.)
        transactions = [t for t in transactions
                        if t.get("from_account_id") in my_ids or t.get("to_account_id") in my_ids]

    # Optional date filter. We compare .date() on both sides so a plain date
    # like 2026-01-01 matches correctly and we avoid timezone-aware vs naive
    # datetime comparison errors.
    if start_date is not None:
        transactions = [t for t in transactions if t["timestamp"].date() >= start_date.date()]
    # Optional type filter, case-insensitive so ?type=transfer and ?type=TRANSFER
    # both work.
    if type is not None:
        transactions = [t for t in transactions if t["type"].upper() == type.upper()]

    return transactions
