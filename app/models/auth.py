"""Pydantic models for the auth routes -- these define the shape of what comes
in (requests) and goes out (responses), and FastAPI validates against them."""
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    """Body for POST /register."""
    email: EmailStr                       # EmailStr auto-validates it's a real email format
    password: str
    full_name: Optional[str] = None
    roles: Optional[List[str]] = None     # optional; defaults to CUSTOMER in the service
    customer_id: Optional[int] = None     # links a CUSTOMER login to their customer record


class TokenResponse(BaseModel):
    """What /login and /refresh return: the two tokens."""
    access_token: str                       # short-lived token, used to access protected routes
    refresh_token: str                      # long-lived token, used to get a new access_token
    token_type: str = "bearer"              # tells the client how to send the token


class RefreshRequest(BaseModel):
    """Body for POST /refresh."""
    refresh_token: str                      # client sends this back to get a new access_token


class UserResponse(BaseModel):
    """Safe view of a user -- note there is NO password field, so we can never
    accidentally leak the hash in an API response."""
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    roles: List[str]                        # always has a value once the user exists
    customer_id: Optional[int] = None
    is_active: bool                         # False means the account is deactivated