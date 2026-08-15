"""Authentication routes: register, login, refresh, me."""
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.models.auth import (
    LoginResponse, MfaCodeRequest, MfaSetupResponse, MfaStatusResponse,
    MfaVerifyRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse,
)
from app.security.dependencies import get_current_user
from app.security.jwt_handler import (
    create_access_token, create_mfa_token, create_refresh_token, decode_token,
)
from app.services.auth_service import AuthService


router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])
service = AuthService()  # one shared instance, same pattern as your other controllers



@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest):

    # create the user; service returns None if the email is already taken

    user = service.register(
        payload.email, payload.password, payload.full_name,
        payload.roles, payload.customer_id,
    )
    if user is None:

        # 409 = "conflict" -- the right status code for "this already exists"
        raise HTTPException(status_code=409, detail="Email already registered")
    return user



@router.post("/login", response_model=LoginResponse)
def login(form: OAuth2PasswordRequestForm = Depends()):

    # OAuth2 form sends 'username' + 'password'; we treat 'username' as the email.
    # (this is a built-in FastAPI form type, not something we wrote ourselves --
    # it expects form data, not JSON, so Postman/the frontend must send it that way)

    user = service.authenticate(form.username, form.password)
    if user is None:

        # don't say "wrong password" specifically -- that tells an attacker
        # the email exists. "Incorrect email or password" is deliberately vague.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"}, # standard header for a 401 on this flow

        )

    #(MULTIFACTOR AUTHENTICATION CODE)
    # SECOND FACTOR GATE.
    # The password was right, but if this account has MFA switched on that is
    # only step one. We deliberately do NOT mint an access token here -- handing
    # one out now would make the second factor decorative, since the caller
    # could just use it and skip the code entirely. Instead they get a
    # short-lived mfa_pending token that ONLY /mfa/verify accepts.
    if user.get("mfa_enabled"):
        return LoginResponse(
            mfa_required=True,
            mfa_token=create_mfa_token(user["id"]),
        )

    # No MFA on this account -- same response shape as before, tokens included.
    return LoginResponse(
        access_token=create_access_token(
            user["id"], user["email"], user["roles"], user.get("customer_id")
        ),
        refresh_token=create_refresh_token(user["id"]),
    )


@router.post("/mfa/verify", response_model=TokenResponse)
def mfa_verify(payload: MfaVerifyRequest):
    """
    Step two of login: exchange the mfa_pending token + a 6-digit code for real
    tokens. This is the ONLY route that accepts an mfa_pending token.
    """
    try:
        data = decode_token(payload.mfa_token)
    except jwt.PyJWTError:
        # covers expired (took too long to type the code), tampered, malformed
        raise HTTPException(status_code=401, detail="Login session expired. Sign in again.")

    # Reject anything that isn't specifically the half-authenticated token --
    # an access or refresh token must not be usable to complete an MFA login.
    if data.get("type") != "mfa_pending":
        raise HTTPException(status_code=401, detail="Invalid login session.")

    user, error = service.verify_mfa_code(int(data["sub"]), payload.code)
    if user is None:
        # 401 with the specific reason (wrong code / reused / locked out). This
        # is safe to be specific about: the caller already proved the password.
        raise HTTPException(status_code=401, detail=error)

    return TokenResponse(
        access_token=create_access_token(
            user["id"], user["email"], user["roles"], user.get("customer_id")
        ),
        refresh_token=create_refresh_token(user["id"]),
    )


@router.get("/mfa/status", response_model=MfaStatusResponse)
def mfa_status(current=Depends(get_current_user)):
    """Does this account have MFA on, and is a secret waiting to be confirmed?"""
    row = service._get_user_mfa(current["id"])
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return MfaStatusResponse(
        mfa_enabled=bool(row["mfa_enabled"]),
        enrollment_pending=bool(row["mfa_secret"]) and not row["mfa_enabled"],
    )


@router.post("/mfa/setup", response_model=MfaSetupResponse)
def mfa_setup(current=Depends(get_current_user)):
    """
    Begin enrollment: generate a secret and return the QR for the phone.
    Requires a valid access token, so only the account owner can enroll it.
    MFA is NOT active yet -- /mfa/activate finishes the job.
    """
    result = service.start_mfa_enrollment(current["id"])
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    return MfaSetupResponse(**result)


@router.post("/mfa/activate")
def mfa_activate(payload: MfaCodeRequest, current=Depends(get_current_user)):
    """Confirm enrollment by proving the phone produces the right code."""
    ok, error = service.activate_mfa(current["id"], payload.code)
    if not ok:
        raise HTTPException(status_code=400, detail=error)
    return {"mfa_enabled": True, "message": "Multi-factor authentication is now on."}


@router.post("/mfa/disable")
def mfa_disable(payload: MfaCodeRequest, current=Depends(get_current_user)):
    """Turn MFA off. Requires a CURRENT code, not just a valid session."""
    ok, error = service.disable_mfa(current["id"], payload.code)
    if not ok:
        raise HTTPException(status_code=400, detail=error)
    return {"mfa_enabled": False, "message": "Multi-factor authentication is off."}


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest):
    # verify the refresh token, then issue a fresh pair of tokens
    try:
        data = decode_token(payload.refresh_token)
    except jwt.PyJWTError:
        # covers expired, tampered, or just malformed tokens all at once
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # make sure someone isn't trying to use an access_token here instead --
    # only a token created as type="refresh" is allowed to mint new tokens
    if data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    # the token was valid, but double check the user behind it still exists
    # (e.g. they could've been deleted after the token was issued)
    user = service.get_user(int(data["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return TokenResponse(
        access_token=create_access_token(
            user["id"], user["email"], user["roles"], user.get("customer_id")
        ),
        refresh_token=create_refresh_token(user["id"]),
    )


@router.get("/me", response_model=UserResponse)
def me(current=Depends(get_current_user)):
    # get_current_user already verified the token; look up the full user record
    user = service.get_user(current["id"])
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user