""" Branch analytics --MANAGER-ONLY routes (a target for the Postman 403 test)."""
from fastapi import APIRouter, Depends

from app.security.dependencies import require_roles
from app.services.account_service import AccountService

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics (Manager)"])
service = AccountService()

@router.get("/branch-summary",
            dependencies=[Depends(require_roles("BRANCH_MANAGER", "ADMIN"))])

def branch_summary():
    """Per-branch account count and total balance. Managers/admins only."""
    accounts = service.get_all_accounts()
    summary = {}
    for a in accounts:
        b = a["branch_id"]
        row = summary.setdefault(b, {"branch_id": b, "account_count": 0, "total_balance": 0.0})
        row["account_count"] += 1
        row["total_balance"] += float(a["balance"])
    return list(summary.values())
                                     
                                