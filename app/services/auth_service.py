"""Auth business logic: register, authenticate, fetch user.

Uses the same query helpers as every other service. Passwords are hashed before
they ever touch the database; we never store or return the plain password.
"""
from datetime import datetime, timedelta, timezone

from app.data.database import execute, query_one
from app.security import totp
from app.security.passwords import hash_password, verify_password

#The columns that are safe to return (deliberately excludes password_hash).
# Using this everywhere means we can never accidentally leak a password hash
# in an API response.
# NOTE: mfa_enabled is safe to expose (the UI needs it to show whether MFA is
# on), but mfa_secret is NOT and is deliberately absent -- anyone holding that
# secret can generate valid codes, so it must never leave the server.
_PUBLIC_COLUMNS = (
    "id, email, full_name, roles, customer_id, is_active, created_at, mfa_enabled"
)

# Brute-force protection for the 6-digit code. Six digits is only 1,000,000
# combinations, which is trivial to grind through without a limit.
MAX_MFA_ATTEMPTS = 5
MFA_LOCKOUT_MINUTES = 15


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
             # note: hash_password() runs here, so the raw password never gets
            # written to the database or logged anywhere
        )

    def authenticate(self, email, password):
        """Return the user row only if email exists, is active, AND password matches."""
        # this SELECT * (unlike _PUBLIC_COLUMNS above) is intentional --
        # we need password_hash internally to check the password below,
        # it just never leaves this function

        user = query_one("SELECT * FROM users WHERE email = %s", (email,))
        if user is None or not user["is_active"]:
            return None  # no such email, or the account was deactivated
        # compare the typed password against the stored bcrypt hash
        if not verify_password(password, user["password_hash"]):
            return None  # wrong password
        return user   # success -- login route uses this to build the tokens

    def get_user(self, user_id):
        # used by /me and /refresh to re-fetch a user's current info by id
        return query_one(
            f"SELECT {_PUBLIC_COLUMNS} FROM users WHERE id = %s", (user_id,)
        )

    # ------------------------------------------------------------------
    # Multi-factor authentication (TOTP)
    # ------------------------------------------------------------------

    def _get_user_mfa(self, user_id):
        """Internal read that INCLUDES mfa_secret. Never hand this to a route."""
        return query_one(
            """SELECT id, email, roles, customer_id, is_active, mfa_secret,
                      mfa_enabled, mfa_last_step, mfa_failed_attempts, mfa_locked_until
               FROM users WHERE id = %s""",
            (user_id,),
        )

    def _check_code(self, user, code):
        """
        The single place a TOTP code is judged. Returns (ok, error_message).

        Every caller goes through here -- login, activate, AND disable -- so the
        brute-force protections cannot be bypassed by attacking whichever
        endpoint happened to be softer. That matters most for disable: without a
        limit there, anyone holding a stolen session could grind the 1,000,000
        combinations and strip the second factor off the account.

        On success the matched time-step is recorded (replay defence) and the
        failure counter is cleared.
        """
        user_id = user["id"]

        # 1. Frozen from earlier failures?
        locked_until = user["mfa_locked_until"]
        if locked_until is not None:
            now = datetime.now(timezone.utc)
            # Column is timestamptz, but be defensive: if it ever comes back
            # naive, treat it as UTC rather than crashing on the comparison.
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(tzinfo=timezone.utc)
            if locked_until > now:
                mins = max(1, int((locked_until - now).total_seconds() // 60) + 1)
                return (False, f"Too many incorrect codes. Try again in {mins} minute(s).")

        # 2. Digits, clock window, and replay guard.
        ok, step, reason = totp.verify(user["mfa_secret"], code, user["mfa_last_step"])

        if not ok:
            attempts = (user["mfa_failed_attempts"] or 0) + 1
            if attempts >= MAX_MFA_ATTEMPTS:
                execute(
                    """UPDATE users
                       SET mfa_failed_attempts = 0, mfa_locked_until = %s
                       WHERE id = %s""",
                    (datetime.now(timezone.utc) + timedelta(minutes=MFA_LOCKOUT_MINUTES), user_id),
                )
                return (False, f"Too many incorrect codes. Locked for {MFA_LOCKOUT_MINUTES} minutes.")

            execute(
                "UPDATE users SET mfa_failed_attempts = %s WHERE id = %s",
                (attempts, user_id),
            )
            if reason == "reused":
                return (False, "That code was already used. Wait for the next one.")
            remaining = MAX_MFA_ATTEMPTS - attempts
            return (False, f"Incorrect code. {remaining} attempt(s) remaining.")

        # 3. Success: burn this time-step so the same code can't be replayed.
        execute(
            """UPDATE users
               SET mfa_last_step = %s, mfa_failed_attempts = 0, mfa_locked_until = NULL
               WHERE id = %s""",
            (step, user_id),
        )
        return (True, None)

    def start_mfa_enrollment(self, user_id):
        """
        Generate a fresh secret and return what the phone needs to scan it.

        The secret is stored immediately but mfa_enabled stays FALSE -- the user
        is not protected (and not locked out) until they prove, in
        activate_mfa(), that their phone actually holds the same secret.
        Re-running this replaces an unconfirmed secret, which is what you want
        if someone starts enrollment, loses the QR, and begins again.
        """
        user = self._get_user_mfa(user_id)
        if user is None:
            return None

        secret = totp.generate_secret()
        execute(
            """UPDATE users
               SET mfa_secret = %s, mfa_enabled = FALSE, mfa_last_step = NULL,
                   mfa_failed_attempts = 0, mfa_locked_until = NULL
               WHERE id = %s""",
            (secret, user_id),
        )

        uri = totp.provisioning_uri(secret, user["email"])
        return {
            "secret": secret,          # shown once, for manual entry
            "otpauth_uri": uri,
            "qr_data_uri": totp.qr_data_uri(uri),
        }

    def activate_mfa(self, user_id, code):
        """
        Turn MFA on, but only after the user echoes back a correct code.

        WHY the confirmation step matters: if we flipped mfa_enabled the moment
        we generated a secret, a user who mis-scanned the QR would be locked out
        of their own account on the next login with no way back in.
        """
        user = self._get_user_mfa(user_id)
        if user is None or not user["mfa_secret"]:
            return (False, "No enrollment in progress. Start setup first.")

        ok, error = self._check_code(user, code)
        if not ok:
            return (False, error)

        execute("UPDATE users SET mfa_enabled = TRUE WHERE id = %s", (user_id,))
        return (True, None)

    def disable_mfa(self, user_id, code):
        """
        Turn MFA off -- but require a current code to do it.

        WHY: if a plain authenticated request could disable MFA, then anyone who
        stole a session could strip the second factor off the account. Demanding
        a live code means the attacker still needs the physical device.
        """
        user = self._get_user_mfa(user_id)
        if user is None or not user["mfa_enabled"]:
            return (False, "MFA is not currently enabled.")

        # Goes through the SAME hardened check as login, so disable is rate
        # limited too -- see _check_code for why that matters.
        ok, error = self._check_code(user, code)
        if not ok:
            return (False, error)

        execute(
            """UPDATE users
               SET mfa_enabled = FALSE, mfa_secret = NULL, mfa_last_step = NULL,
                   mfa_failed_attempts = 0, mfa_locked_until = NULL
               WHERE id = %s""",
            (user_id,),
        )
        return (True, None)

    def verify_mfa_code(self, user_id, code):
        """
        The login-time check. Returns (user_row_or_None, error_message).

        Enforces three things beyond "do the digits match":
          1. lockout    -- too many wrong codes freezes the account for a while
          2. replay     -- a code already spent cannot be used a second time
          3. attempt    -- every failure is counted and persisted
        """
        user = self._get_user_mfa(user_id)
        if user is None or not user["is_active"]:
            return (None, "Account is not available.")
        if not user["mfa_enabled"] or not user["mfa_secret"]:
            return (None, "MFA is not enabled for this account.")

        ok, error = self._check_code(user, code)
        if not ok:
            return (None, error)

        return (self.get_user(user_id), None)