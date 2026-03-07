"""
Server-side API key store — reads/writes {DATA_DIR}/api_keys.json.

Admin sets keys once via the Admin panel. All LLM calls use these server keys.
Falls back to settings env vars when a key is empty in the JSON file.
"""

import json
from pathlib import Path

from config import settings

_PROVIDERS = ("claude", "openai", "deepseek", "gemini", "grok")
_DEFAULT_KEYS = {p: "" for p in _PROVIDERS}

# Map provider name → settings attribute for env var fallback
_ENV_FALLBACKS = {
    "claude":   "anthropic_api_key",
    "openai":   "openai_api_key",
    "deepseek": "deepseek_api_key",
    "gemini":   "gemini_api_key",
    "grok":     "grok_api_key",
}


def _keys_path() -> Path:
    p = Path(settings.data_dir) / "api_keys.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_keys() -> dict:
    """Read api_keys.json; returns all-empty dict if missing."""
    path = _keys_path()
    if not path.exists():
        save_keys(_DEFAULT_KEYS)
        return dict(_DEFAULT_KEYS)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        # Ensure all providers present
        for p in _PROVIDERS:
            data.setdefault(p, "")
        return data
    except Exception:
        return dict(_DEFAULT_KEYS)


def save_keys(keys: dict) -> None:
    _keys_path().write_text(json.dumps(keys, indent=2), encoding="utf-8")


def get_key(provider: str, fallback: str = "") -> str:
    """
    Return the server key for a provider.
    Priority: api_keys.json → settings env var → fallback argument.
    """
    keys = load_keys()
    key = keys.get(provider, "").strip()
    if key:
        return key
    env_attr = _ENV_FALLBACKS.get(provider, "")
    env_key = getattr(settings, env_attr, "").strip() if env_attr else ""
    return env_key or fallback


def masked_keys() -> dict:
    """Return keys with all but last 4 chars replaced by *. Empty stays empty."""
    keys = load_keys()
    result = {}
    for p, k in keys.items():
        k = k.strip()
        if not k:
            result[p] = ""
        elif len(k) <= 4:
            result[p] = "****"
        else:
            result[p] = "*" * (len(k) - 4) + k[-4:]
    return result
