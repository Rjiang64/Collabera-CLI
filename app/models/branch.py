# app/models/branch.py
from pydantic import BaseModel

class BranchResponse(BaseModel):
    id: int
    name: str
    location: str
    manager: str
    phone: str