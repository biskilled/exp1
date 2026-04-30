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
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# ── Pricing YAML path ──────────────────────────────────────────────────────────

_PRICING_YAML = Path(__file__).parent.parent.parent.parent / "workspace" / "_templates" / "pricing.yaml"


def _load_yaml_defaults() -> dict[str, dict[str, dict[str, float]]]:
    """Load per-token pricing from workspace/_templates/pricing.yaml."""
    try:
        if _PRICING_YAML.exists():
            import yaml
            with open(_PRICING_YAML) as f:
                data = yaml.safe_load(f) or {}
            # Normalise: each entry must be {"input": float, "output": float}
            result: dict = {}
            for provider, models in data.items():
                if isinstance(models, dict):
                    result[provider] = {
                        model: {k: float(v) for k, v in costs.items()}
                        for model, costs in models.items()
                        if isinstance(costs, dict)
                    }
            if result:
                return result
    except Exception as e:
        log.debug(f"Could not load pricing YAML: {e}")
    return {}


# ── Default per-token costs (USD/token) — fallback if YAML missing ─────────────

_HARDCODED_DEFAULTS: dict[str, dict[str, dict[str, float]]] = {
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

# Merge: YAML takes precedence over hardcoded, hardcoded fills any gaps
_yaml = _load_yaml_defaults()
_DEFAULTS: dict[str, dict[str, dict[str, float]]] = {}
for _p, _models in _HARDCODED_DEFAULTS.items():
    _DEFAULTS[_p] = {**_models, **_yaml.get(_p, {})}
for _p, _models in _yaml.items():
    if _p not in _DEFAULTS:
        _DEFAULTS[_p] = _models
del _yaml, _p, _models  # cleanup module namespace

_DEFAULT_CONFIG: dict = {
    "updated_at": None,
    "updated_by": None,
    "providers": _DEFAULTS,
}

# ── SQL ───────────────────────────────────────────────────────────────────────

_SQL_GET_COSTS = "SELECT provider_costs FROM mng_clients WHERE id=1"

_SQL_UPDATE_COSTS = "UPDATE mng_clients SET provider_costs=%s WHERE id=1"


def load_costs() -> dict:
    """Read provider costs from mng_clients; returns defaults if unavailable."""
    from core.database import db
    if db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_COSTS)
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
    from core.database import db
    cfg["updated_at"] = datetime.now(timezone.utc).isoformat()
    if updated_by:
        cfg["updated_by"] = updated_by
    if not db.is_available():
        log.warning("save_costs: DB not available")
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_UPDATE_COSTS, (json.dumps(cfg),))
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
