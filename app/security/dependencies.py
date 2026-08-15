
"""
FastAPI security dependencies that protects routes.

  * get_current_user  -> reads the Bearer token, verifies it, returns the user.
                         Add it to a route to REQUIRE a valid login.
  * require_roles(...) -> returns a dependency that ALSO checks the user's roles.
                         Add it to a route to require specific roles (RBAC).

Usage:
    @router.get("/admin", dependencies=[Depends(require_roles("ADMIN"))])
    def admin_only(): ...

    @router.get("/me")
    def me(user = Depends(get_current_user)): ...
"""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.security.jwt_handler import decode_token

# Tells FastAPI to look for the token in the "Authorization: Bearer <token>"
# header. tokenUrl points at the login route so Swagger's Authorize button works.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Verify the access token and return {id, email, roles, customer_id}."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)          # verifies signature + expiry
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_error                # bad signature / malformed token

    # A refresh token must NOT be usable to access protected routes.
    if payload.get("type") != "access":
        raise credentials_error

    # Hand the route a clean dict of who the caller is.
    return {
        "id": int(payload["sub"]),
        "email": payload.get("email"),
        "roles": payload.get("roles", []),
        "customer_id": payload.get("customer_id"),
    }


def require_roles(*allowed_roles: str):
    """Build a dependency that requires the user to hold at least one of these roles."""
    def role_checker(user: dict = Depends(get_current_user)) -> dict:
        # set intersection: does the user have any of the allowed roles?
        if not set(user["roles"]) & set(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(allowed_roles)}",
            )
        return user
    return role_checker