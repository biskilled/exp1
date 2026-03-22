"""
routers/route_agents.py — REST API for agent and pipeline execution.

Endpoints:
  GET  /agents/roles                        list roles from DB
  GET  /agents/pipelines                    list available pipeline YAMLs
  POST /agents/run                          run a single agent (sync)
  POST /agents/run-pipeline                 run a full pipeline (sync)
  GET  /agents/runs/{run_id}                get cached run result
"""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.agent import Agent
from agents.orchestrator import AgentWorkflow, PipelineDef
from core.logger import get_logger

log = get_logger(__name__)
router = APIRouter()

# In-memory run cache (run_id → WorkflowResult summary dict)
# In production you'd persist this to the DB; this is sufficient for testing.
_run_cache: dict[str, dict] = {}


# ── Request / response models ─────────────────────────────────────────────────

class AgentRunRequest(BaseModel):
    role: str                          # DB role name e.g. "Product Manager"
    task: str
    handoff: dict | None = None        # structured input from a previous agent
    project: str = "aicli"
    max_tokens: int = 4096


class PipelineRunRequest(BaseModel):
    pipeline: str = "standard"        # name of YAML in workspace/_templates/pipelines/
    task: str
    project: str = "aicli"
    max_tokens: int = 4096


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/roles")
async def list_roles() -> list[dict]:
    """Return all active agent roles from the DB."""
    from core.database import db
    if not db.is_available():
        return []
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT name, description, provider, model, role_type,
                              react, max_iterations, tools
                       FROM mng_agent_roles
                       WHERE client_id=1 AND is_active=true
                       ORDER BY name""",
                )
                rows = cur.fetchall()
        return [
            {
                "name": r[0], "description": r[1], "provider": r[2],
                "model": r[3], "role_type": r[4], "react": r[5],
                "max_iterations": r[6], "tools": r[7] or [],
            }
            for r in rows
        ]
    except Exception as e:
        log.error("list_roles failed: %s", e)
        return []


@router.get("/pipelines")
async def list_pipelines() -> list[dict]:
    """List available pipeline YAML definitions."""
    names = PipelineDef.list_available()
    pipelines = []
    for name in names:
        try:
            pd = PipelineDef.load(name)
            pipelines.append({
                "name": pd.name,
                "version": pd.version,
                "description": pd.description.strip(),
                "stages": [{"key": s.key, "role": s.role} for s in pd.stages],
                "max_rejection_retries": pd.rejection_max_retries,
            })
        except Exception as e:
            pipelines.append({"name": name, "error": str(e)})
    return pipelines


@router.post("/run")
async def run_single_agent(req: AgentRunRequest) -> dict:
    """Run a single agent with optional handoff input.

    Returns full ReAct trace (Thought/Action/Observation steps) + structured output.
    """
    log.info("POST /agents/run — role='%s' project='%s'", req.role, req.project)
    try:
        agent = await Agent.from_role(req.role)
        result = await agent.run_pipeline(
            task=req.task,
            handoff=req.handoff,
            project=req.project,
            max_tokens=req.max_tokens,
        )
    except Exception as e:
        log.exception("Agent run failed for role='%s': %s", req.role, e)
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "role": req.role,
        "status": result.status,
        "structured_output": result.structured_output,
        "output": result.output,
        "steps": [
            {
                "step": s.step_num,
                "thought": s.thought,
                "action": s.action_name,
                "args": s.action_args,
                "observation": s.observation,
                "guard_fired": s.hallucination_guard_fired,
            }
            for s in result.steps
        ],
        "tool_calls_made": result.tool_calls_made,
        "cost_usd": result.cost_usd,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "error": result.error,
    }


@router.post("/run-pipeline")
async def run_pipeline(req: PipelineRunRequest) -> dict:
    """Run a full multi-agent pipeline.

    Stages execute sequentially; reviewer rejection loops back to developer.
    Returns a summary with per-stage details and ReAct traces.
    """
    log.info(
        "POST /agents/run-pipeline — pipeline='%s' project='%s' task='%s'",
        req.pipeline, req.project, req.task[:80],
    )
    try:
        workflow = AgentWorkflow(pipeline=req.pipeline, project=req.project)
        wf = await workflow.run(task=req.task)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        log.exception("Pipeline run failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    summary = wf.to_summary()

    # Attach full ReAct traces per stage
    summary["stage_details"] = {
        s.key: {
            "role": s.role,
            "status": s.result.status,
            "attempt": s.attempt,
            "structured_output": s.result.structured_output,
            "steps": [
                {
                    "step": step.step_num,
                    "thought": step.thought,
                    "action": step.action_name,
                    "observation": step.observation,
                    "guard_fired": step.hallucination_guard_fired,
                }
                for step in s.result.steps
            ],
        }
        for s in wf.stages
    }

    # Cache for GET /agents/runs/{run_id}
    _run_cache[wf.run_id] = summary

    return summary


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict:
    """Retrieve a cached pipeline run result by run_id."""
    if run_id not in _run_cache:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found in cache")
    return _run_cache[run_id]
