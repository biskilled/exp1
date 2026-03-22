"""
Usage tracking router.

Usage is stored per-user in {DATA_DIR}/usage/{user_id}.jsonl.
Each line: {ts, provider, model, input_tokens, output_tokens, cost_usd}

GET /usage/me          → totals + last 50 calls for current user
GET /usage/admin       → all-users summary (admin only)

Helper exposed for chat.py:
    log_usage(user_id, provider, model, input_tokens, output_tokens)
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status

from core.config import settings
from core.auth import get_current_user
from core.database import db
from agents.providers.pr_pricing import calculate_cost
from core.user import find_by_id, list_users

router = APIRouter()


def _cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Derive provider from model name prefix for calculate_cost lookup."""
    if model.startswith("claude"):
        provider = "claude"
    elif model.startswith("gpt"):
        provider = "openai"
    elif model.startswith("deepseek"):
        provider = "deepseek"
    elif model.startswith("gemini"):
        provider = "gemini"
    elif model.startswith("grok"):
        provider = "grok"
    else:
        provider = "claude"  # safe default
    return calculate_cost(provider, model, input_tokens, output_tokens, markup_pct=0)


def _usage_path(user_id: str) -> Path:
    p = Path(settings.data_dir) / "usage" / f"{user_id}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def log_usage(
    user_id: str,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    charged_usd: float = 0.0,
) -> None:
    """Append one usage record to PostgreSQL (when available) and JSONL file."""
    real_cost = _cost(model, input_tokens, output_tokens)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": real_cost,
        "charged_usd": charged_usd,
    }
    # Primary: PostgreSQL
    if db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO mng_usage_logs
                           (user_id, provider, model, input_tokens, output_tokens, cost_usd, charged_usd)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (user_id, provider, model, input_tokens, output_tokens, real_cost, charged_usd),
                    )
        except Exception:
            pass
    # Always write to file (fallback / portability)
    with open(_usage_path(user_id), "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _load_usage(user_id: str) -> list[dict]:
    path = _usage_path(user_id)
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records


def _aggregate(records: list[dict]) -> dict:
    total_input = sum(r.get("input_tokens", 0) for r in records)
    total_output = sum(r.get("output_tokens", 0) for r in records)
    total_cost = round(sum(r.get("cost_usd", 0.0) for r in records), 6)
    calls_by_provider: dict[str, int] = {}
    for r in records:
        calls_by_provider[r.get("provider", "?")] = (
            calls_by_provider.get(r.get("provider", "?"), 0) + 1
        )
    return {
        "total_calls": len(records),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_cost_usd": total_cost,
        "calls_by_provider": calls_by_provider,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/me")
async def my_usage(current_user: dict = Depends(get_current_user)):
    records = _load_usage(current_user["sub"])
    return {
        **_aggregate(records),
        "recent": records[-50:],
    }


@router.get("/admin")
async def admin_usage(current_user: dict = Depends(get_current_user)):
    user = find_by_id(current_user["sub"])
    if not user or not user.get("is_admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")

    result = []
    for u in list_users():
        records = _load_usage(u["id"])
        result.append({
            "user_id": u["id"],
            "email": u["email"],
            "created_at": u.get("created_at"),
            **_aggregate(records),
        })
    return result
