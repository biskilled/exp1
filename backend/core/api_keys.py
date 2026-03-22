"""
API key store — server keys in mng_clients.server_api_keys (encrypted),
per-user keys in mng_user_api_keys (encrypted).

Priority for get_key(provider, user_id):
  1. User's own key (mng_user_api_keys) — if user_id provided
  2. Server key (mng_clients.server_api_keys)
  3. Env var (settings.*_api_key)

All values are Fernet-encrypted at rest. Never stored in plain text or files.
"""

import json
import logging
from typing import Optional

log = logging.getLogger(__name__)

_PROVIDERS = ("claude", "openai", "deepseek", "gemini", "grok")

_ENV_ATTRS = {
    "claude":   "anthropic_api_key",
    "openai":   "openai_api_key",
    "deepseek": "deepseek_api_key",
    "gemini":   "gemini_api_key",
    "grok":     "grok_api_key",
}

# ── SQL ───────────────────────────────────────────────────────────────────────

_SQL_GET_SERVER_KEYS = "SELECT server_api_keys FROM mng_clients WHERE id=1"

_SQL_UPDATE_SERVER_KEYS = "UPDATE mng_clients SET server_api_keys=%s WHERE id=1"

_SQL_GET_USER_KEY = (
    "SELECT key_enc FROM mng_user_api_keys WHERE user_id=%s AND provider=%s"
)

_SQL_UPSERT_USER_KEY = """INSERT INTO mng_user_api_keys (user_id, provider, key_enc, updated_at)
                   VALUES (%s, %s, %s, NOW())
                   ON CONFLICT (user_id, provider)
                   DO UPDATE SET key_enc=EXCLUDED.key_enc, updated_at=NOW()"""

_SQL_DELETE_USER_KEY = (
    "DELETE FROM mng_user_api_keys WHERE user_id=%s AND provider=%s"
)

_SQL_LIST_USER_KEYS = (
    "SELECT provider, key_enc, updated_at FROM mng_user_api_keys WHERE user_id=%s"
)


# ── Internal helpers ───────────────────────────────────────────────────────────

def _env_key(provider: str) -> str:
    from core.config import settings
    attr = _ENV_ATTRS.get(provider, "")
    return getattr(settings, attr, "").strip() if attr else ""


def _load_server_keys() -> dict[str, str]:
    """Return {provider: encrypted_key} from mng_clients. Empty dict if unavailable."""
    from core.database import db
    if not db.is_available():
        return {}
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_SERVER_KEYS)
                row = cur.fetchone()
                if row and row[0]:
                    return dict(row[0])
    except Exception as e:
        log.debug(f"_load_server_keys DB error: {e}")
    return {}


# ── Public API ─────────────────────────────────────────────────────────────────

def get_key(provider: str, user_id: Optional[str] = None, fallback: str = "") -> str:
    """
    Return a plain-text API key for a provider.
    Priority: user DB key → server DB key → env var → fallback.
    """
    from core.encryption import decrypt

    # 1. Per-user key
    if user_id:
        from core.database import db
        if db.is_available():
            try:
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(_SQL_GET_USER_KEY, (user_id, provider))
                        row = cur.fetchone()
                        if row and row[0]:
                            return decrypt(row[0])
            except Exception as e:
                log.debug(f"get_key user lookup error: {e}")

    # 2. Server DB key
    server_keys = _load_server_keys()
    enc = server_keys.get(provider, "").strip()
    if enc:
        try:
            return decrypt(enc)
        except ValueError:
            log.warning(f"get_key: server key for '{provider}' failed to decrypt")

    # 3. Env var
    return _env_key(provider) or fallback


def save_server_key(provider: str, plaintext_key: str) -> None:
    """Encrypt and save a server-level API key to mng_clients."""
    from core.database import db
    from core.encryption import encrypt
    if not db.is_available():
        log.warning("save_server_key: DB not available")
        return
    try:
        keys = _load_server_keys()
        if plaintext_key.strip():
            keys[provider] = encrypt(plaintext_key.strip())
        else:
            keys.pop(provider, None)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_UPDATE_SERVER_KEYS, (json.dumps(keys),))
    except Exception as e:
        log.warning(f"save_server_key DB error: {e}")


def save_user_key(user_id: str, provider: str, plaintext_key: str) -> None:
    """Encrypt and upsert a per-user API key."""
    from core.database import db
    from core.encryption import encrypt
    if not db.is_available():
        raise RuntimeError("Database not available")
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _SQL_UPSERT_USER_KEY,
                (user_id, provider, encrypt(plaintext_key.strip())),
            )


def delete_user_key(user_id: str, provider: str) -> bool:
    """Remove a per-user API key. Returns True if a row was deleted."""
    from core.database import db
    if not db.is_available():
        return False
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_DELETE_USER_KEY, (user_id, provider))
            return cur.rowcount > 0


def list_user_keys(user_id: str) -> list[dict]:
    """Return masked key info for all providers the user has saved."""
    from core.database import db
    from core.encryption import decrypt
    if not db.is_available():
        return []
    result = []
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_LIST_USER_KEYS, (user_id,))
                for row in cur.fetchall():
                    try:
                        plain = decrypt(row[1])
                        masked = ("*" * (len(plain) - 4) + plain[-4:]) if len(plain) > 4 else "****"
                    except ValueError:
                        masked = "****"
                    result.append({
                        "provider":   row[0],
                        "masked":     masked,
                        "updated_at": row[2].isoformat() if row[2] else None,
                    })
    except Exception as e:
        log.debug(f"list_user_keys DB error: {e}")
    return result


def _mask(k: str) -> str:
    k = k.strip()
    if not k:
        return ""
    return ("*" * (len(k) - 4) + k[-4:]) if len(k) > 4 else "****"


def masked_keys() -> dict:
    """
    Server-level key status for admin panel.
    Source: 'db' (server DB key set), 'env' (only env var), 'unset'.
    """
    from core.encryption import decrypt
    server_keys = _load_server_keys()
    result = {}
    for p in _PROVIDERS:
        enc = server_keys.get(p, "").strip()
        if enc:
            try:
                plain = decrypt(enc)
                result[p] = {"masked": _mask(plain), "source": "db"}
                continue
            except ValueError:
                pass
        env = _env_key(p)
        if env:
            result[p] = {"masked": _mask(env), "source": "env"}
        else:
            result[p] = {"masked": "", "source": "unset"}
    return result
