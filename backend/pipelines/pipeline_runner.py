"""
workflow_runner.py — Sequential multi-agent workflow executor.

Reads YAML definitions from workspace/{project}/workflows/{name}/workflow.yaml.
Runs each step (agent) with the specified LLM, saving state after every step to:
  workspace/{project}/_system/runs/{run_id}.json

Pause/resume pattern:
  After each step: status → 'waiting', background task exits.
  POST /workflows/runs/{run_id}/decision resumes from next (or same) step.

YAML step fields:
  name, provider, model, prompt (path relative to workspace/{project}/prompts/),
  inject_context (bool, default true), score_field (str), score_min (number).
  If score_field+score_min set: auto-continue when score >= score_min,
  auto-retry when score < score_min (up to max_iterations), else pause for user.
"""
from __future__ import annotations

import asyncio
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

from core.config import settings
from core.api_keys import get_key
from agents import providers as llm_clients

# ── File helpers ──────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _run_dir(project: str) -> Path:
    return Path(settings.workspace_dir) / project / "_system" / "runs"

def _run_path(project: str, run_id: str) -> Path:
    return _run_dir(project) / f"{run_id}.json"

def _save(project: str, run_id: str, data: dict) -> None:
    p = _run_path(project, run_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, default=str))

def load_run(project: str, run_id: str) -> dict:
    p = _run_path(project, run_id)
    if not p.exists():
        raise FileNotFoundError(f"Run not found: {run_id}")
    return json.loads(p.read_text())

def list_runs(project: str, limit: int = 30) -> list[dict]:
    d = _run_dir(project)
    if not d.exists():
        return []
    runs = []
    for f in sorted(d.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
        try:
            data = json.loads(f.read_text())
            runs.append({k: data.get(k) for k in
                         ["run_id", "workflow_name", "status", "started_at",
                          "finished_at", "current_step", "user_input"]})
        except Exception:
            pass
    return runs

# ── Public API ────────────────────────────────────────────────────────────────

async def start_run(workflow_name: str, user_input: str, project: str) -> str:
    """Create run JSON and start background execution. Returns run_id."""
    wf_path = (Path(settings.workspace_dir) / project / "workflows"
               / workflow_name / "workflow.yaml")
    if not wf_path.exists():
        raise FileNotFoundError(f"Workflow not found: {workflow_name}")

    wf = yaml.safe_load(wf_path.read_text())
    steps_spec = wf.get("steps", [])
    run_id = str(uuid.uuid4())[:8]

    run = {
        "run_id": run_id,
        "workflow_name": workflow_name,
        "project": project,
        "status": "running",
        "user_input": user_input,
        "max_iterations": int(wf.get("max_iterations", 3)),
        "started_at": _now(),
        "finished_at": None,
        "current_step": 0,
        "total_cost_usd": 0.0,
        "steps": [
            {
                "index": i,
                "name": s.get("name", f"step{i+1}"),
                "provider": s.get("provider", "claude"),
                "status": "pending",
                "output": "",
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "iteration": 0,
                "started_at": None,
                "finished_at": None,
            }
            for i, s in enumerate(steps_spec)
        ],
    }

    _save(project, run_id, run)
    asyncio.create_task(_execute(run_id, project, step_idx=0))
    return run_id


async def decide(run_id: str, project: str, action: str,
                 next_step: int | None = None) -> None:
    """Handle user decision: continue | retry | stop."""
    run = load_run(project, run_id)

    if action == "stop":
        run["status"] = "stopped"
        run["finished_at"] = _now()
        _save(project, run_id, run)
        return

    if action == "retry":
        idx = run["current_step"]
        step = run["steps"][idx]
        step["status"] = "pending"
        step["iteration"] = step.get("iteration", 0) + 1
        run["status"] = "running"
        _save(project, run_id, run)
        asyncio.create_task(_execute(run_id, project, step_idx=idx))
        return

    # action == "continue"
    idx = next_step if next_step is not None else run["current_step"] + 1
    if idx >= len(run["steps"]):
        run["status"] = "done"
        run["finished_at"] = _now()
        _save(project, run_id, run)
        return

    run["current_step"] = idx
    run["status"] = "running"
    _save(project, run_id, run)
    asyncio.create_task(_execute(run_id, project, step_idx=idx))


# ── Execution ─────────────────────────────────────────────────────────────────

async def _execute(run_id: str, project: str, step_idx: int) -> None:
    """Run one step, persist result, then auto-advance or pause for user."""
    try:
        run = load_run(project, run_id)
        wf_path = (Path(settings.workspace_dir) / project / "workflows"
                   / run["workflow_name"] / "workflow.yaml")
        steps_yaml = yaml.safe_load(wf_path.read_text()).get("steps", [])
        step_spec  = steps_yaml[step_idx] if step_idx < len(steps_yaml) else {}
        step       = run["steps"][step_idx]

        # Mark running
        step["status"]     = "running"
        step["started_at"] = _now()
        run["current_step"] = step_idx
        run["status"]       = "running"
        _save(project, run_id, run)

        # Build inputs
        system_prompt = _load_prompt(step_spec, project)
        user_msg      = _build_message(step_spec, run, step_idx)
        provider      = step_spec.get("provider", "claude")
        model         = step_spec.get("model") or None
        api_key       = get_key(provider)

        # Call LLM
        try:
            result = await _call_llm(provider, model, user_msg, system_prompt, api_key)
            step["status"]       = "done"
            step["output"]       = result["content"]
            step["input_tokens"] = result.get("input_tokens", 0)
            step["output_tokens"]= result.get("output_tokens", 0)
            step["cost_usd"]     = _calc_cost(
                provider, result.get("input_tokens", 0), result.get("output_tokens", 0)
            )
            run["total_cost_usd"] = sum(s.get("cost_usd", 0) for s in run["steps"])
        except Exception as exc:
            step["status"] = "error"
            step["output"] = str(exc)

        step["finished_at"] = _now()
        _save(project, run_id, run)

        if step["status"] == "error":
            run["status"] = "waiting"
            _save(project, run_id, run)
            return

        # Score-based auto-continue / auto-retry
        score_field = step_spec.get("score_field")
        score_min   = step_spec.get("score_min")
        if score_field and score_min is not None:
            score    = _extract_score(step["output"], str(score_field))
            max_iter = run.get("max_iterations", 3)

            if score is not None and score >= float(score_min):
                # Score threshold met → auto-advance
                await _advance(run_id, project, step_idx)
                return

            if score is not None and step.get("iteration", 0) < max_iter - 1:
                # Score too low but still have retries → auto-retry
                step["iteration"] = step.get("iteration", 0) + 1
                step["status"]    = "pending"
                _save(project, run_id, run)
                asyncio.create_task(_execute(run_id, project, step_idx=step_idx))
                return

        # Pause — wait for user decision
        run["status"] = "waiting"
        _save(project, run_id, run)

    except Exception as exc:
        try:
            run = load_run(project, run_id)
            run["status"]    = "error"
            run["error"]     = str(exc)
            run["finished_at"] = _now()
            _save(project, run_id, run)
        except Exception:
            pass


async def _advance(run_id: str, project: str, current_idx: int) -> None:
    """Move to next step or mark run done."""
    run      = load_run(project, run_id)
    next_idx = current_idx + 1
    if next_idx >= len(run["steps"]):
        run["status"]     = "done"
        run["finished_at"] = _now()
        _save(project, run_id, run)
    else:
        run["current_step"] = next_idx
        run["status"]       = "running"
        _save(project, run_id, run)
        asyncio.create_task(_execute(run_id, project, step_idx=next_idx))


# ── LLM dispatch ──────────────────────────────────────────────────────────────

async def _call_llm(provider: str, model: str | None,
                    user_msg: str, system: str, api_key: str) -> dict:
    messages = [{"role": "user", "content": user_msg}]

    if provider == "claude":
        return await llm_clients.call_claude(
            messages, system=system, model=model, api_key=api_key
        )
    if provider == "deepseek":
        return await llm_clients.call_deepseek(
            messages, system=system, api_key=api_key
        )
    if provider == "grok":
        return await llm_clients.call_grok(
            messages, system=system, api_key=api_key
        )
    if provider == "gemini":
        return await llm_clients.call_gemini(
            user_msg, system=system, model=model, api_key=api_key
        )
    if provider == "openai":
        import openai as _oai
        key = api_key or settings.openai_api_key
        if not key:
            raise ValueError("No OpenAI API key configured")
        client = _oai.OpenAI(api_key=key)
        msgs = ([{"role": "system", "content": system}] if system else []) + messages
        r = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model=model or settings.openai_model, messages=msgs, max_tokens=4096
            )
        )
        usage = r.usage
        return {
            "content": r.choices[0].message.content or "",
            "input_tokens":  usage.prompt_tokens     if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
        }
    raise ValueError(f"Unknown provider: {provider}")


# ── Prompt / message builders ─────────────────────────────────────────────────

def _load_prompt(step_spec: dict, project: str) -> str:
    """Load system prompt from file or inline spec."""
    prompt_path = step_spec.get("prompt", "")
    if not prompt_path:
        return step_spec.get("role_prompt", "")

    # Try relative to workspace/{project}/prompts/
    for base in [
        Path(settings.workspace_dir) / project / "prompts" / prompt_path,
        Path(settings.workspace_dir) / project / prompt_path,
    ]:
        if base.exists():
            return base.read_text()

    return f"You are a {step_spec.get('name', 'agent')} agent."


def _build_message(step_spec: dict, run: dict, step_idx: int) -> str:
    """Build user message: task + previous step outputs (if inject_context)."""
    parts: list[str] = []

    if run.get("user_input"):
        parts.append(f"# Task\n{run['user_input']}")

    inject = step_spec.get("inject_context", True)
    if inject and step_idx > 0:
        prev = [
            f"## {s['name']} output\n{s['output']}"
            for s in run["steps"][:step_idx]
            if s.get("output")
        ]
        if prev:
            parts.append("# Previous agent outputs\n\n" + "\n\n".join(prev))

    return "\n\n".join(parts) or "Please complete your assigned task."


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_score(text: str, field: str) -> float | None:
    """Extract numeric score from agent output text."""
    patterns = [
        rf'["\']?{re.escape(field)}["\']?\s*[=:]\s*(\d+(?:\.\d+)?)',
        rf'{re.escape(field)}\s+(?:is|=|:)\s+(\d+(?:\.\d+)?)',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    return None


def _calc_cost(provider: str, input_tok: int, output_tok: int) -> float:
    """Rough cost estimate — load from provider_costs.json when available."""
    # Default per-million rates
    rates = {
        "claude":   (3.0, 15.0),
        "openai":   (2.5, 10.0),
        "deepseek": (0.14, 0.28),
        "gemini":   (0.35, 1.05),
        "grok":     (5.0, 15.0),
    }
    try:
        cost_path = Path(settings.data_dir) / "provider_usage" / "provider_costs.json"
        if cost_path.exists():
            costs = json.loads(cost_path.read_text())
            if provider in costs:
                c = costs[provider]
                inp_rate = float(c.get("input_per_million", rates.get(provider, (3.0, 15.0))[0]))
                out_rate = float(c.get("output_per_million", rates.get(provider, (3.0, 15.0))[1]))
                return (input_tok * inp_rate + output_tok * out_rate) / 1_000_000
    except Exception:
        pass
    r = rates.get(provider, (3.0, 15.0))
    return (input_tok * r[0] + output_tok * r[1]) / 1_000_000
