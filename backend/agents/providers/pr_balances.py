"""
Manual provider balance store — admin-entered current balance per provider,
stored in mng_clients.provider_balances.

Since Anthropic (personal accounts) and OpenAI do not expose per-API-key
balance endpoints, the admin can manually enter the current balance shown
in their provider dashboard.
"""

import json
import logging
from datetime import datetime, timezone

log = logging.getLogger(__name__)

_PROVIDERS = ("claude", "openai", "deepseek", "gemini", "grok")
_EMPTY_ENTRY: dict = {"balance_usd": None, "updated_at": None, "updated_by": None}


def load_balances() -> dict:
    """Return manual balances for all providers from mng_clients."""
    from core.database import db
    if db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT provider_balances FROM mng_clients WHERE id=1")
                    row = cur.fetchone()
                    if row and row[0]:
                        data = row[0]
                        for p in _PROVIDERS:
                            data.setdefault(p, dict(_EMPTY_ENTRY))
                        return data
        except Exception as e:
            log.debug(f"load_balances DB error: {e}")
    return {p: dict(_EMPTY_ENTRY) for p in _PROVIDERS}


def save_balances(updates: dict, updated_by: str = "admin") -> dict:
    """
    Save manual balances for one or more providers.
    `updates` is a dict of {provider: balance_usd (float or None)}.
    Returns the full updated store.
    """
    from core.database import db
    data = load_balances()
    now = datetime.now(timezone.utc).isoformat()
    for provider, balance_usd in updates.items():
        if provider not in _PROVIDERS:
            continue
        data[provider] = {
            "balance_usd": float(balance_usd) if balance_usd is not None else None,
            "updated_at":  now,
            "updated_by":  updated_by,
        }
    if not db.is_available():
        log.warning("save_balances: DB not available")
        return data
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE mng_clients SET provider_balances=%s WHERE id=1",
                    (json.dumps(data),),
                )
    except Exception as e:
        log.warning(f"save_balances DB error: {e}")
    return data
