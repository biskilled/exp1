"""
Live API balance queries for each LLM provider.

Only DeepSeek exposes a public balance endpoint at this time.
All other providers (Anthropic, OpenAI, Gemini, Grok) return {"available": False}
because they do not offer a balance-check endpoint per API key.

Results are cached in-memory for 5 minutes to avoid hammering provider APIs.
"""

import asyncio
import time
import urllib.request
import urllib.error
import json as _json
from typing import Optional

from core.api_keys import get_key

# httpx is preferred but optional — falls back to stdlib urllib
try:
    import httpx as _httpx
except ImportError:
    _httpx = None

_CACHE: dict[str, tuple[float, dict]] = {}   # provider → (expire_ts, result)
_TTL = 300  # 5 minutes


def _cached(provider: str) -> Optional[dict]:
    entry = _CACHE.get(provider)
    if entry and time.time() < entry[0]:
        return entry[1]
    return None


def _store(provider: str, result: dict) -> dict:
    _CACHE[provider] = (time.time() + _TTL, result)
    return result


def _parse_deepseek_response(data: dict) -> dict:
    infos = data.get("balance_infos", [])
    usd = next((b for b in infos if b.get("currency") == "USD"), infos[0] if infos else {})
    return {
        "available":             True,
        "balance_usd":           float(usd.get("total_balance", 0)),
        "granted_balance_usd":   float(usd.get("granted_balance", 0)),
        "topped_up_balance_usd": float(usd.get("topped_up_balance", 0)),
    }


async def _fetch_deepseek_balance(api_key: str) -> dict:
    if _httpx is not None:
        # Preferred: async httpx
        try:
            async with _httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(
                    "https://api.deepseek.com/user/balance",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                resp.raise_for_status()
                return _parse_deepseek_response(resp.json())
        except Exception as e:
            return {"available": False, "reason": "api_error", "error": str(e)}
    else:
        # Fallback: stdlib urllib (synchronous, run in thread so we don't block event loop)
        def _sync_fetch() -> dict:
            try:
                req = urllib.request.Request(
                    "https://api.deepseek.com/user/balance",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = _json.loads(resp.read().decode())
                return _parse_deepseek_response(data)
            except Exception as e:
                return {"available": False, "reason": "api_error", "error": str(e)}

        return await asyncio.to_thread(_sync_fetch)


async def get_provider_balance(provider: str) -> dict:
    """
    Return live balance info for one provider.

    Returns {"available": False, "reason": "..."} when unsupported or key missing.
    """
    cached = _cached(provider)
    if cached is not None:
        return cached

    key = get_key(provider)
    if not key:
        return _store(provider, {"available": False, "reason": "no_key"})

    if provider == "deepseek":
        result = await _fetch_deepseek_balance(key)
    else:
        # Anthropic, OpenAI, Gemini, Grok do not offer a balance endpoint per API key
        result = {"available": False, "reason": "unsupported"}

    return _store(provider, result)


async def get_all_balances() -> dict:
    """Fetch balances for all providers concurrently."""
    providers = ("claude", "openai", "deepseek", "gemini", "grok")
    results = await asyncio.gather(*[get_provider_balance(p) for p in providers])
    return dict(zip(providers, results))
