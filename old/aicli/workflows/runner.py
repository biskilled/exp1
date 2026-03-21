"""
WorkflowRunner — YAML-based multi-step workflow executor.

Replaces workflows/engine.py.

Features:
- Loads workflow.yaml from workspace/<project>/workflows/<name>/
- File injection via core/context_builder.py
- Per-step retry and provider fallback
- Cost tracking via core/cost_tracker.py
- Pre/post git actions (git_pull, git_commit, git_push)
- Run log saved to workspace/<project>/runs/<ts>_<workflow>.json
- Loop-back on fail (on_fail: {loop_to: step_name})
- stop_condition: score threshold from structured JSON output
"""

import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console

from core.context_builder import ContextBuilder
from core.cost_tracker import CostTracker

console = Console()


# ------------------------------------------------------------------
# Provider registry — instantiated lazily from config
# ------------------------------------------------------------------

def _make_provider(provider_name: str, config: dict, logger=None):
    """Instantiate a provider from config dict."""
    prov_cfg = config.get("providers", {}).get(provider_name, {})

    if provider_name == "claude":
        from providers.claude_agent import ClaudeAgent
        return ClaudeAgent(config=config, logger=logger)

    elif provider_name == "openai":
        from providers.openai_agent import OpenAIAgent
        return OpenAIAgent(
            model=prov_cfg.get("model", "gpt-4.1"),
            api_key_env=prov_cfg.get("api_key_env", "OPENAI_API_KEY"),
            logger=logger,
        )

    elif provider_name == "deepseek":
        from providers.deepseek_agent import DeepSeekAgent
        return DeepSeekAgent(
            model=prov_cfg.get("model", "deepseek-chat"),
            api_key_env=prov_cfg.get("api_key_env", "DEEPSEEK_API_KEY"),
            logger=logger,
        )

    elif provider_name == "gemini":
        from providers.gemini_agent import GeminiAgent
        return GeminiAgent(
            model=prov_cfg.get("model", "gemini-2.0-flash"),
            api_key_env=prov_cfg.get("api_key_env", "GEMINI_API_KEY"),
            logger=logger,
        )

    elif provider_name == "grok":
        from providers.grok_agent import GrokAgent
        return GrokAgent(
            model=prov_cfg.get("model", "grok-3"),
            api_key_env=prov_cfg.get("api_key_env", "XAI_API_KEY"),
            logger=logger,
        )

    else:
        raise ValueError(f"Unknown provider: {provider_name!r}")


# ------------------------------------------------------------------
# Git helpers
# ------------------------------------------------------------------

def _git_action(action: str, cwd: Path) -> None:
    cmds = {
        "git_pull":   ["git", "pull", "--rebase"],
        "git_commit": ["git", "commit", "-am", f"chore: workflow auto-commit [{datetime.now(timezone.utc):%Y-%m-%d %H:%M}]"],
        "git_push":   ["git", "push"],
        "git_add":    ["git", "add", "."],
    }
    cmd = cmds.get(action)
    if not cmd:
        console.print(f"[yellow]Unknown git action: {action}[/yellow]")
        return
    try:
        subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        console.print(f"[dim]  git action: {action} ✓[/dim]")
    except subprocess.CalledProcessError as e:
        console.print(f"[yellow]  git action {action} failed: {e.stderr.strip()}[/yellow]")


# ------------------------------------------------------------------
# Output format extraction
# ------------------------------------------------------------------

def _extract_json(text: str) -> dict:
    """Try to parse JSON from LLM output (may be wrapped in code fence)."""
    # Try code fence first
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Try bare JSON
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    return {}


# ------------------------------------------------------------------
# WorkflowRunner
# ------------------------------------------------------------------

class WorkflowRunner:

    def __init__(
        self,
        config: dict,
        workspace_root: Path,
        project_name: str,
        logger=None,
    ):
        self.config = config
        self.workspace_root = workspace_root
        self.project_dir = workspace_root / project_name
        self.logger = logger
        self._providers: dict = {}

    def _get_provider(self, name: str):
        if name not in self._providers:
            # Check fallback config
            fallback_name = (
                self.config.get("providers", {})
                .get(name, {})
                .get("fallback")
            )
            provider = _make_provider(name, self.config, self.logger)
            if fallback_name:
                try:
                    fallback = _make_provider(fallback_name, self.config, self.logger)
                    provider.fallback = fallback
                except Exception:
                    pass
            self._providers[name] = provider
        return self._providers[name]

    def run(self, workflow_name: str, user_input: str = "") -> str:
        """
        Run a named workflow from the project workspace.
        Returns the final step output.
        """
        wf_dir = self.project_dir / "workflows" / workflow_name
        wf_yaml = wf_dir / "workflow.yaml"

        if not wf_yaml.exists():
            raise FileNotFoundError(f"Workflow not found: {wf_yaml}")

        with open(wf_yaml, encoding="utf-8") as f:
            wf: dict = yaml.safe_load(f)

        console.print(f"\n[bold cyan]Workflow: {wf.get('name', workflow_name)}[/bold cyan]")
        if wf.get("description"):
            console.print(f"[dim]{wf['description']}[/dim]\n")

        # Load project config for code_dir
        project_yaml = self.project_dir / "project.yaml"
        code_dir: Optional[Path] = None
        if project_yaml.exists():
            with open(project_yaml, encoding="utf-8") as f:
                proj_cfg = yaml.safe_load(f) or {}
            cd = proj_cfg.get("code_dir")
            if cd:
                code_dir = (self.project_dir / cd).resolve()

        context_builder = ContextBuilder(
            project_dir=self.project_dir,
            code_dir=code_dir,
        )

        tracker = CostTracker(
            workflow_name=workflow_name,
            project_dir=self.project_dir,
        )

        # Pre-actions
        if wf.get("pre_actions") and code_dir and code_dir.exists():
            for action in wf["pre_actions"]:
                _git_action(action, code_dir)

        steps = wf.get("steps", [])
        max_iterations = wf.get("max_iterations", 1)
        stop_condition = wf.get("stop_condition", {})

        previous_output = user_input
        step_outputs: dict[str, str] = {}
        iteration = 0
        final_output = ""

        # Build step index for loop-back
        step_names = [s.get("name", f"step_{i}") for i, s in enumerate(steps)]

        step_idx = 0
        while step_idx < len(steps):
            step = steps[step_idx]
            step_name = step.get("name", f"step_{step_idx}")

            console.print(
                f"[bold]  Step: {step_name}[/bold] "
                f"[dim]provider={step.get('provider', 'claude')}[/dim]"
            )

            # Build context
            context_prefix = context_builder.build(
                inject_files=step.get("inject_files"),
                inject_context=step.get("inject_context"),
            )

            # Build prompt
            prompt_rel = step.get("prompt", "")
            prompt_text = ""
            if prompt_rel:
                prompt_path = wf_dir / prompt_rel
                if not prompt_path.exists():
                    prompt_path = self.project_dir / prompt_rel
                if prompt_path.exists():
                    prompt_text = prompt_path.read_text(encoding="utf-8")
                else:
                    console.print(f"  [yellow]Prompt file not found: {prompt_rel}[/yellow]")

            # Assemble full prompt
            parts: list[str] = []
            if context_prefix:
                parts.append(context_prefix)
            if step.get("inject_input") and user_input:
                parts.append(f"--- USER INPUT ---\n{user_input}")
            if step.get("inject_previous_output") and previous_output:
                parts.append(f"--- PREVIOUS OUTPUT ---\n{previous_output}")
            if prompt_text:
                parts.append(prompt_text)

            full_prompt = "\n\n".join(parts) if parts else previous_output

            # System role
            role_text = ""
            role_rel = step.get("role", "")
            if role_rel:
                role_path = self.project_dir / role_rel
                if role_path.exists():
                    role_text = role_path.read_text(encoding="utf-8")

            # Call provider
            provider_name = step.get("provider", "claude")
            prov_cfg = (
                wf.get("provider_config", {}).get(provider_name, {})
                or self.config.get("providers", {}).get(provider_name, {})
            )
            max_retries = prov_cfg.get("max_retries", 3)

            try:
                agent = self._get_provider(provider_name)
                agent.max_retries = max_retries

                output = ""
                if provider_name == "claude":
                    # Claude uses its own streaming send()
                    output = agent.send(full_prompt)
                else:
                    # Other providers: stream to stdout then collect
                    chunks: list[str] = []
                    for chunk in agent.stream(full_prompt, system=role_text):
                        print(chunk, end="", flush=True)
                        chunks.append(chunk)
                    print()
                    output = "".join(chunks)

            except Exception as e:
                console.print(f"  [red]Provider error: {e}[/red]")
                output = f"[error: {e}]"

            # Token tracking (rough estimate if not available from provider)
            input_tokens = agent.count_tokens(full_prompt) if hasattr(agent, "count_tokens") else len(full_prompt) // 4
            output_tokens = agent.count_tokens(output) if hasattr(agent, "count_tokens") else len(output) // 4
            model = getattr(agent, "model", provider_name)

            # Extract structured output if requested
            structured: dict = {}
            score: Optional[float] = None
            if step.get("output_format") == "json":
                structured = _extract_json(output)
                score = structured.get("score")
                produces = step.get("produces", {})
                for key in produces:
                    if key in structured:
                        console.print(f"  [dim]{key}: {structured[key]}[/dim]")

            tracker.record(
                step_name=step_name,
                provider=provider_name,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                output_preview=output[:200],
                score=score,
            )

            step_outputs[step_name] = output
            previous_output = output
            final_output = output

            # --- Stop condition check ---
            if stop_condition and score is not None:
                field = stop_condition.get("field", "score")
                threshold = stop_condition.get("threshold", 8)
                val = structured.get(field, score)
                if val is not None and float(val) >= float(threshold):
                    console.print(f"  [green]Stop condition met ({field}={val} >= {threshold})[/green]")
                    break

            # --- on_pass / on_fail routing ---
            on_fail = step.get("on_fail", {})
            on_pass = step.get("on_pass", {})

            if structured and "approved" in structured:
                approved = bool(structured.get("approved"))
                if not approved and on_fail.get("loop_to"):
                    target = on_fail["loop_to"]
                    if target in step_names:
                        iteration += 1
                        if iteration >= max_iterations:
                            console.print(f"  [yellow]Max iterations ({max_iterations}) reached.[/yellow]")
                            break
                        console.print(f"  [yellow]Not approved — looping to: {target}[/yellow]")
                        step_idx = step_names.index(target)
                        continue
                elif approved and on_pass.get("next") == "end":
                    console.print(f"  [green]Approved — workflow complete.[/green]")
                    break

            step_idx += 1

        # Print cost table
        tracker.print_table(console)
        tracker.save()

        # Save run log
        self._save_run_log(workflow_name, steps, tracker, user_input, final_output)

        # Post-actions
        if wf.get("post_actions") and code_dir and code_dir.exists():
            for action in wf["post_actions"]:
                if action == "git_commit":
                    _git_action("git_add", code_dir)
                _git_action(action, code_dir)

        return final_output

    def list_workflows(self) -> list[str]:
        """Return workflow names found in this project's workspace."""
        wf_base = self.project_dir / "workflows"
        if not wf_base.exists():
            return []
        return [
            d.name
            for d in sorted(wf_base.iterdir())
            if d.is_dir() and (d / "workflow.yaml").exists()
        ]

    def _save_run_log(
        self,
        workflow_name: str,
        steps: list[dict],
        tracker: CostTracker,
        user_input: str,
        final_output: str,
    ) -> None:
        runs_dir = self.project_dir / "runs"
        runs_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        log_path = runs_dir / f"{ts}_{workflow_name}.json"

        duration = (datetime.now(timezone.utc) - tracker.started_at).total_seconds()
        log = {
            "workflow": workflow_name,
            "started_at": tracker.started_at.isoformat(),
            "duration_secs": round(duration, 1),
            "user_input": user_input[:500],
            "steps": tracker.steps,
            "total_cost_usd": round(tracker.total_cost, 6),
            "final_output_preview": final_output[:500],
        }

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2)
        console.print(f"[dim]Run log saved: {log_path}[/dim]")
