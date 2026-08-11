"""
Handles HTTP routes for branches.
Branches are reference data, so this reads straight from the database
via the shared query helpers - no service layer needed for read-only data.
"""

from fastapi import APIRouter, HTTPException

from app.data.database import query_all, query_one

router = APIRouter(prefix="/api/v1/branches", tags=["Branches"])


@router.get("")
def list_branches():
    return query_all("SELECT * FROM branches ORDER BY id")


@router.get("/{branch_id}")
def get_branch(branch_id: int):
    branch = query_one("SELECT * FROM branches WHERE id = %s", (branch_id,))
    if branch is None:
        raise HTTPException(status_code=404, detail=f"Branch {branch_id} not found")
    return branch