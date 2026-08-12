"""Auth business logic: register, authenticate, fetch user.

Uses the same query helpers as every other service. Passwords are hashed before
they ever touch the database; we never store or return the plain password.
"""
from app.data.database import execute, query_one
from app.security.passwords import hash_password, verify_password

#The columns that are safe to return (deliberately excludes password_hash).
_PUBLIC_COLUMNS = "id, email, full_name, roles, customer_id, is_active, created_at"


class AuthService:
    def register(self, email, password, full_name=None, roles=None, customer_id=None):
        # 1. reject if the email is already taken
        if query_one("SELECT id FROM users WHERE email = %s", (email,)) is not None:
            return None
        # 2. default new users to the CUSTOMER role
        roles = roles or ["CUSTOMER"]
        # 3. hash the password, then insert the new user and return the safe columns
        return execute(
            f"""
            INSERT INTO users (email, password_hash, full_name, roles, customer_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING {_PUBLIC_COLUMNS};
            """,
            (email, hash_password(password), full_name, roles, customer_id),
        )

    def authenticate(self, email, password):
        """Return the user row only if email exists, is active, AND password matches."""
        user = query_one("SELECT * FROM users WHERE email = %s", (email,))
        if user is None or not user["is_active"]:
            return None
        # compare the typed password against the stored bcrypt hash
        if not verify_password(password, user["password_hash"]):
            return None
        return user

    def get_user(self, user_id):
        return query_one(
            f"SELECT {_PUBLIC_COLUMNS} FROM users WHERE id = %s", (user_id,)
        )