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
service = AuthService()


@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest):
    # create the user; service returns None if the email is already taken
    user = service.register(
        payload.email, payload.password, payload.full_name,
        payload.roles, payload.customer_id,
    )
    if user is None:
        raise HTTPException(status_code=409, detail="Email already registered")
    return user


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends()):
    # OAuth2 form sends 'username' + 'password'; we treat 'username' as the email.
    user = service.authenticate(form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
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
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    if data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")
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