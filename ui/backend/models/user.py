"""
User store — dual-mode: PostgreSQL when DATABASE_URL is set, JSON file fallback.

Public API (identical in both modes):
    create_user(email, password)  → dict
    authenticate(email, password) → dict | None
    find_by_id(user_id)           → dict | None
    find_by_email(email)          → dict | None
    list_users()                  → list[dict]
    update_user(user_id, **fields)→ dict | None
    delete_user(user_id)          → bool
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import settings
from core.auth import hash_password, verify_password
from core.database import db


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe(user: dict) -> dict:
    """Strip password_hash from returned dicts."""
    return {k: v for k, v in user.items() if k != "password_hash"}


# ── JSON file fallback ────────────────────────────────────────────────────────

def _users_path() -> Path:
    p = Path(settings.data_dir) / "users.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _load_all() -> list[dict]:
    path = _users_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_all(users: list[dict]) -> None:
    _users_path().write_text(json.dumps(users, indent=2), encoding="utf-8")


# ── PostgreSQL implementations ────────────────────────────────────────────────

_PG_COLS = ("id, email, password_hash, is_admin, is_active, created_at, last_login, "
            "role, balance_added_usd, balance_used_usd, coupons_used, stripe_customer_id")


# Fields added for monetization — not in PostgreSQL schema yet (file store only for now)
_BALANCE_DEFAULTS = {
    "role": "free",
    "balance_added_usd": 0.0,
    "balance_used_usd": 0.0,
    "coupons_used": [],
    "stripe_customer_id": "",
}


def _migrate_user(user: dict) -> dict:
    """Add missing monetization fields to legacy user records."""
    # Derive role from is_admin BEFORE applying defaults (defaults include role="free")
    if "role" not in user:
        user["role"] = "admin" if user.get("is_admin") else "free"
    for k, v in _BALANCE_DEFAULTS.items():
        if k not in user:
            user[k] = v
    # Keep is_admin in sync with role
    user["is_admin"] = user.get("role") == "admin"
    return user


def _pg_row(row: tuple) -> dict:
    keys = [
        "id", "email", "password_hash", "is_admin", "is_active", "created_at", "last_login",
        "role", "balance_added_usd", "balance_used_usd", "coupons_used", "stripe_customer_id",
    ]
    d = dict(zip(keys, row))
    for k in ("created_at", "last_login"):
        if d.get(k) and hasattr(d[k], "isoformat"):
            d[k] = d[k].isoformat()
    # Ensure numeric balance fields are Python floats (not Decimal)
    for k in ("balance_added_usd", "balance_used_usd"):
        if d.get(k) is not None:
            d[k] = float(d[k])
    # Ensure coupons_used is a list
    if d.get("coupons_used") is None:
        d["coupons_used"] = []
    return d


def _pg_find_by_email(email: str) -> Optional[dict]:
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT {_PG_COLS} FROM users WHERE email = %s", (email.lower().strip(),))
            row = cur.fetchone()
    return _pg_row(row) if row else None


def _pg_find_by_id(user_id: str) -> Optional[dict]:
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT {_PG_COLS} FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
    return _pg_row(row) if row else None


def _pg_create_user(email: str, password: str) -> dict:
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            is_admin = cur.fetchone()[0] == 0
    uid = str(uuid.uuid4())
    role = "admin" if is_admin else "free"
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (id, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)",
                (uid, email, hash_password(password), is_admin),
            )
    return _migrate_user({"id": uid, "email": email, "is_admin": is_admin, "role": role, "is_active": True, "created_at": _now()})


def _pg_list_users() -> list[dict]:
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT {_PG_COLS} FROM users ORDER BY created_at")
            rows = cur.fetchall()
    return [_safe(_migrate_user(_pg_row(r))) for r in rows]


def _pg_update_user(user_id: str, **fields) -> Optional[dict]:
    allowed = {"is_admin", "is_active", "last_login", "role", "balance_added_usd", "balance_used_usd", "coupons_used"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return _safe(_pg_find_by_id(user_id) or {}) or None
    set_clause = ", ".join(f"{k} = %s" for k in updates)
    values = list(updates.values()) + [user_id]
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE users SET {set_clause} WHERE id = %s", values)
    row = _pg_find_by_id(user_id)
    return _safe(row) if row else None


def _pg_delete_user(user_id: str) -> bool:
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET is_active = FALSE WHERE id = %s", (user_id,))
            return cur.rowcount > 0


# ── Public API ────────────────────────────────────────────────────────────────

def find_by_email(email: str) -> Optional[dict]:
    if db.is_available():
        return _pg_find_by_email(email)
    email = email.lower().strip()
    for u in _load_all():
        if u.get("email") == email:
            return _migrate_user(u)
    return None


def find_by_id(user_id: str) -> Optional[dict]:
    if db.is_available():
        return _safe(_migrate_user(_pg_find_by_id(user_id) or {})) or None
    for u in _load_all():
        if u.get("id") == user_id:
            return _safe(_migrate_user(u))
    return None


def create_user(email: str, password: str) -> dict:
    """Create and persist a new user. Raises ValueError on duplicate email."""
    email = email.lower().strip()
    if find_by_email(email):
        raise ValueError(f"Email already registered: {email}")
    if db.is_available():
        return _pg_create_user(email, password)
    users = _load_all()
    is_admin = len(users) == 0
    role = "admin" if is_admin else "free"
    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "password_hash": hash_password(password),
        "created_at": _now(),
        "role": role,
        "is_admin": is_admin,
        "is_active": True,
        "balance_added_usd": 0.0,
        "balance_used_usd": 0.0,
        "coupons_used": [],
        "stripe_customer_id": "",
    }
    users.append(user)
    _save_all(users)
    return _safe(user)


def authenticate(email: str, password: str) -> Optional[dict]:
    """Return user dict (no password_hash) if credentials match, else None."""
    # Fetch raw (with hash) for verification
    if db.is_available():
        raw = _pg_find_by_email(email)
    else:
        email_lower = email.lower().strip()
        raw = next((u for u in _load_all() if u.get("email") == email_lower), None)

    if not raw:
        return None
    if not verify_password(password, raw.get("password_hash", "")):
        return None

    # Update last_login
    update_user(raw["id"], last_login=_now())
    return _safe(_migrate_user(raw))


def list_users() -> list[dict]:
    if db.is_available():
        return _pg_list_users()
    return [_safe(_migrate_user(u)) for u in _load_all()]


_UPDATABLE_FIELDS = {
    "is_admin", "is_active", "last_login",
    "role", "balance_added_usd", "balance_used_usd", "coupons_used", "stripe_customer_id",
}


def update_user(user_id: str, **fields) -> Optional[dict]:
    """Update allowed fields."""
    if db.is_available():
        return _pg_update_user(user_id, **fields)
    users = _load_all()
    for u in users:
        if u.get("id") == user_id:
            _migrate_user(u)
            for k, v in fields.items():
                if k in _UPDATABLE_FIELDS:
                    u[k] = v
            # Keep is_admin in sync with role
            if "role" in fields:
                u["is_admin"] = fields["role"] == "admin"
            _save_all(users)
            return _safe(u)
    return None


def delete_user(user_id: str) -> bool:
    """Soft-delete: sets is_active=False."""
    if db.is_available():
        return _pg_delete_user(user_id)
    users = _load_all()
    for u in users:
        if u.get("id") == user_id:
            u["is_active"] = False
            _save_all(users)
            return True
    return False
