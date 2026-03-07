"""
Live API balance queries for each LLM provider.

Only DeepSeek exposes a public balance endpoint at this time.
All other providers (Anthropic, OpenAI, Gemini, Grok) return {"available": False}
because they do not offer a balance-check endpoint per API key.

Results are cached in-memory for 5 minutes to avoid hammering provider APIs.
"""

import asyncio
import time
from typing import Optional

import httpx

from core.api_keys import get_key

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


async def _fetch_deepseek_balance(api_key: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                "https://api.deepseek.com/user/balance",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            # Response: {"is_available": true, "balance_infos": [{"currency":"USD", "total_balance":"..."}]}
            infos = data.get("balance_infos", [])
            usd = next((b for b in infos if b.get("currency") == "USD"), infos[0] if infos else {})
            return {
                "available":             True,
                "balance_usd":           float(usd.get("total_balance", 0)),
                "granted_balance_usd":   float(usd.get("granted_balance", 0)),
                "topped_up_balance_usd": float(usd.get("topped_up_balance", 0)),
            }
    except Exception as e:
        return {"available": False, "reason": "api_error", "error": str(e)}


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
