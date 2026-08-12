# app/models/account.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional   

class AccountResponse(BaseModel):
    id: int
    customer_id: int
    account_type: str
    balance: float
    branch_id: int
    created_at: datetime
    is_active: bool


class TransactionResponse(BaseModel):
    id: int
    from_account_id: Optional[int] = None   # None for deposits
    to_account_id: Optional[int] = None      # None for withdrawals
    amount: float
    type: str
    status: str
    description: Optional[str] = None
    timestamp: datetime