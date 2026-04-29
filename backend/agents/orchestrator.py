"""
agents/orchestrator.py — Pipeline executor for YAML-defined multi-agent workflows.

Loads pipeline definitions from workspace/_templates/pipelines/*.yaml and runs
agents in sequence, passing each agent's structured JSON output as the next
agent's handoff input.

Key features:
  - YAML pipeline definitions (no code changes needed to add a pipeline)
  - Reviewer rejection loops back to Developer (configurable, with max retries)
  - Full ReAct enforcement via Agent.run_pipeline()
  - Workflow memory: saves full result to pr_interactions + optional CLAUDE.md refresh
  - Logging: every stage and rejection logged to app.log

Usage:
    workflow = AgentWorkflow(pipeline="standard", project="myproject")
    result = await workflow.run("Add input validation to the login form")
    print(result.final_verdict)     # "approved" | "rejected" | "error"
    print(result.total_cost_usd)
    for stage, agent_result in result.results.items():
        for step in agent_result.steps:
            print(f"  [{step.step_num}] {step.thought[:80]}")
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from agents.agent import Agent, AgentResult
from core.config import settings
from core.logger import get_logger

log = get_logger(__name__)

_PIPELINES_DIR = (
    Path(settings.workspace_dir).parent / "workspace" / "_templates" / "pipelines"
)
# Resolve to absolute path
_PIPELINES_DIR = Path(settings.workspace_dir) / ".." / "workspace" / "_templates" / "pipelines"


def _pipelines_dir() -> Path:
    """Return the pipelines template directory, resolving workspace_dir."""
    ws = Path(settings.workspace_dir)
    # workspace_dir = engine_root/workspace, so templates = engine_root/workspace/_templates/pipelines
    # but the YAML files might be under workspace/ directly
    candidates = [
        ws / "_templates" / "pipelines",
        ws.parent / "workspace" / "_templates" / "pipelines",
    ]
    for c in candidates:
        if c.exists():
            return c
    # return first candidate even if it doesn't exist (will be created)
    return candidates[0]


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class StageResult:
    key: str
    role: str
    result: AgentResult
    attempt: int = 1          # which attempt (1 = first, 2+ = after rejection retry)
    duration_s: float = 0.0


@dataclass
class WorkflowResult:
    task: str
    pipeline: str
    project: str
    run_id: str
    stages: list[StageResult] = field(default_factory=list)
    final_verdict: str = "unknown"    # "approved" | "rejected" | "error"
    error: str | None = None
    total_cost_usd: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_steps: int = 0
    duration_s: float = 0.0

    @property
    def results(self) -> dict[str, AgentResult]:
        """Map stage key → last AgentResult for that stage."""
        out: dict[str, AgentResult] = {}
        for s in self.stages:
            out[s.key] = s.result
        return out

    @property
    def last_handoff(self) -> dict | None:
        """Structured output from the last completed stage."""
        for s in reversed(self.stages):
            if s.result.structured_output:
                return s.result.structured_output
        return None

    def to_summary(self) -> dict:
        return {
            "run_id": self.run_id,
            "pipeline": self.pipeline,
            "project": self.project,
            "task": self.task[:200],
            "final_verdict": self.final_verdict,
            "total_stages": len(self.stages),
            "total_steps": self.total_steps,
            "total_cost_usd": round(self.total_cost_usd, 5),
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "duration_s": round(self.duration_s, 2),
            "error": self.error,
            "stages": [
                {
                    "key": s.key,
                    "role": s.role,
                    "status": s.result.status,
                    "attempt": s.attempt,
                    "steps": len(s.result.steps),
                    "cost_usd": round(s.result.cost_usd, 5),
                    "duration_s": round(s.duration_s, 2),
                }
                for s in self.stages
            ],
        }


# ── Pipeline definition loader ────────────────────────────────────────────────

@dataclass
class PipelineStage:
    key: str
    role: str
    description: str = ""


@dataclass
class PipelineDef:
    name: str
    version: str
    description: str
    stages: list[PipelineStage]
    rejection_loops_back_to: str = "developer"
    rejection_max_retries: int = 2
    save_memory: bool = True

    @classmethod
    def load(cls, pipeline_name: str) -> "PipelineDef":
        """Load a pipeline definition from workspace/_templates/pipelines/{name}.yaml"""
        pdir = _pipelines_dir()
        yaml_path = pdir / f"pl_{pipeline_name}.yaml"
        if not yaml_path.exists():
            raise FileNotFoundError(
                f"Pipeline '{pipeline_name}' not found at {yaml_path}. "
                f"Available: {[f.stem[3:] for f in pdir.glob('pl_*.yaml')]}"
            )
        raw = yaml.safe_load(yaml_path.read_text())
        stages = [
            PipelineStage(
                key=s["key"],
                role=s["role"],
                description=s.get("description", ""),
            )
            for s in raw.get("stages", [])
        ]
        rejection = raw.get("on_rejection", {})
        completion = raw.get("on_completion", {})
        return cls(
            name=raw.get("name", pipeline_name),
            version=raw.get("version", "1.0"),
            description=raw.get("description", ""),
            stages=stages,
            rejection_loops_back_to=rejection.get("loops_back_to", "developer"),
            rejection_max_retries=int(rejection.get("max_retries", 2)),
            save_memory=bool(completion.get("save_memory", True)),
        )

    @staticmethod
    def list_available() -> list[str]:
        """Return names of all available pipeline YAMLs."""
        pdir = _pipelines_dir()
        if not pdir.exists():
            return []
        return sorted(f.stem[3:] for f in pdir.glob("pl_*.yaml"))


# ── Orchestrator ──────────────────────────────────────────────────────────────

class AgentWorkflow:
    """Pipeline executor: loads YAML definition, runs agents in sequence with handoff passing."""

    def __init__(
        self,
        pipeline: str = "standard",
        project: str | None = None,
    ) -> None:
        self.pipeline_def = PipelineDef.load(pipeline)
        self.project = project or settings.active_project

    async def run(self, task: str, api_key: str | None = None) -> WorkflowResult:
        """Execute the pipeline for the given task.

        Returns a WorkflowResult with per-stage details, cost, and final verdict.
        """
        run_id = str(uuid.uuid4())
        t_start = time.monotonic()

        log.info(
            "Pipeline '%s' starting run_id=%s project=%s task=%s",
            self.pipeline_def.name, run_id, self.project, task[:100],
        )

        wf = WorkflowResult(
            task=task,
            pipeline=self.pipeline_def.name,
            project=self.project,
            run_id=run_id,
        )

        handoff: dict | None = None
        stage_map = {s.key: s for s in self.pipeline_def.stages}
        stage_order = [s.key for s in self.pipeline_def.stages]

        # ── Sequential stage execution ─────────────────────────────────────────
        i = 0
        rejection_retries = 0

        while i < len(stage_order):
            stage_def = stage_map[stage_order[i]]
            attempt = 1 + (rejection_retries if stage_order[i] == self.pipeline_def.rejection_loops_back_to else 0)

            log.info(
                "Pipeline '%s' → stage [%d/%d] '%s' (role='%s', attempt=%d)",
                self.pipeline_def.name, i + 1, len(stage_order),
                stage_def.key, stage_def.role, attempt,
            )

            stage_result = await self._run_stage(
                stage_def=stage_def,
                task=task,
                handoff=handoff,
                attempt=attempt,
                api_key=api_key,
            )
            wf.stages.append(stage_result)
            wf.total_cost_usd      += stage_result.result.cost_usd
            wf.total_input_tokens  += stage_result.result.input_tokens
            wf.total_output_tokens += stage_result.result.output_tokens
            wf.total_steps         += len(stage_result.result.steps)

            # Check for agent-level errors
            if stage_result.result.status in ("loop_detected", "max_steps_reached", "error"):
                wf.final_verdict = "error"
                wf.error = (
                    f"Stage '{stage_def.key}' failed with status={stage_result.result.status}: "
                    + (stage_result.result.error or "")
                )
                log.error("Pipeline '%s' aborted: %s", self.pipeline_def.name, wf.error)
                break

            # Update handoff for next stage
            handoff = stage_result.result.structured_output or {
                "role": stage_def.role,
                "raw_output": stage_result.result.output[:2000],
            }

            # ── Reviewer rejection handling ────────────────────────────────────
            if stage_order[i] == "reviewer":
                verdict = (handoff or {}).get("verdict", "approved")
                if verdict in ("rejected", "needs_changes"):
                    if rejection_retries < self.pipeline_def.rejection_max_retries:
                        rejection_retries += 1
                        log.warning(
                            "Pipeline '%s' reviewer verdict='%s' — looping back to '%s' (retry %d/%d)",
                            self.pipeline_def.name, verdict,
                            self.pipeline_def.rejection_loops_back_to,
                            rejection_retries, self.pipeline_def.rejection_max_retries,
                        )
                        # Inject reviewer feedback into handoff for developer
                        handoff["reviewer_feedback"] = handoff.get("issues", [])
                        handoff["suggested_fixes"]   = handoff.get("suggested_fixes", [])
                        # Jump back to developer stage
                        i = stage_order.index(self.pipeline_def.rejection_loops_back_to)
                        continue
                    else:
                        wf.final_verdict = "rejected"
                        log.warning(
                            "Pipeline '%s' max rejection retries reached — verdict=rejected",
                            self.pipeline_def.name,
                        )
                        break
                else:
                    wf.final_verdict = "approved"
                    log.info("Pipeline '%s' approved!", self.pipeline_def.name)

            i += 1

        if wf.final_verdict == "unknown":
            wf.final_verdict = "done"

        wf.duration_s = time.monotonic() - t_start

        # ── Persist workflow to memory ─────────────────────────────────────────
        if self.pipeline_def.save_memory:
            await self._save_workflow_memory(wf)

        log.info(
            "Pipeline '%s' finished: verdict=%s cost=$%.4f steps=%d duration=%.1fs",
            self.pipeline_def.name, wf.final_verdict,
            wf.total_cost_usd, wf.total_steps, wf.duration_s,
        )
        return wf

    async def _run_stage(
        self,
        stage_def: PipelineStage,
        task: str,
        handoff: dict | None,
        attempt: int,
        api_key: str | None,
    ) -> StageResult:
        """Load the agent for this stage and run it with run_pipeline()."""
        t0 = time.monotonic()
        try:
            agent = await Agent.from_role(stage_def.role)
            result = await agent.run_pipeline(
                task=task,
                handoff=handoff,
                project=self.project,
                api_key=api_key,
            )
        except Exception as e:
            log.exception("Stage '%s' raised exception: %s", stage_def.key, e)
            result = AgentResult(
                output=str(e),
                status="error",
                error=str(e),
            )
        return StageResult(
            key=stage_def.key,
            role=stage_def.role,
            result=result,
            attempt=attempt,
            duration_s=time.monotonic() - t0,
        )

    async def _save_workflow_memory(self, wf: WorkflowResult) -> None:
        """Persist the full workflow summary to mem_mrr_prompts."""
        from core.database import db
        if not db.is_available():
            return
        try:
            summary = wf.to_summary()
            metadata = json.dumps({
                "run_id": wf.run_id,
                "pipeline": wf.pipeline,
                "workflow": True,
                "tags": ["pipeline", wf.pipeline, wf.final_verdict],
            })
            content = json.dumps(summary)
            project_id = db.get_or_create_project_id(wf.project)
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO mem_mrr_prompts
                           (project_id, source, session_id, content, metadata, created_at)
                           VALUES (%s, %s, %s, %s, %s::jsonb, NOW())""",
                        (project_id, f"pipeline:{wf.pipeline}", wf.run_id, content, metadata),
                    )
                conn.commit()
            log.debug("Workflow '%s' saved to mem_mrr_prompts (run_id=%s)", wf.pipeline, wf.run_id)
        except Exception as e:
            log.warning("Failed to save workflow memory: %s", e)
