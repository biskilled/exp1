"""
Pricing engine — loads markup config from mng_clients.pricing_config,
applies admin-set markup, enforces free-tier limits.

Key functions:
    load_pricing()                                         → config dict
    save_pricing(cfg)                                      → persist to DB
    calculate_cost(provider, model, in, out, markup)       → USD
    can_user_access(user, provider, model)                 → (bool, reason)
"""

import json
import logging
from typing import Optional

log = logging.getLogger(__name__)

# ── Base costs (USD per 1M tokens: input, output) ─────────────────────────────

BASE_COSTS: dict[str, dict[str, tuple[float, float]]] = {
    "claude": {
        "claude-sonnet-4-6":         (3.00, 15.00),
        "claude-opus-4-6":           (15.00, 75.00),
        "claude-haiku-4-5-20251001": (0.80,  4.00),
    },
    "openai": {
        "gpt-4.1":      (2.00, 8.00),
        "gpt-4.1-mini": (0.40, 1.60),
        "gpt-4o":       (5.00, 15.00),
        "gpt-4o-mini":  (0.15, 0.60),
    },
    "deepseek": {
        "deepseek-chat":     (0.27, 1.10),
        "deepseek-reasoner": (0.55, 2.19),
    },
    "gemini": {
        "gemini-2.0-flash": (0.10, 0.40),
        "gemini-1.5-pro":   (3.50, 10.50),
        "gemini-1.5-flash": (0.075, 0.30),
    },
    "grok": {
        "grok-3":      (3.00, 15.00),
        "grok-3-fast": (5.00, 25.00),
    },
}

_DEFAULT_PRICING: dict = {
    "free_tier_limit_usd": 5.0,
    "free_tier_models": ["claude-haiku-4-5-20251001", "deepseek-chat", "gemini-2.0-flash"],
    "providers": {
        "claude":   {"markup_percent": 0},
        "openai":   {"markup_percent": 0},
        "deepseek": {"markup_percent": 0},
        "gemini":   {"markup_percent": 0},
        "grok":     {"markup_percent": 0},
    },
}

# ── SQL ───────────────────────────────────────────────────────────────────────

_SQL_GET_PRICING = "SELECT pricing_config FROM mng_clients WHERE id=1"

_SQL_UPDATE_PRICING = "UPDATE mng_clients SET pricing_config=%s WHERE id=1"


def load_pricing() -> dict:
    """Read pricing config from mng_clients; falls back to defaults."""
    from core.database import db
    if db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_PRICING)
                    row = cur.fetchone()
                    if row and row[0]:
                        data = row[0]
                        for k, v in _DEFAULT_PRICING.items():
                            if k not in data:
                                data[k] = v
                        return data
        except Exception as e:
            log.debug(f"load_pricing DB error: {e}")
    return dict(_DEFAULT_PRICING)


def save_pricing(cfg: dict) -> None:
    """Persist pricing config to mng_clients."""
    from core.database import db
    if not db.is_available():
        log.warning("save_pricing: DB not available")
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_UPDATE_PRICING, (json.dumps(cfg),))
    except Exception as e:
        log.warning(f"save_pricing DB error: {e}")


def calculate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    markup_pct: float = 0.0,
) -> float:
    """Return cost in USD including markup. Falls back to $1/$5 per 1M if model unknown."""
    provider_costs = BASE_COSTS.get(provider, {})
    inp_price, out_price = provider_costs.get(model, (1.00, 5.00))
    base = (input_tokens * inp_price + output_tokens * out_price) / 1_000_000
    return round(base * (1 + markup_pct / 100), 8)


def can_user_access(user: dict, provider: str, model: str) -> tuple[bool, str]:
    """
    Check whether this user may call this provider/model.
    Returns (True, "") or (False, reason).
    Admins always pass.
    """
    role = user.get("role", "free")

    if role == "admin":
        return True, ""

    pricing = load_pricing()
    free_limit = pricing.get("free_tier_limit_usd", 5.0)
    free_models: list[str] = pricing.get("free_tier_models", [])

    balance_added = user.get("balance_added_usd", 0.0)
    balance_used  = user.get("balance_used_usd", 0.0)
    balance = balance_added - balance_used

    if role == "free":
        if model not in free_models:
            return False, f"Model '{model}' requires a paid account. Upgrade to access this model."
        if balance_used >= free_limit:
            return False, f"Free tier limit of ${free_limit:.2f} reached. Add credits to continue."
        return True, ""

    if balance <= 0:
        return False, "Insufficient balance. Please add credits to your account."

    return True, ""
