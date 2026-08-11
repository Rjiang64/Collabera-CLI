# app/models/account.py
from pydantic import BaseModel
from datetime import datetime

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
    from_account_id: int
    to_account_id: int
    amount: float
    type: str
    timestamp: datetime
    status: str
    description: str