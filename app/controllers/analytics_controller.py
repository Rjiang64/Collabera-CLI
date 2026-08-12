""" Branch analytics --MANAGER-ONLY routes (a target for the Postman 403 test).
This controller exists mainly to give the security test suite an endpoint that
ONLY managers/admins can reach. A CUSTOMER hitting it should be denied (403),
which is exactly what the Phase 05-B Postman tests check.
"""
from fastapi import APIRouter, Depends
# require_roles is our RBAC gate -- it blocks anyone without an allowed role.
from app.security.dependencies import require_roles
# We reuse the account service to read account data for the summary.
from app.services.account_service import AccountService

# Group these routes under the /api/v1/analytics path.
#
# WHY we set a prefix here:
#   1. Every route in this file automatically starts with /api/v1/analytics, so
#      we don't repeat that path on each @router.get -- we just write the last
#      part (e.g. "/branch-summary" -> /api/v1/analytics/branch-summary). Less
#      repetition, and if the base path ever changes we edit it in one place.
#   2. The "/api/v1" part is versioning: putting a version in the URL means we
#      can release a future "/api/v2" with different behavior WITHOUT breaking
#      existing clients still calling v1. It's a standard REST convention.
#   3. "/analytics" groups all manager-analytics endpoints under one clear,
#      predictable namespace, separate from /customers, /accounts, etc. -- so
#      the API stays organized and easy to navigate.
#
# 'tags' is unrelated to the URL -- it just labels this section in the /docs
# (Swagger) page so these routes appear grouped under "Analytics (Manager)".
router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics (Manager)"])

# One shared service instance for every route in this file.
service = AccountService()

# GET /api/v1/analytics/branch-summary
# The 'dependencies=[Depends(require_roles("BRANCH_MANAGER", "ADMIN"))]' is the
# security part: before this function runs, require_roles checks the caller's
# JWT roles. If they're not a BRANCH_MANAGER or ADMIN, it raises 403 and the
# function below never executes. (No token at all -> 401.)
@router.get("/branch-summary",
            dependencies=[Depends(require_roles("BRANCH_MANAGER", "ADMIN"))])

def branch_summary():
    """Per-branch account count and total balance. Managers/admins only."""
    # Pull every account from the database.
    accounts = service.get_all_accounts()

    # Build a dictionary keyed by branch_id, aggregating stats per branch.
    #
    # WHY: the endpoint needs ONE row per branch (its total account count and
    # total balance), but the data above is one row per ACCOUNT. So we need a
    # place to keep a running total for each branch as we loop. We key the dict
    # by branch_id so that, for any account, we can instantly find "the running
    # total for THIS account's branch" and add to it -- no searching required.
    # (A list would force us to scan it every time to find the right branch.)
    # This is the classic "group-by aggregation" pattern -- the same thing SQL
    # does with: SELECT branch_id, COUNT(*), SUM(balance) ... GROUP BY branch_id.
    summary = {}

    for a in accounts:
        b = a["branch_id"] # which branch this account belongs to

        # setdefault handles the "first time vs. already seen" problem in one line.
        #
        # THE PROBLEM: as we loop, each account belongs to a branch that we've
        # either never seen before, or already started counting. Those two cases
        # need different handling -- create a new running total, or add to the
        # existing one -- and we'd normally write an if/else to tell them apart:
        #
        #     if b not in summary:
        #         summary[b] = {"branch_id": b, "account_count": 0, "total_balance": 0.0}
        #     row = summary[b]
        #
        # WHY setdefault: it does exactly that if/else in a single call --
        #   - if branch b is NOT in the dict yet -> it inserts the fresh row
        #     (count 0, balance 0.0) and returns it,
        #   - if branch b IS already there -> it ignores the default and returns
        #     the row that's already stored.
        # Either way we get back the correct row to update, so every account in a
        # branch keeps adding to the SAME running total. That's what lets the
        # counts and balances accumulate branch-by-branch in a single pass,
        # without a separate "have I seen this branch?" check.
        row = summary.setdefault(b, {"branch_id": b, "account_count": 0, "total_balance": 0.0})
        row["account_count"] += 1 # one more account in this branch
        row["total_balance"] += float(a["balance"])  # add its balance to the branch total
         # float(...) converts the DB's Decimal balance into a plain number for JSON.

    # summary is {branch_id: {...}, ...}; return just the finished per-branch rows.
    return list(summary.values()) 
                                     
                                