"""
Manual provider balance store — admin-entered current balance per provider.

Since Anthropic (personal accounts) and OpenAI do not expose per-API-key
balance endpoints, the admin can manually enter the current balance shown
in their provider dashboard. Stored in {DATA_DIR}/provider_balances.json.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from core.config import settings

_PROVIDERS = ("claude", "openai", "deepseek", "gemini", "grok")

_EMPTY_ENTRY: dict = {"balance_usd": None, "updated_at": None, "updated_by": None}


def _path() -> Path:
    p = Path(settings.data_dir) / "provider_usage" / "provider_balances.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_balances() -> dict:
    """Return manual balances for all providers."""
    path = _path()
    if not path.exists():
        return {p: dict(_EMPTY_ENTRY) for p in _PROVIDERS}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        for p in _PROVIDERS:
            data.setdefault(p, dict(_EMPTY_ENTRY))
        return data
    except Exception:
        return {p: dict(_EMPTY_ENTRY) for p in _PROVIDERS}


def save_balances(updates: dict, updated_by: str = "admin") -> dict:
    """
    Save manual balances for one or more providers.
    `updates` is a dict of {provider: balance_usd (float or None)}.
    Returns the full updated store.
    """
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
    _path().write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
