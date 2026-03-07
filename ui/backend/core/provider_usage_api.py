"""
Provider usage API fetcher — retrieves actual usage data from provider dashboards.

Supported providers:
  - OpenAI:    GET /v1/usage + /v1/dashboard/billing/subscription + /v1/dashboard/billing/credit_grants
  - Anthropic: GET /v1/organizations/{org_id}/usage  (requires org_id)

Results are stored as JSONL in {DATA_DIR}/provider_usage/{provider}_{date}.jsonl
and also returned as structured dicts.

Admin-only endpoint: POST /admin/fetch-provider-usage
"""

import asyncio
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import settings
from core.api_keys import get_key

try:
    import httpx as _httpx
except ImportError:
    _httpx = None  # type: ignore


# ── Storage helpers ────────────────────────────────────────────────────────────

def _usage_dir() -> Path:
    p = Path(settings.data_dir) / "provider_usage"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.mkdir(exist_ok=True)
    return p


def _save_result(provider: str, result: dict) -> None:
    """Append a fetch result to the provider's JSONL history file."""
    try:
        path = _usage_dir() / f"{provider}.jsonl"
        record = {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            **result,
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


def load_usage_history(provider: Optional[str] = None, limit: int = 20) -> list[dict]:
    """Load the last N fetch records per provider (or all providers)."""
    d = _usage_dir()
    results: list[dict] = []
    files = [d / f"{provider}.jsonl"] if provider else sorted(d.glob("*.jsonl"))
    for f in files:
        if not f.exists():
            continue
        prov = f.stem
        try:
            lines = [l.strip() for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
            for line in reversed(lines[-limit:]):
                try:
                    r = json.loads(line)
                    r.setdefault("provider", prov)
                    results.append(r)
                except Exception:
                    pass
        except Exception:
            pass
    results.sort(key=lambda r: r.get("fetched_at", ""), reverse=True)
    return results[:limit]


# ── HTTP helpers ───────────────────────────────────────────────────────────────

async def _http_get(url: str, headers: dict) -> dict:
    """Async GET — uses httpx if available, else asyncio + urllib."""
    if _httpx:
        async with _httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()
    else:
        def _sync():
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        return await asyncio.to_thread(_sync)


# ── OpenAI ─────────────────────────────────────────────────────────────────────

async def fetch_openai_usage(
    start_date: str,
    end_date: str,
    api_key: Optional[str] = None,
) -> dict:
    """
    Fetch OpenAI usage via /v1/usage API.
    start_date / end_date format: YYYY-MM-DD
    Returns structured summary + raw data.
    """
    key = api_key or get_key("openai")
    if not key:
        return {"provider": "openai", "error": "No API key configured", "ok": False}

    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    result: dict = {
        "provider": "openai",
        "ok": False,
        "start_date": start_date,
        "end_date": end_date,
        "usage": [],
        "subscription": None,
        "credit_grants": None,
        "errors": [],
    }

    # Usage data
    try:
        data = await _http_get(
            f"https://api.openai.com/v1/usage?start_date={start_date}&end_date={end_date}",
            headers,
        )
        result["usage"] = data.get("data", [])
        # Summarise
        total_prompt = sum(d.get("n_context_tokens_total", 0) for d in result["usage"])
        total_gen    = sum(d.get("n_generated_tokens_total", 0) for d in result["usage"])
        result["total_prompt_tokens"]     = total_prompt
        result["total_completion_tokens"] = total_gen
        result["ok"] = True
    except Exception as e:
        result["errors"].append(f"usage: {e}")

    # Subscription (credit balance)
    try:
        sub = await _http_get("https://api.openai.com/v1/dashboard/billing/subscription", headers)
        result["subscription"] = {
            "plan": sub.get("plan", {}).get("title", "unknown"),
            "hard_limit_usd":     sub.get("hard_limit_usd"),
            "soft_limit_usd":     sub.get("soft_limit_usd"),
            "system_hard_limit_usd": sub.get("system_hard_limit_usd"),
        }
    except Exception as e:
        result["errors"].append(f"subscription: {e}")

    # Credit grants
    try:
        grants = await _http_get("https://api.openai.com/v1/dashboard/billing/credit_grants", headers)
        result["credit_grants"] = {
            "total_granted":    grants.get("total_granted"),
            "total_used":       grants.get("total_used"),
            "total_available":  grants.get("total_available"),
            "grants":           grants.get("grants", []),
        }
    except Exception as e:
        result["errors"].append(f"credit_grants: {e}")

    _save_result("openai", result)
    return result


# ── Anthropic ──────────────────────────────────────────────────────────────────

async def fetch_anthropic_usage(
    start_date: str,
    end_date: str,
    org_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> dict:
    """
    Fetch Anthropic usage via /v1/organizations/{org_id}/usage.
    Requires an org_id (visible in the Anthropic console).
    start_date / end_date format: YYYY-MM-DD
    """
    key = api_key or get_key("claude")
    if not key:
        return {"provider": "anthropic", "error": "No API key configured", "ok": False}

    result: dict = {
        "provider": "anthropic",
        "ok": False,
        "start_date": start_date,
        "end_date": end_date,
        "usage": [],
        "errors": [],
    }

    if not org_id:
        result["errors"].append("org_id is required for Anthropic usage API")
        _save_result("anthropic", result)
        return result

    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    try:
        url = (
            f"https://api.anthropic.com/v1/organizations/{org_id}/usage"
            f"?start_time={start_date}T00:00:00Z&end_time={end_date}T23:59:59Z"
        )
        data = await _http_get(url, headers)
        result["usage"] = data.get("usage", data.get("data", []))
        total_input  = sum(u.get("input_tokens",  0) for u in result["usage"])
        total_output = sum(u.get("output_tokens", 0) for u in result["usage"])
        result["total_input_tokens"]  = total_input
        result["total_output_tokens"] = total_output
        result["ok"] = True
    except Exception as e:
        result["errors"].append(str(e))

    _save_result("anthropic", result)
    return result


# ── Dispatcher ─────────────────────────────────────────────────────────────────

async def fetch_provider_usage(
    provider: str,
    start_date: str,
    end_date: str,
    org_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> dict:
    """Dispatch to the right provider fetcher."""
    if provider == "openai":
        return await fetch_openai_usage(start_date, end_date, api_key)
    elif provider in ("anthropic", "claude"):
        return await fetch_anthropic_usage(start_date, end_date, org_id, api_key)
    else:
        return {
            "provider": provider,
            "ok": False,
            "error": f"Usage API not supported for provider '{provider}'",
        }
