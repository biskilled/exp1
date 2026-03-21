"""
Server-side API key store — reads/writes {DATA_DIR}/api_keys.json.

Admin sets keys once via the Admin panel. All LLM calls use these server keys.
Falls back to settings env vars when a key is empty in the JSON file.
"""

import json
from pathlib import Path

from core.config import settings

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
    p = Path(settings.secrets_dir) / "api_keys.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _env_key(provider: str) -> str:
    """Return the env-var value for a provider (empty string if not set)."""
    attr = _ENV_FALLBACKS.get(provider, "")
    return getattr(settings, attr, "").strip() if attr else ""


def load_keys() -> dict:
    """Read api_keys.json; on first creation seeds from current env vars."""
    path = _keys_path()
    if not path.exists():
        # Seed from env vars so admin sees existing keys immediately
        initial = {p: _env_key(p) for p in _PROVIDERS}
        save_keys(initial)
        return dict(initial)
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


def _mask(k: str) -> str:
    k = k.strip()
    if not k:
        return ""
    return ("*" * (len(k) - 4) + k[-4:]) if len(k) > 4 else "****"


def masked_keys() -> dict:
    """
    Return per-provider info: masked key + source ('saved' | 'env' | 'unset').

    'saved' — key stored in api_keys.json
    'env'   — json key empty, but env var is set (shown so admin knows it's active)
    'unset' — nowhere configured
    """
    keys = load_keys()
    result = {}
    for p in _PROVIDERS:
        saved = keys.get(p, "").strip()
        if saved:
            result[p] = {"masked": _mask(saved), "source": "saved"}
        else:
            env = _env_key(p)
            if env:
                result[p] = {"masked": _mask(env), "source": "env"}
            else:
                result[p] = {"masked": "", "source": "unset"}
    return result
