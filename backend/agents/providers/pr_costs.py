"""
Provider cost configuration — per-token pricing stored in mng_clients.provider_costs.

Manages the actual API cost per token for each provider/model combination.
Separate from pr_pricing.py (which handles markup and free-tier policy).

Key functions:
    load_costs()                              → full config dict
    save_costs(cfg)                           → persist to DB
    estimate_cost(provider, model, in, out)   → float (USD, no markup)
    get_model_list()                          → list of {provider, model, input, output}
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger(__name__)

# ── Default per-token costs (USD/token) ────────────────────────────────────────

_DEFAULTS: dict[str, dict[str, dict[str, float]]] = {
    "claude": {
        "claude-sonnet-4-6":         {"input": 0.000003,   "output": 0.000015},
        "claude-opus-4-6":           {"input": 0.000015,   "output": 0.000075},
        "claude-haiku-4-5-20251001": {"input": 0.0000008,  "output": 0.000004},
    },
    "openai": {
        "gpt-4.1":      {"input": 0.000002,   "output": 0.000008},
        "gpt-4.1-mini": {"input": 0.0000004,  "output": 0.0000016},
        "gpt-4o":       {"input": 0.000005,   "output": 0.000015},
        "gpt-4o-mini":  {"input": 0.00000015, "output": 0.0000006},
    },
    "deepseek": {
        "deepseek-chat":     {"input": 0.00000027, "output": 0.0000011},
        "deepseek-reasoner": {"input": 0.00000055, "output": 0.00000219},
    },
    "gemini": {
        "gemini-2.0-flash": {"input": 0.0000001,   "output": 0.0000004},
        "gemini-1.5-pro":   {"input": 0.0000035,   "output": 0.0000105},
        "gemini-1.5-flash": {"input": 0.000000075, "output": 0.0000003},
    },
    "grok": {
        "grok-3":      {"input": 0.000003, "output": 0.000015},
        "grok-3-fast": {"input": 0.000005, "output": 0.000025},
    },
}

_DEFAULT_CONFIG: dict = {
    "updated_at": None,
    "updated_by": None,
    "providers": _DEFAULTS,
}


def load_costs() -> dict:
    """Read provider costs from mng_clients; returns defaults if unavailable."""
    from data.database import db
    if db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT provider_costs FROM mng_clients WHERE id=1")
                    row = cur.fetchone()
                    if row and row[0]:
                        data = row[0]
                        providers = data.setdefault("providers", {})
                        for prov, models in _DEFAULTS.items():
                            if prov not in providers:
                                providers[prov] = dict(models)
                            else:
                                for model, costs in models.items():
                                    if model not in providers[prov]:
                                        providers[prov][model] = dict(costs)
                        return data
        except Exception as e:
            log.debug(f"load_costs DB error: {e}")
    return dict(_DEFAULT_CONFIG)


def save_costs(cfg: dict, updated_by: Optional[str] = None) -> None:
    """Persist provider costs to mng_clients."""
    from data.database import db
    cfg["updated_at"] = datetime.now(timezone.utc).isoformat()
    if updated_by:
        cfg["updated_by"] = updated_by
    if not db.is_available():
        log.warning("save_costs: DB not available")
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE mng_clients SET provider_costs=%s WHERE id=1",
                    (json.dumps(cfg),),
                )
    except Exception as e:
        log.warning(f"save_costs DB error: {e}")


def estimate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Estimate real cost in USD. Falls back to conservative default if model unknown."""
    try:
        cfg = load_costs()
        providers = cfg.get("providers", {})
        model_costs = providers.get(provider, {}).get(model)
        if model_costs is None:
            model_lower = model.lower()
            for m, costs in providers.get(provider, {}).items():
                if model_lower.startswith(m.lower()) or m.lower().startswith(model_lower):
                    model_costs = costs
                    break
        if model_costs is None:
            return round((input_tokens * 0.000001) + (output_tokens * 0.000005), 8)
        inp = float(model_costs.get("input", 0.000001))
        out = float(model_costs.get("output", 0.000005))
        return round(input_tokens * inp + output_tokens * out, 8)
    except Exception:
        return 0.0


def get_model_list() -> list[dict]:
    """Return a flat list of all models with their costs for the admin editor."""
    cfg = load_costs()
    rows: list[dict] = []
    for provider, models in cfg.get("providers", {}).items():
        for model, costs in models.items():
            rows.append({
                "provider": provider,
                "model":    model,
                "input":    float(costs.get("input",  0.0)),
                "output":   float(costs.get("output", 0.0)),
            })
    return rows
