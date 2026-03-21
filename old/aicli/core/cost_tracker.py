"""
Cost tracker — records token usage and cost per workflow step.

Appends to workspace/<project>/runs/workflow_costs.jsonl.
Prints a Rich table after each workflow run.

Pricing is loaded from ui/backend/data/provider_costs.json (the single source of
truth managed by the admin UI). Falls back to built-in defaults if the file is
absent (e.g., backend not yet started).
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

# ── Fallback defaults (USD per token) — matches ui/backend/core/provider_costs.py ──
# Only used when ui/backend/data/provider_costs.json is not available.
_FALLBACK_PER_TOKEN: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6":         {"input": 0.000003,    "output": 0.000015},
    "claude-opus-4-6":           {"input": 0.000015,    "output": 0.000075},
    "claude-haiku-4-5-20251001": {"input": 0.0000008,   "output": 0.000004},
    "gpt-4.1":                   {"input": 0.000002,    "output": 0.000008},
    "gpt-4.1-mini":              {"input": 0.0000004,   "output": 0.0000016},
    "gpt-4o":                    {"input": 0.000005,    "output": 0.000015},
    "gpt-4o-mini":               {"input": 0.00000015,  "output": 0.0000006},
    "deepseek-chat":             {"input": 0.00000027,  "output": 0.0000011},
    "deepseek-reasoner":         {"input": 0.00000055,  "output": 0.00000219},
    "grok-3":                    {"input": 0.000003,    "output": 0.000015},
    "grok-3-fast":               {"input": 0.000005,    "output": 0.000025},
    "grok-3-mini":               {"input": 0.0000003,   "output": 0.0000005},
    "gemini-2.0-flash":          {"input": 0.0000001,   "output": 0.0000004},
    "gemini-1.5-pro":            {"input": 0.0000035,   "output": 0.0000105},
    "gemini-1.5-flash":          {"input": 0.000000075, "output": 0.0000003},
}

# Resolved once at import time — points to the canonical pricing file
_ENGINE_ROOT = Path(__file__).parent.parent.resolve()
_PROVIDER_COSTS_FILE = _ENGINE_ROOT / "ui" / "backend" / "data" / "provider_costs.json"


def _load_pricing() -> dict[str, dict[str, float]]:
    """
    Load per-token costs from ui/backend/data/provider_costs.json.
    Returns a flat model→{input,output} dict.
    Falls back to _FALLBACK_PER_TOKEN if the file is missing or malformed.
    """
    try:
        if _PROVIDER_COSTS_FILE.exists():
            data = json.loads(_PROVIDER_COSTS_FILE.read_text(encoding="utf-8"))
            flat: dict[str, dict[str, float]] = {}
            for _provider, models in data.get("providers", {}).items():
                for model, costs in models.items():
                    flat[model] = {
                        "input":  float(costs.get("input",  0.000001)),
                        "output": float(costs.get("output", 0.000005)),
                    }
            if flat:
                return flat
    except Exception:
        pass
    return dict(_FALLBACK_PER_TOKEN)


def _calc_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate USD cost using the canonical pricing file."""
    pricing = _load_pricing()
    costs = pricing.get(model)
    if costs is None:
        # Try prefix match (e.g. "claude-sonnet" matches "claude-sonnet-4-6")
        model_lower = model.lower()
        for m, c in pricing.items():
            if model_lower.startswith(m.lower()) or m.lower().startswith(model_lower):
                costs = c
                break
    if costs is None:
        costs = {"input": 0.000001, "output": 0.000005}  # conservative default
    return round(input_tokens * costs["input"] + output_tokens * costs["output"], 8)


class CostTracker:
    """Accumulates step costs for a workflow run."""

    def __init__(self, workflow_name: str, project_dir: Optional[Path] = None):
        self.workflow_name = workflow_name
        self.project_dir = project_dir
        self.steps: list[dict] = []
        self.started_at = datetime.now(timezone.utc)

    def record(
        self,
        step_name: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        output_preview: str = "",
        score: Optional[float] = None,
    ) -> float:
        """Record a step and return the cost in USD."""
        cost = _calc_cost(model, input_tokens, output_tokens)
        entry = {
            "step": step_name,
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost, 6),
            "output_preview": output_preview[:200],
        }
        if score is not None:
            entry["score"] = score
        self.steps.append(entry)
        return cost

    @property
    def total_cost(self) -> float:
        return sum(s["cost_usd"] for s in self.steps)

    @property
    def total_input_tokens(self) -> int:
        return sum(s["input_tokens"] for s in self.steps)

    @property
    def total_output_tokens(self) -> int:
        return sum(s["output_tokens"] for s in self.steps)

    def print_table(self, console: Optional[Console] = None) -> None:
        """Print a Rich table summarising this run's costs."""
        c = console or Console()
        table = Table(title=f"Workflow: {self.workflow_name} — cost summary", show_lines=True)
        table.add_column("Step", style="cyan")
        table.add_column("Provider", style="yellow")
        table.add_column("Model", style="dim")
        table.add_column("In tok", justify="right")
        table.add_column("Out tok", justify="right")
        table.add_column("Cost USD", justify="right", style="green")

        for s in self.steps:
            table.add_row(
                s["step"],
                s["provider"],
                s["model"],
                str(s["input_tokens"]),
                str(s["output_tokens"]),
                f"${s['cost_usd']:.5f}",
            )

        table.add_section()
        table.add_row(
            "[bold]TOTAL[/bold]", "", "",
            str(self.total_input_tokens),
            str(self.total_output_tokens),
            f"[bold]${self.total_cost:.5f}[/bold]",
        )
        c.print(table)

    def save(self, project_dir: Optional[Path] = None, run_data: Optional[dict] = None) -> Optional[Path]:
        """Append to runs/workflow_costs.jsonl and return the path."""
        dest = project_dir or self.project_dir
        if not dest:
            return None

        log_dir = dest / "runs"
        log_dir.mkdir(parents=True, exist_ok=True)
        costs_path = log_dir / "workflow_costs.jsonl"

        record = {
            "ts": self.started_at.isoformat(),
            "workflow": self.workflow_name,
            "steps": self.steps,
            "total_cost_usd": round(self.total_cost, 6),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
        }
        if run_data:
            record.update(run_data)

        with open(costs_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        return costs_path
