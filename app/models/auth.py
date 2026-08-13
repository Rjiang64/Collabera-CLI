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


class LoginResponse(BaseModel):
    """
    What POST /login returns. It has two shapes:

      MFA off -> mfa_required=False and the two tokens are populated, exactly
                 like the old TokenResponse. Existing clients keep working.
      MFA on  -> mfa_required=True and mfa_token is populated, while
                 access_token/refresh_token stay None. The caller must then
                 post the 6-digit code to /mfa/verify to get real tokens.
    """
    mfa_required: bool = False
    mfa_token: Optional[str] = None         # short-lived, ONLY valid at /mfa/verify
    access_token: Optional[str] = None      # None until the second factor passes
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class MfaVerifyRequest(BaseModel):
    """Body for POST /mfa/verify -- finishes a login that needs a second factor."""
    mfa_token: str                          # handed out by /login
    code: str                               # the 6 digits from the authenticator app


class MfaCodeRequest(BaseModel):
    """Body for POST /mfa/activate and /mfa/disable (caller is already logged in)."""
    code: str


class MfaSetupResponse(BaseModel):
    """
    What POST /mfa/setup returns so the phone can enroll.

    NOTE: 'secret' is returned exactly once, to the already-authenticated user
    who is enrolling, so they can type it in manually if the camera fails. It is
    never exposed by /me or any listing route.
    """
    secret: str
    otpauth_uri: str
    qr_data_uri: str                        # SVG QR, ready for <img src="...">


class MfaStatusResponse(BaseModel):
    """Whether MFA is on, and whether a secret is waiting to be confirmed."""
    mfa_enabled: bool
    enrollment_pending: bool


class UserResponse(BaseModel):
    """Safe view of a user -- note there is NO password field, so we can never
    accidentally leak the hash in an API response."""
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    roles: List[str]                        # always has a value once the user exists
    customer_id: Optional[int] = None
    is_active: bool                         # False means the account is deactivated
    mfa_enabled: bool = False               # drives the MFA badge in the UI