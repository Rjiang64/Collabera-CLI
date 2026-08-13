"""
TOTP (Time-based One-Time Password) -- the second factor.

HOW IT WORKS, in one paragraph:
When a user enrolls we generate a random secret and show it to them as a QR
code. Their authenticator app (Google Authenticator, Authy, 1Password...) stores
that secret. From then on, BOTH sides independently compute the same 6-digit
number from two inputs: the shared secret, and the current time rounded down to
a 30-second "step". Nothing is transmitted between us and the phone -- the codes
match because the inputs match. That's why this works with no SMS, no network on
the phone, and no third-party service that could fail during a demo.

WHY THIS IS A REAL SECOND FACTOR:
The secret never travels over the login request; only a derived 6-digit code
does, and that code is useless 30-90 seconds later. An attacker who steals the
password still cannot log in without the physical device holding the secret.
"""

import base64
import hmac
import io
import time

import pyotp
import qrcode
import qrcode.image.svg

# A TOTP "step" is the window a single code is valid for. 30s is the value every
# authenticator app assumes by default -- changing it would break compatibility.
STEP_SECONDS = 30

# How many steps either side of "now" we still accept. 1 means a code is good
# for the previous, current, and next window (~90s total). This absorbs clock
# drift between the server and the phone -- without it, a phone whose clock is a
# few seconds off would never be able to log in.
DEFAULT_WINDOW = 1

# The name shown above the code inside the authenticator app.
ISSUER = "SRTRS Bank"


def generate_secret() -> str:
    """Create a new random base32 secret for a user enrolling in MFA."""
    # pyotp.random_base32() uses the secrets module underneath, i.e. a
    # cryptographically secure RNG -- not random.random().
    return pyotp.random_base32()


def provisioning_uri(secret: str, email: str) -> str:
    """
    Build the otpauth:// URI that the QR code encodes.

    Format: otpauth://totp/SRTRS%20Bank:user@example.com?secret=...&issuer=...
    Every authenticator app understands this scheme, which is why scanning the
    QR is all the setup the phone needs.
    """
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=ISSUER)


def qr_data_uri(uri: str) -> str:
    """
    Render the provisioning URI as an SVG QR code, returned as a data: URI the
    frontend can drop straight into an <img src="...">.

    We render SVG (not PNG) deliberately: the SVG factory is pure Python, so we
    avoid pulling in Pillow just to draw black squares.
    """
    img = qrcode.make(uri, image_factory=qrcode.image.svg.SvgPathImage)
    buf = io.BytesIO()
    img.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def current_step(at: float | None = None) -> int:
    """Which 30-second window we're in right now."""
    return int((at if at is not None else time.time()) // STEP_SECONDS)


def verify(secret: str, code: str, last_step: int | None = None,
           window: int = DEFAULT_WINDOW) -> tuple[bool, int | None, str | None]:
    """
    Check a 6-digit code.

    Returns (ok, matched_step, reason).
      ok           True only if the code is valid AND has not been used before.
      matched_step the time-step the code belonged to -- the caller stores this
                   so the same code cannot be replayed.
      reason       "invalid" or "reused" when ok is False.

    WHY WE DON'T USE pyotp's built-in valid_window:
    pyotp.verify(code, valid_window=1) answers "is this code acceptable?" but not
    "WHICH window did it match?". We need that answer, because storing the
    matched step is what lets us reject a replay of the same code a few seconds
    later. So we walk the candidate steps ourselves.
    """
    if not secret or not code:
        return (False, None, "invalid")

    # Strip spaces -- authenticator apps display codes as "418 302" and people
    # type them the way they see them.
    code = code.strip().replace(" ", "")
    if not code.isdigit() or len(code) != 6:
        return (False, None, "invalid")

    totp = pyotp.TOTP(secret)
    now = current_step()

    for offset in range(-window, window + 1):
        step = now + offset
        expected = totp.at(step * STEP_SECONDS)

        # compare_digest, not ==, so the comparison takes the same amount of
        # time whether the first digit is wrong or only the last one is. A plain
        # == leaks, through timing, how much of the code was correct.
        if hmac.compare_digest(expected, code):
            # Valid code -- but has this exact window already been spent?
            if last_step is not None and step <= last_step:
                return (False, None, "reused")
            return (True, step, None)

    return (False, None, "invalid")
