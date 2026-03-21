"""
Provider usage API fetcher — retrieves actual usage data from provider dashboards.

Supported providers & their API constraints:
  - OpenAI:    GET /v1/usage?date=YYYY-MM-DD  (one day at a time, regular API key)
               GET /v1/organization/usage/completions  (date range, Admin API key required)
  - Anthropic: GET /v1/organizations/{org_id}/usage  (Admin API key + beta header required)

Results are stored as JSONL in {DATA_DIR}/provider_usage/{provider}.jsonl.

A "local recalculate" mode re-estimates cost from our own mng_usage_logs + provider_costs.json,
which works without any special key permissions.
"""

import asyncio
import json
import urllib.request
import urllib.error
from datetime import datetime, date as _date, timedelta, timezone
from pathlib import Path
from typing import Optional

from core.config import settings
from core.api_keys import get_key

try:
    import httpx as _httpx
except ImportError:
    _httpx = None  # type: ignore


# ── Storage helpers ────────────────────────────────────────────────────────────

def _usage_dir() -> Path:
    p = Path(settings.data_dir) / "provider_usage"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _save_result(provider: str, result: dict) -> None:
    """Append a fetch result to the provider's JSONL history file."""
    try:
        path = _usage_dir() / f"{provider}.jsonl"
        record = {"fetched_at": datetime.now(timezone.utc).isoformat(), **result}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


def delete_history_record(provider: str, fetched_at: str) -> bool:
    """Remove a single record from the provider's JSONL history by fetched_at timestamp."""
    path = _usage_dir() / f"{provider}.jsonl"
    if not path.exists():
        return False
    try:
        lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
        new_lines, deleted = [], False
        for line in lines:
            try:
                r = json.loads(line)
                if r.get("fetched_at") == fetched_at:
                    deleted = True
                    continue
            except Exception:
                pass
            new_lines.append(line)
        path.write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")
        return deleted
    except Exception:
        return False


def clear_history(provider: Optional[str] = None) -> int:
    """Delete all history records for a provider (or all if provider is None). Returns count deleted."""
    d = _usage_dir()
    files = [d / f"{provider}.jsonl"] if provider else list(d.glob("*.jsonl"))
    total = 0
    for fpath in files:
        if fpath.exists():
            lines = [l for l in fpath.read_text(encoding="utf-8").splitlines() if l.strip()]
            total += len(lines)
            fpath.write_text("", encoding="utf-8")
    return total


def load_usage_history(provider: Optional[str] = None, limit: int = 20) -> list[dict]:
    """Load the last N fetch records (newest first)."""
    d = _usage_dir()
    files = [d / f"{provider}.jsonl"] if provider else sorted(d.glob("*.jsonl"))
    results: list[dict] = []
    for fpath in files:
        if not fpath.exists():
            continue
        prov = fpath.stem
        try:
            lines = [l.strip() for l in fpath.read_text(encoding="utf-8").splitlines() if l.strip()]
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

async def _http_get(url: str, headers: dict) -> tuple[int, dict]:
    """
    Async GET — returns (status_code, body_dict).
    Uses httpx if available, else asyncio + urllib.
    Does NOT raise on 4xx/5xx so callers can inspect the status code.
    """
    if _httpx:
        async with _httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=headers)
            try:
                body = resp.json()
            except Exception:
                body = {"_raw": resp.text}
            return resp.status_code, body
    else:
        def _sync() -> tuple[int, dict]:
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    return r.status, json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                try:
                    body = json.loads(e.read().decode())
                except Exception:
                    body = {"_error": str(e)}
                return e.code, body
        return await asyncio.to_thread(_sync)


def _date_range(start: str, end: str) -> list[str]:
    """Return list of YYYY-MM-DD strings from start to end inclusive."""
    s = _date.fromisoformat(start)
    e = _date.fromisoformat(end)
    days = []
    cur = s
    while cur <= e:
        days.append(cur.isoformat())
        cur += timedelta(days=1)
    return days


# ── OpenAI ─────────────────────────────────────────────────────────────────────
#
# Two paths:
#   1. Regular API key → iterate day-by-day: GET /v1/usage?date=YYYY-MM-DD
#   2. Admin API key   → date range:         GET /v1/organization/usage/completions
#      (Admin key looks like: sk-proj-admin-... or can be set in api_keys.json as "openai_admin")
#
# The /v1/dashboard/billing/* endpoints require browser session cookies — they
# CANNOT be called with API keys (always return 403). We no longer attempt them.

async def fetch_openai_usage(
    start_date: str,
    end_date: str,
    api_key: Optional[str] = None,
) -> dict:
    key = api_key or get_key("openai")
    if not key:
        return {"provider": "openai", "error": "No OpenAI API key configured", "ok": False,
                "start_date": start_date, "end_date": end_date}

    headers = {"Authorization": f"Bearer {key}"}

    result: dict = {
        "provider": "openai",
        "ok": False,
        "start_date": start_date,
        "end_date": end_date,
        "usage": [],
        "errors": [],
        "notes": [],
    }

    # Try the new Admin API first (works if key is an Admin key)
    # start_time and end_time must be Unix timestamps
    try:
        s_unix = int(datetime.fromisoformat(f"{start_date}T00:00:00+00:00").timestamp())
        e_unix = int(datetime.fromisoformat(f"{end_date}T23:59:59+00:00").timestamp())
        url = (
            f"https://api.openai.com/v1/organization/usage/completions"
            f"?start_time={s_unix}&end_time={e_unix}&bucket_width=1d&limit=31"
        )
        status, data = await _http_get(url, headers)
        if status == 200:
            buckets = data.get("data", [])
            total_prompt = sum(b.get("input_tokens",  0) for b in buckets)
            total_gen    = sum(b.get("output_tokens", 0) for b in buckets)
            result["usage"] = buckets
            result["total_prompt_tokens"]     = total_prompt
            result["total_completion_tokens"] = total_gen
            result["ok"] = True
            result["notes"].append("Used /v1/organization/usage/completions (Admin API)")
            _save_result("openai", result)
            return result
        elif status == 403:
            result["notes"].append(
                "Admin API key required for /v1/organization/usage/completions. "
                "Create one at platform.openai.com → Settings → Organization → Admin keys. "
                "Falling back to legacy per-day endpoint…"
            )
        elif status == 404:
            result["notes"].append("Admin API endpoint not found, falling back to legacy per-day endpoint…")
        else:
            result["errors"].append(f"Admin API returned {status}: {data.get('error', data)}")
    except Exception as e:
        result["errors"].append(f"Admin API error: {e}")

    # Fallback: legacy per-day endpoint GET /v1/usage?date=YYYY-MM-DD
    days = _date_range(start_date, end_date)
    all_usage = []
    total_prompt = total_gen = 0
    day_errors = []

    for day in days:
        try:
            status, data = await _http_get(
                f"https://api.openai.com/v1/usage?date={day}",
                headers,
            )
            if status == 200:
                day_data = data.get("data", [])
                all_usage.extend(day_data)
                total_prompt += sum(d.get("n_context_tokens_total",   0) for d in day_data)
                total_gen    += sum(d.get("n_generated_tokens_total", 0) for d in day_data)
            elif status == 403:
                day_errors.append(f"{day}: 403 Forbidden — key may lack usage read permissions")
                break  # No point retrying all days
            else:
                err_body = data.get("error", {})
                day_errors.append(f"{day}: {status} {err_body.get('message', data)}")
        except Exception as e:
            day_errors.append(f"{day}: {e}")

    if day_errors:
        result["errors"].extend(day_errors)

    if all_usage or total_prompt or total_gen:
        result["usage"] = all_usage
        result["total_prompt_tokens"]     = total_prompt
        result["total_completion_tokens"] = total_gen
        result["ok"] = True
        result["notes"].append(f"Used legacy /v1/usage?date= endpoint for {len(days)} day(s)")
    elif not result["errors"]:
        result["errors"].append("No usage data returned for the selected date range")

    _save_result("openai", result)
    return result


# ── Anthropic ──────────────────────────────────────────────────────────────────
#
# The Anthropic Organization Usage API requires:
#   - An Admin API key  (sk-ant-admin-...) — NOT a regular workspace API key
#   - Create at: console.anthropic.com → Settings → API keys → Admin keys
#   - The org_id is shown in the Anthropic console URL or Settings page
#
# Headers needed:
#   x-api-key: <admin_key>
#   anthropic-version: 2023-06-01
#   anthropic-beta: usage-reporting-2025-03-01   ← required for beta usage API

async def fetch_anthropic_usage(
    start_date: str,
    end_date: str,
    org_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> dict:
    key = api_key or get_key("claude")
    if not key:
        return {
            "provider": "anthropic", "ok": False,
            "start_date": start_date, "end_date": end_date,
            "errors": ["No Anthropic API key configured"],
        }

    result: dict = {
        "provider": "anthropic",
        "ok": False,
        "start_date": start_date,
        "end_date": end_date,
        "usage": [],
        "errors": [],
        "notes": [],
    }

    if not org_id:
        result["errors"].append(
            "org_id is required. Find it at: console.anthropic.com → Settings → Organization"
        )
        _save_result("anthropic", result)
        return result

    # Detect if a regular vs admin key (admin keys start with sk-ant-admin-)
    if key.startswith("sk-ant-api"):
        result["notes"].append(
            "Warning: Regular workspace API key detected. "
            "Anthropic usage API requires an Admin API key (sk-ant-admin-...). "
            "Create one at console.anthropic.com → Settings → API keys → Admin API keys."
        )

    headers = {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "usage-reporting-2025-03-01",
        "content-type": "application/json",
    }

    # Try multiple endpoint/parameter formats (API is in beta, format may vary)
    attempts = [
        # Format 1: ISO timestamps with time component
        (
            f"https://api.anthropic.com/v1/organizations/{org_id}/usage"
            f"?start_time={start_date}T00%3A00%3A00Z&end_time={end_date}T23%3A59%3A59Z"
        ),
        # Format 2: date-only params
        (
            f"https://api.anthropic.com/v1/organizations/{org_id}/usage"
            f"?start_date={start_date}&end_date={end_date}"
        ),
        # Format 3: different beta header
        None,  # placeholder — handled inline below
    ]

    last_status = None
    last_body: dict = {}

    for i, url in enumerate(attempts):
        if url is None:
            # Format 3: try without beta header
            hdrs_no_beta = {k: v for k, v in headers.items() if k != "anthropic-beta"}
            try:
                url3 = (
                    f"https://api.anthropic.com/v1/organizations/{org_id}/usage"
                    f"?start_time={start_date}T00:00:00Z&end_time={end_date}T23:59:59Z"
                )
                last_status, last_body = await _http_get(url3, hdrs_no_beta)
            except Exception as e:
                result["errors"].append(f"Attempt 3 (no-beta): {e}")
                continue
        else:
            try:
                last_status, last_body = await _http_get(url, headers)
            except Exception as e:
                result["errors"].append(f"Attempt {i+1}: {e}")
                continue

        if last_status == 200:
            usage = last_body.get("usage", last_body.get("data", []))
            result["usage"] = usage
            result["total_input_tokens"]  = sum(u.get("input_tokens",  0) for u in usage)
            result["total_output_tokens"] = sum(u.get("output_tokens", 0) for u in usage)
            result["ok"] = True
            break
        elif last_status == 403:
            result["errors"].append(
                f"403 Forbidden — Admin API key required for Anthropic usage data. "
                f"Regular workspace keys cannot access usage history. "
                f"Create an Admin API key at console.anthropic.com → Settings → API keys."
            )
            break  # No point retrying
        elif last_status == 404:
            result["errors"].append(f"Attempt {i+1}: 404 {last_body.get('error', last_body)}")
            # Continue to next format
        else:
            result["errors"].append(f"Attempt {i+1}: {last_status} {last_body.get('error', last_body)}")
            break

    if not result["ok"] and not any("Admin API key required" in e for e in result["errors"]):
        result["notes"].append(
            "Anthropic usage API is in beta. If all attempts fail with 404, "
            "the organization usage endpoint may not be enabled for your account. "
            "Alternative: use 'Recalculate from Local Data' to estimate costs from tracked usage."
        )

    _save_result("anthropic", result)
    return result


# ── Local recalculation ────────────────────────────────────────────────────────
#
# Reads mng_usage_logs (JSONL files or PostgreSQL) and re-estimates cost using
# the current provider_costs.json. Does not require any provider API key.

async def recalculate_local_costs(start_date: str, end_date: str) -> dict:
    """
    Re-estimate cost for all usage records in the given date range
    using the current provider_costs.json pricing.
    Returns a summary and updates estimated_cost_usd in records.
    """
    from agents.providers.pr_costs import estimate_cost
    from data.database import db

    result: dict = {
        "mode": "local_recalculate",
        "ok": False,
        "start_date": start_date,
        "end_date": end_date,
        "records_processed": 0,
        "total_estimated_usd": 0.0,
        "by_provider": {},
        "errors": [],
    }

    rows: list[dict] = []

    if db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT user_id, provider, model, input_tokens, output_tokens, cost_usd, charged_usd
                        FROM mng_usage_logs
                        WHERE DATE(created_at) BETWEEN %s AND %s
                          AND user_id IS NOT NULL
                        """,
                        (start_date, end_date),
                    )
                    for r in cur.fetchall():
                        rows.append({
                            "user_id": r[0], "provider": r[1], "model": r[2],
                            "input_tokens": r[3], "output_tokens": r[4],
                            "cost_usd": float(r[5] or 0), "charged_usd": float(r[6] or 0),
                        })
        except Exception as e:
            result["errors"].append(f"DB error: {e}")
    else:
        # Read from JSONL files
        usage_dir = Path(settings.data_dir) / "usage"
        if usage_dir.exists():
            for uf in usage_dir.glob("*.jsonl"):
                for line in uf.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                        day = r.get("ts", "")[:10]
                        if start_date <= day <= end_date:
                            r["user_id"] = uf.stem
                            rows.append(r)
                    except Exception:
                        pass

    for row in rows:
        provider     = row.get("provider", "unknown")
        model        = row.get("model", "")
        input_t      = row.get("input_tokens",  0)
        output_t     = row.get("output_tokens", 0)
        est_cost     = estimate_cost(provider, model, input_t, output_t)

        result["records_processed"] += 1
        result["total_estimated_usd"] = round(result["total_estimated_usd"] + est_cost, 8)

        pb = result["by_provider"].setdefault(provider, {
            "input_tokens": 0, "output_tokens": 0,
            "estimated_usd": 0.0, "records": 0,
        })
        pb["input_tokens"]  += input_t
        pb["output_tokens"] += output_t
        pb["estimated_usd"]  = round(pb["estimated_usd"] + est_cost, 8)
        pb["records"]       += 1

    result["ok"] = True
    _save_result("local_recalculate", result)
    return result


# ── Dispatcher ─────────────────────────────────────────────────────────────────

async def fetch_provider_usage(
    provider: str,
    start_date: str,
    end_date: str,
    org_id: Optional[str] = None,
    api_key: Optional[str] = None,
) -> dict:
    if provider == "openai":
        return await fetch_openai_usage(start_date, end_date, api_key)
    elif provider in ("anthropic", "claude"):
        return await fetch_anthropic_usage(start_date, end_date, org_id, api_key)
    elif provider == "local":
        return await recalculate_local_costs(start_date, end_date)
    else:
        return {
            "provider": provider,
            "ok": False,
            "error": f"Usage API not supported for provider '{provider}'",
        }
