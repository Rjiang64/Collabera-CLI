"""
Handles HTTP routes for branches.
Branches are just reference data, so this reads straight from
sample_data.py - no service layer needed for read-only data.
"""

from fastapi import APIRouter, HTTPException
from app.data.sample_data import BRANCHES

router = APIRouter(prefix="/api/v1/branches", tags=["Branches"])


@router.get("")
def list_branches():
    return list(BRANCHES.values())


@router.get("/{branch_id}")
def get_branch(branch_id: int):
    branch = BRANCHES.get(branch_id)
    if branch is None:
        raise HTTPException(status_code=404, detail=f"Branch {branch_id} not found")
    return branch