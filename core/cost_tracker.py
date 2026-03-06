"""
Cost tracker — records token usage and cost per workflow step.

Appends to workspace/<project>/.aicli/workflow_costs.jsonl.
Prints a Rich table after each workflow run.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

# Cost per 1M tokens (input / output) in USD — update as pricing changes
PRICING: dict[str, dict] = {
    # Anthropic
    "claude-sonnet-4-6":      {"input": 3.00,  "output": 15.00},
    "claude-opus-4-6":        {"input": 15.00, "output": 75.00},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
    # OpenAI
    "gpt-4.1":                {"input": 2.00,  "output": 8.00},
    "gpt-4o":                 {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini":            {"input": 0.15,  "output": 0.60},
    # DeepSeek
    "deepseek-chat":          {"input": 0.27,  "output": 1.10},
    "deepseek-reasoner":      {"input": 0.55,  "output": 2.19},
    # xAI
    "grok-3":                 {"input": 3.00,  "output": 15.00},
    "grok-3-fast":            {"input": 0.60,  "output": 4.00},
    "grok-3-mini":            {"input": 0.30,  "output": 0.50},
    # Gemini
    "gemini-2.0-flash":       {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro":         {"input": 1.25,  "output": 5.00},
}


def _calc_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICING.get(model, {"input": 1.00, "output": 5.00})
    return (input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000


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

    def save(self, run_data: dict | None = None) -> Path | None:
        """Append to workflow_costs.jsonl and return the path."""
        if not self.project_dir:
            return None

        log_dir = self.project_dir / ".aicli"
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
