"""
Pydantic models for customers.
These define what a valid request body looks like, and what
gets sent back in a response. FastAPI uses these to validate
incoming JSON automatically.
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class CustomerCreate(BaseModel):
    # required fields when creating a new customer
    name: str
    email: EmailStr
    phone: str
    address: str
    branch_id: int = 1


class CustomerUpdate(BaseModel):
    # everything optional - only send the fields you want to change
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    branch_id: Optional[int] = None


class CustomerResponse(BaseModel):
    # what gets sent back to the client
    id: int
    name: str
    email: str
    phone: str
    address: str
    branch_id: int
    created_at: datetime
    is_active: bool