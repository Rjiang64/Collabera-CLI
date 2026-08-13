"""
JWT creation and verification.

Two token types:
  * access  -> short-lived (minutes). Carries the user id, email, roles, and
               customer_id. Sent on EVERY request in the Authorization header.
  * refresh -> long-lived (days). Only used to get a new access token, so it
               carries just the user id.

Both are signed with JWT_SECRET using the HS256 algorithm. The signature is what
makes a token tamper-proof: if someone changes the payload, the signature no
longer matches and verification fails. If the secret ever leaks, anyone could
forge valid tokens -- which is why it lives in .env, never in the code.
"""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from dotenv import load_dotenv

""" 
Build the path to the project--root .env (three folders up from this file:
app/security/jwt_handler.py -> app/security -> app -> project root) and load it,
so JWT_SECRET is available  no matter which file imports this one first.
"""
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# -- configuration read from .env (with safe fallbacks if a value is missing) ---
SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me") # the secret signing key
ALGORITHM = "HS256"                                      # HMAC-SHA256 signing algorithm
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "30")) # access token lifetime
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))
# How long the user has to type their 6-digit code after the password step.
# Short on purpose: this token proves "password was correct" and nothing else,
# so it should not sit around being stealable.
MFA_TOKEN_MINUTES = int(os.getenv("MFA_TOKEN_MINUTES", "5"))



def _now() -> datetime:
    # Current time in UTC. Using UTC (not local time) keeps token expiry
    # consistent no matter what timezine the server runs in.
    return datetime.now(timezone.utc)


def create_access_token(user_id: int, email: str, roles: list[str], customer_id=None) -> str:
    """ Build a signed access token. The dictionary below is  the token's 'payload'
    -- the data packed inside the token that we can read back after verifying  it."""
    payload = {
        "sub": str(user_id), # 'subject' -- the standard JWT claim for "who this token is about"
        "email": email,
        "roles": roles,
        "customer_id": customer_id,
        "type": "access",
        "iat": _now(),
        "exp": _now() + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    # jwt.encode signs the patload with our SECRET and returns the token string.
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """ Build a long-lived refresh token. It only carries the user id, because its
    single job is to prove identity long enough to hand out a fresh access token."""
    payload = {
        "sub": str(user_id), # who the token is about
        "type": "refresh",   # marks this as a refresh token ( cant be used to access routes)
        "iat": _now(),       # isseued-at-time
        "exp": _now() + timedelta(days=REFRESH_TOKEN_DAYS), # longer expiry than the access token
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

def create_mfa_token(user_id: int) -> str:
    """
    Build the short-lived token handed out AFTER a correct password but BEFORE
    the 6-digit code. It is the server's way of remembering "this person passed
    step one" without keeping session state.

    SECURITY: type is "mfa_pending", NOT "access". get_current_user() only
    accepts type == "access", so this token cannot open a single protected
    route -- its one and only use is POST /auth/mfa/verify. That distinction is
    what stops the password alone from being enough to get into the app.
    """
    payload = {
        "sub": str(user_id),   # who is half-way through logging in
        "type": "mfa_pending", # deliberately not "access"
        "iat": _now(),
        "exp": _now() + timedelta(minutes=MFA_TOKEN_MINUTES),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
     """
    Verify a token and return its payload (the dictionary we packed in above).

    jwt.decode does three things at once:
      1. checks the signature matches our SECRET (proves it wasn't tampered with),
      2. checks the token hasn't expired (the 'exp' field),
      3. returns the payload if both pass.

    It RAISES on failure:
      - jwt.ExpiredSignatureError if the token is past its 'exp' time,
      - jwt.PyJWTError (the parent error) if the signature is invalid or the
        token is malformed.
    The caller (our security dependency) catches these and returns a 401.
    """
     return jwt.decode(token, SECRET, algorithms=[ALGORITHM])

