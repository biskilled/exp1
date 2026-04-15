"""
JWT authentication helpers.

Usage:
    # Protect a route (raises 401 if invalid / missing):
    @router.get("/me")
    async def me(user: dict = Depends(get_current_user)):
        ...

    # Optional auth (returns None when REQUIRE_AUTH=False or no token):
    @router.post("/chat")
    async def chat(req: ChatRequest, user: dict | None = Depends(get_optional_user)):
        ...
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from core.config import settings

_bearer = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"

# Fixed UUID for the seeded admin user (m048 migration).
# Used as a stable FK target in all mirror tables when no real user is authenticated.
ADMIN_USER_ID = "00000000-0000-0000-0000-000000000001"


def _resolve_user_id(uid: str | None) -> str:
    """Return ADMIN_USER_ID when uid is None, 'dev-admin', or empty."""
    if not uid or uid == "dev-admin":
        return ADMIN_USER_ID
    return uid


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate JWT. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI dependencies ──────────────────────────────────────────────────────

_DEV_ADMIN = {
    "sub": ADMIN_USER_ID,
    "id": ADMIN_USER_ID,
    "email": "admin@local",
    "role": "admin",
    "is_admin": True,
    "is_active": True,
    "balance_added_usd": 999.0,
    "balance_used_usd": 0.0,
    "coupons_used": [],
}


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    """Always requires a valid JWT. Use on protected routes. Dev mode bypasses auth."""
    if settings.dev_mode:
        return _DEV_ADMIN
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[dict]:
    """Returns user dict or None (used when REQUIRE_AUTH may be False)."""
    if settings.dev_mode or not settings.require_auth:
        return _DEV_ADMIN
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)
