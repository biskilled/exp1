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

_PG_COLS = "id, email, password_hash, is_admin, is_active, created_at, last_login"


def _pg_row(row: tuple) -> dict:
    keys = ["id", "email", "password_hash", "is_admin", "is_active", "created_at", "last_login"]
    d = dict(zip(keys, row))
    for k in ("created_at", "last_login"):
        if d.get(k) and hasattr(d[k], "isoformat"):
            d[k] = d[k].isoformat()
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
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (id, email, password_hash, is_admin) VALUES (%s, %s, %s, %s)",
                (uid, email, hash_password(password), is_admin),
            )
    return {"id": uid, "email": email, "is_admin": is_admin, "is_active": True, "created_at": _now()}


def _pg_list_users() -> list[dict]:
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT {_PG_COLS} FROM users ORDER BY created_at")
            rows = cur.fetchall()
    return [_safe(_pg_row(r)) for r in rows]


def _pg_update_user(user_id: str, **fields) -> Optional[dict]:
    allowed = {"is_admin", "is_active", "last_login"}
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
            return u
    return None


def find_by_id(user_id: str) -> Optional[dict]:
    if db.is_available():
        return _safe(_pg_find_by_id(user_id) or {}) or None
    for u in _load_all():
        if u.get("id") == user_id:
            return _safe(u)
    return None


def create_user(email: str, password: str) -> dict:
    """Create and persist a new user. Raises ValueError on duplicate email."""
    email = email.lower().strip()
    if find_by_email(email):
        raise ValueError(f"Email already registered: {email}")
    if db.is_available():
        return _pg_create_user(email, password)
    users = _load_all()
    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "password_hash": hash_password(password),
        "created_at": _now(),
        "is_admin": len(users) == 0,
        "is_active": True,
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
    return _safe(raw)


def list_users() -> list[dict]:
    if db.is_available():
        return _pg_list_users()
    return [_safe(u) for u in _load_all()]


def update_user(user_id: str, **fields) -> Optional[dict]:
    """Update allowed fields: is_admin, is_active, last_login."""
    if db.is_available():
        return _pg_update_user(user_id, **fields)
    users = _load_all()
    for u in users:
        if u.get("id") == user_id:
            for k, v in fields.items():
                if k in ("is_admin", "is_active", "last_login"):
                    u[k] = v
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
