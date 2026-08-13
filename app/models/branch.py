# app/models/branch.py
"""
Pydantic model for a branch.

WHY there is only a Response model here (no BranchCreate / BranchUpdate):
branches are REFERENCE DATA -- a fixed list of physical locations that the app
reads but never creates or edits through the API. Compare this with customers,
which have Create/Update/Response models because customers are added and edited
constantly. Adding write models here would imply an API surface that
branch_controller deliberately does not expose.

WHY a response model at all, when branch_controller returns raw dicts:
it documents the exact shape a branch row has, and it is ready for the day the
branch routes want the same validation the customer routes get. FastAPI uses a
response_model to both validate what we send AND to generate the /docs schema.
"""
from pydantic import BaseModel


class BranchResponse(BaseModel):
    """One branch as returned by GET /api/v1/branches."""
    id: int
    name: str          # e.g. "Branch 1"
    location: str      # street address, shown in the manager Analytics table
    manager: str       # the person running the branch (a name, not a user id)
    phone: str
