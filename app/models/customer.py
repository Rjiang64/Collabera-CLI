"""
Valid customer request
FastAPI reads rejects bad requests automatically,
before any of our code runs.
"""
 
from typing import Optional
 
from pydantic import BaseModel
 
 
class CustomerCreate(BaseModel):
    """
    The body for POST /api/v1/customers  (creating new customer).
    Every field is required
    """
    name: str
    email: str
    phone: str
    address: str
    branch_id: int 
 
 
class CustomerUpdate(BaseModel):
    """
    The body for PUT /api/v1/customers/{id} (changing someone).
 
    Every field is Optional and defaults to None, so the sender
    can update just ONE thing:
 
        {"address": "999 New St"}
 
    ...without having to resend name, email, and phone.
    """
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    branch_id: Optional[int] = None
 