"""Authentication routes: register, login, refresh, me."""
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.models.auth import RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from app.security.dependencies import get_current_user
from app.security.jwt_handler import (
    create_access_token, create_refresh_token, decode_token,
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



@router.post("/login", response_model=TokenResponse)
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
    # on success, hand back both tokens
    return TokenResponse(
        access_token=create_access_token(
            user["id"], user["email"], user["roles"], user.get("customer_id")
        ),
        refresh_token=create_refresh_token(user["id"]),
    )


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