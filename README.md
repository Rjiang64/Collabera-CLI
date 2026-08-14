
# SRTRS Bank — Full-Stack Banking Application

A production-patterned **Bank Management System**: a secure REST API (FastAPI +
PostgreSQL) with JWT authentication, role-based access control, and TOTP
two-factor authentication, plus a React single-page frontend. Deployed on AWS
(EC2 + S3 + CloudFront) with the database on Neon.

---

## Live Demo & Login

**Live site:** https://d30m9rrzofroww.cloudfront.net


### Sample login — Branch Manager
| Email | Password | Role |
|-------|----------|------|
| `mgr@test.com` | `pw123456` | `BRANCH_MANAGER` |

Log in as the manager to see the full picture, including the **Analytics** page
(per-branch account counts and balances) that is restricted to managers/admins.

### Try the Two-Factor Authentication
1. Log in.
2. Open the **Security** tab in the app.
3. Click to enable MFA — a **QR code** appears.
4. **Scan it with Google Authenticator** (or Authy / 1Password) on your phone.
5. Enter the **6-digit code** the app shows to confirm — MFA is now on.
6. Log out and log back in: after your password, you'll be prompted for the
   current 6-digit code before you're allowed in.

> See [Two-Factor Authentication (2FA)](#two-factor-authentication-2fa) below for a
> code-level walkthrough of exactly how this works.

---

## Table of Contents
- [Live Demo & Login](#live-demo--login)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started — Backend](#getting-started--backend)
- [Getting Started — Frontend](#getting-started--frontend)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Roles & Access Control (RBAC)](#roles--access-control-rbac)
- [Two-Factor Authentication (2FA)](#two-factor-authentication-2fa)
- [Testing (Postman)](#testing-postman)
- [Deployment (AWS)](#deployment-aws)
- [Security Notes](#security-notes)

---

## Features

- **RESTful API** for customers, accounts, transactions, and branches.
- **Authentication** — email + password login, passwords hashed with **bcrypt**.
- **JWT tokens** — short-lived access tokens + long-lived refresh tokens (HS256).
- **Role-Based Access Control** — `CUSTOMER`, `TELLER`, `BRANCH_MANAGER`, `ADMIN`,
  enforced per-endpoint plus per-record ownership checks.
- **Two-Factor Authentication (TOTP)** — authenticator-app codes with QR
  enrollment, replay protection, timing-safe verification, and account lockout.
- **Banking operations** — open accounts, transfers, teller deposits/withdrawals,
  transaction history, and a manager-only branch analytics view.
- **React frontend** — login (incl. MFA), dashboard, accounts, analytics, and a
  security/MFA-setup page; UI mirrors the backend's roles.
- **Cloud-deployed** — EC2 backend, S3 + CloudFront frontend, Neon database.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, **FastAPI**, Uvicorn |
| Auth | **PyJWT** (JWT), **bcrypt** (hashing), **pyotp** + **qrcode** (TOTP) |
| Database | **PostgreSQL** (hosted on **Neon**), accessed with **psycopg 3** |
| Frontend | **React** + **Vite**, **Material UI**, React Router, **axios** |
| Testing | Postman collection |
| Deployment | AWS **EC2** (Nginx + systemd), **S3** + **CloudFront** |

---

## Architecture

The backend is a **layered architecture** — each layer has one job, so any one
can change without disturbing the others.

```
HTTP request
  -> controllers/   routes, status codes, RBAC gates
  -> services/      banking rules (create customer, move money, verify MFA)
  -> data/          raw SQL against PostgreSQL (Neon)
                    ^ security/ (passwords, JWT, role deps, TOTP) is used across layers
```

Deployed topology:

```
Browser
   | HTTPS
   v
CloudFront (frontend)  -->  S3 bucket (React build)
   |
   | API calls (HTTPS)
   v
CloudFront (backend)   -->  EC2 (Nginx -> uvicorn/FastAPI)  -->  Neon PostgreSQL
```

---

## Getting Started — Backend


### 1. Set up the environment
```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure secrets
Create a `.env` file in the project root (see [Environment Variables](#environment-variables)):
```
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DB?sslmode=require
JWT_SECRET=<a long random string>
ACCESS_TOKEN_MINUTES=30
REFRESH_TOKEN_DAYS=7
```

### 3. Create the database tables
```bash
python create_users_table.py     # creates the users table
python scripts/migrate_mfa.py     # adds the MFA columns to users
```
The `branches`, `customers`, `accounts`, and `transactions` tables are seeded
from `app/data/sample_data.py` (or your own SQL). Users are created via the
`/api/v1/auth/register` endpoint (or a seed script).

### 4. Run the API
```bash
uvicorn app.main:app --reload
```
- API root: http://127.0.0.1:8000/
- Interactive docs (Swagger UI): http://127.0.0.1:8000/docs

---

## Getting Started — Frontend

### Prerequisites
- Node.js 18+ (developed on Node 26)

### Run it
```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```
`npm run dev` uses `frontend/.env` (points at `http://127.0.0.1:8000`).

### Build for production
```bash
npm run build                     # outputs static files to frontend/dist/
```
The production build uses `frontend/.env.production` (points at the deployed
backend URL). The `dist/` folder is what gets uploaded to S3.

> **Note:** the frontend needs the backend running (or deployed) to log in.
> Make sure the backend origin is included in the API's CORS `allow_origins`.

---

## Environment Variables

### Backend (`.env`)
| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string (Neon), e.g. `postgresql://...?sslmode=require` |
| `JWT_SECRET` | Secret key used to sign/verify JWTs. Keep secret; use a long random value |
| `ACCESS_TOKEN_MINUTES` | Access-token lifetime in minutes (default 30) |
| `REFRESH_TOKEN_DAYS` | Refresh-token lifetime in days (default 7) |
| `MFA_TOKEN_MINUTES` | Lifetime of the `mfa_pending` token (default 5) |

### Frontend (`.env` / `.env.production`)
| Variable | Purpose |
|----------|---------|
| `VITE_API_URL` | Base URL of the backend API (no trailing slash) |

> `.env` files are gitignored and must never be committed.

---

## API Endpoints

Base path: `/api/v1`

### Auth (`/api/v1/auth`)
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/register` | Create a user (defaults to CUSTOMER role) | public |
| POST | `/login` | Log in (OAuth2 **form** data: `username`+`password`) → tokens or `mfa_required` | public |
| POST | `/mfa/verify` | Exchange the `mfa_token` + 6-digit code for real tokens | mfa_token |
| GET | `/mfa/status` | Is MFA enabled / pending for the current user? | access token |
| POST | `/mfa/setup` | Begin MFA enrollment → returns secret + QR | access token |
| POST | `/mfa/activate` | Confirm enrollment with a valid code | access token |
| POST | `/mfa/disable` | Turn MFA off (requires a current code) | access token |
| POST | `/refresh` | Get a new access/refresh pair | refresh token |
| GET | `/me` | Current user's info | access token |

### Customers (`/api/v1/customers`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `` | Create a customer |
| GET | `` | List customers |
| GET | `/{id}` | Get a customer |
| PUT | `/{id}` | Update a customer |
| DELETE | `/{id}` | Deactivate (soft delete) a customer |

### Accounts & Transactions (`/api/v1`)
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| POST | `/accounts` | Open an account | TELLER/MANAGER/ADMIN |
| GET | `/accounts` | List accounts (customers see only their own) | any (filtered) |
| GET | `/accounts/{id}` | Get an account (ownership-checked) | any (own) |
| POST | `/accounts/{id}/deposit` | Teller deposit | TELLER/MANAGER/ADMIN |
| POST | `/accounts/{id}/withdraw` | Teller withdrawal | TELLER/MANAGER/ADMIN |
| POST | `/transactions/transfer` | Transfer (from an owned account) | CUSTOMER (own)/ADMIN |
| GET | `/transactions` | List transactions (customers see only their own) | any (filtered) |

### Branches & Analytics
| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/api/v1/branches` | List branches | any authenticated |
| GET | `/api/v1/branches/{id}` | Get a branch | any authenticated |
| GET | `/api/v1/analytics/branch-summary` | Per-branch account counts + balances | BRANCH_MANAGER/ADMIN |

**Status codes:** `200` OK · `201` Created · `400` bad request · `401`
unauthenticated · `403` wrong role · `404` not found · `409` conflict · `422`
validation.

---

## Roles & Access Control (RBAC)

Four roles, checked from the roles claim inside the JWT:

| Role | Can do |
|------|--------|
| `CUSTOMER` | View **only their own** accounts/transactions; transfer from their own account |
| `TELLER` | Open accounts; deposit/withdraw on behalf of customers |
| `BRANCH_MANAGER` | View branch analytics/metrics; oversight of accounts/transactions |
| `ADMIN` | Full access |

Enforced two ways in `app/security/dependencies.py`:
- **`require_roles(...)`** — a dependency gate on an endpoint (wrong role → 403).
- **Ownership checks** — e.g. a customer can only see/transfer from accounts whose
  `customer_id` matches the `customer_id` in their token.

`users.customer_id` links a customer login to its `customers` record. Staff
logins (teller/manager/admin) have `customer_id = NULL`.

---

## Two-Factor Authentication (2FA)

This is the standout security feature. It uses **TOTP** (Time-based One-Time
Password) — the same 6-digit codes as Google Authenticator, Authy, or 1Password.
After the password, the user must enter a code that only their phone can produce.

**In the app:** log in → open the **Security** tab → enable MFA → scan the QR
code with Google Authenticator → confirm with a code. From then on, every login
asks for a fresh 6-digit code.

### How TOTP works (no network, no SMS)
When the user enrolls, the server generates a random secret and shows it as a QR
code. The phone stores that secret. From then on, **both sides independently
compute the same 6-digit number** from two shared inputs: the secret, and the
current time rounded to a 30-second "step." Nothing is transmitted between phone
and server — the codes match because the inputs match.

### 1. Enrollment — generate a secret + QR (`app/security/totp.py`)
```python
def generate_secret() -> str:
    # cryptographically secure random base32 secret
    return pyotp.random_base32()

def provisioning_uri(secret: str, email: str) -> str:
    # the otpauth:// URI encoded into the QR the phone scans
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=ISSUER)
```
The service stores the secret but keeps MFA **off** until confirmed
(`app/services/auth_service.py` → `start_mfa_enrollment`):
```python
secret = totp.generate_secret()
execute(
    """UPDATE users
       SET mfa_secret = %s, mfa_enabled = FALSE, ...
       WHERE id = %s""",
    (secret, user_id),
)
# returns { secret, otpauth_uri, qr_data_uri }  -> the frontend renders the QR
```

### 2. Confirm enrollment — prove the phone works before turning it on
```python
def activate_mfa(self, user_id, code):
    ...
    ok, error = self._check_code(user, code)     # must enter a valid code first
    if not ok:
        return (False, error)
    execute("UPDATE users SET mfa_enabled = TRUE WHERE id = %s", (user_id,))
```
Why: if MFA flipped on the instant a secret was generated, a user who mis-scanned
the QR would be **locked out of their own account**. The confirm step prevents that.

### 3. Login becomes two steps (`app/controllers/auth_controller.py`)
After a correct password, if MFA is on, the server does **not** issue an access
token — it issues a short-lived `mfa_pending` token instead:
```python
if user.get("mfa_enabled"):
    return LoginResponse(
        mfa_required=True,
        mfa_token=create_mfa_token(user["id"]),   # NOT an access token
    )
```
That token's type is deliberately **not** `"access"`, so it can't open any
protected route — its only use is `/mfa/verify` (`app/security/jwt_handler.py`):
```python
payload = {
    "sub": str(user_id),
    "type": "mfa_pending",   # deliberately not "access"
    ...
}
```
The user then exchanges it + their 6-digit code for real tokens:
```python
@router.post("/mfa/verify")
def mfa_verify(payload: MfaVerifyRequest):
    data = decode_token(payload.mfa_token)
    if data.get("type") != "mfa_pending":            # reject access/refresh tokens here
        raise HTTPException(status_code=401, detail="Invalid login session.")
    user, error = service.verify_mfa_code(int(data["sub"]), payload.code)
    ...
    return TokenResponse(access_token=..., refresh_token=...)
```
This is what stops the password alone from being enough to get in.

### 4. Verifying a code — replay-proof and timing-safe (`app/security/totp.py`)
```python
for offset in range(-window, window + 1):        # accept prev/current/next 30s step
    step = now + offset
    expected = totp.at(step * STEP_SECONDS)
    # constant-time compare so timing can't leak how many digits were right
    if hmac.compare_digest(expected, code):
        # replay guard: a code from an already-used (or older) step is rejected
        if last_step is not None and step <= last_step:
            return (False, None, "reused")
        return (True, step, None)
return (False, None, "invalid")
```

### 5. Brute-force lockout (`app/services/auth_service.py` → `_check_code`)
```python
if attempts >= MAX_MFA_ATTEMPTS:                  # 5 wrong codes
    execute(
        """UPDATE users
           SET mfa_failed_attempts = 0, mfa_locked_until = %s
           WHERE id = %s""",
        (now + timedelta(minutes=MFA_LOCKOUT_MINUTES), user_id),
    )
```
Six digits is only 1,000,000 combinations, so without a limit an attacker could
grind through them. After too many failures the account is temporarily frozen.

### Why this is secure
- **The secret never travels** over the login request — only a derived 6-digit
  code does, and it's useless ~90 seconds later.
- A stolen **password alone cannot log in** — the attacker still needs the
  physical device holding the secret.
- **Replay** is blocked (used time-step is remembered), **timing attacks** are
  blocked (`hmac.compare_digest`), and **brute force** is blocked (lockout).
- The MFA **secret is never returned** by any user-facing endpoint.
- Even **disabling** MFA requires a current code — a stolen session can't strip
  the second factor off the account.

---

## Testing (Postman)

A collection is included at `postman/Bank Api Request.postman_collection.json`.

- The **login** request captures `access_token` into a collection variable, and
  requests inherit it as a Bearer token.
- Test the security matrix: `200` when allowed, `403` for a wrong role, `401`
  for a missing/invalid token.
- **Login is form data** — use `x-www-form-urlencoded` with `username` +
  `password` (not JSON), matching the OAuth2 form flow.

---

## Deployment (AWS)

Deployed with production patterns:

- **Backend:** EC2 (Amazon Linux) running FastAPI via `uvicorn` + `systemd`,
  behind `Nginx` (reverse proxy on port 80). Fronted by a **CloudFront**
  distribution to provide HTTPS.
  - `ec2-user-data.sh` bootstraps the instance on first boot (Python venv, Nginx,
    systemd unit) — no AWS API calls / no IAM required.
  - `deploy.sh <ec2-ip>` pushes the code + `.env` over SSH and restarts the
    service. Also the redeploy command.
- **Frontend:** `npm run build` → `dist/` uploaded to an **S3** bucket, served
  globally via **CloudFront** (private bucket + Origin Access Control).
- **Database:** **Neon** PostgreSQL (managed, serverless) — unchanged between
  local and cloud; only `DATABASE_URL` differs.
- **CORS:** the backend's `allow_origins` includes the frontend CloudFront URL.

> Secrets are delivered to the instance over SSH into `/opt/bankapp/backend.env`
> (chmod 600). In an account with IAM, AWS Systems Manager Parameter Store would
> be the alternative.

---

## Security Notes

- Passwords are **bcrypt-hashed**; raw passwords are never stored or logged.
- JWTs are **signed** (HS256) with a secret from `.env`; a tampered token fails
  verification. The `JWT_SECRET` must be kept private.
- Access tokens are **short-lived** (30 min); refresh tokens renew them.
- Token **type** is enforced: an `mfa_pending` token can only be used at
  `/mfa/verify`; a refresh token can only be used at `/refresh`; protected routes
  require an `access` token.
- RBAC is enforced **server-side**; the frontend mirrors it for UX but is not the
  source of truth.
- `_PUBLIC_COLUMNS` in the auth service ensures the password hash and MFA secret
  are never returned by user-facing endpoints.
- `.env` and `venv/` are gitignored — never commit secrets or virtual envs.
