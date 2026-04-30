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
                    """SELECT name, description, provider, model,
                              react, max_iterations, tools
                       FROM mng_agent_roles
                       WHERE client_id=1 AND is_active=true
                       ORDER BY name""",
                )
                rows = cur.fetchall()
        return [
            {
                "name": r[0], "description": r[1], "provider": r[2],
                "model": r[3], "react": r[4],
                "max_iterations": r[5], "tools": r[6] or [],
            }
            for r in rows
        ]
    except Exception as e:
        log.error("list_roles failed: %s", e)
        return []


@router.get("/pipelines")
async def list_pipelines(mode: str | None = None) -> list[dict]:
    """List available pipeline YAML definitions, filtered to activated=TRUE.

    Optional ?mode=use_case|item further filters to pipelines with that mode flag set.
    """
    from core.database import db
    from fastapi import Query as _Q  # noqa: F401 (mode already in signature via Query default)

    # Fetch activated + mode flags from DB
    activated_names: set[str] | None = None
    mode_allowed: set[str] | None    = None
    if db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT name, activated,
                                  COALESCE(mode_use_case, TRUE),
                                  COALESCE(mode_item, TRUE)
                           FROM mng_agent_pipelines WHERE client_id=1"""
                    )
                    rows = cur.fetchall()
            if rows:
                activated_names = {r[0] for r in rows if bool(r[1])}
                if mode == "use_case":
                    mode_allowed = {r[0] for r in rows if bool(r[2])}
                elif mode == "item":
                    mode_allowed = {r[0] for r in rows if bool(r[3])}
        except Exception as e:
            log.warning("list_pipelines: could not query mng_agent_pipelines: %s", e)

    names = PipelineDef.list_available()
    pipelines = []
    for name in names:
        if activated_names is not None and name not in activated_names:
            continue
        if mode_allowed is not None and name not in mode_allowed:
            continue
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


# ── Async pipeline run endpoints ───────────────────────────────────────────────

import asyncio as _asyncio
import json as _json
from datetime import datetime as _datetime

from fastapi import Query

# Approval gate registry (run_id → event + result)
_approval_events:  dict[str, _asyncio.Event] = {}
_approval_results: dict[str, dict]           = {}


class AsyncPipelineRunRequest(BaseModel):
    pipeline:        str           = "standard"
    task:            str
    project:         str           = "aicli"
    input_files:     list          = []
    source:          str           = "direct"   # direct|use_case|item|chat
    linked_uc_id:    str | None    = None
    linked_item_id:  str | None    = None


def _append_stage_log(conn, stage_id: int, text: str, level: str = "info") -> None:
    """Append one log entry to pr_pipeline_run_stages.log_lines."""
    entry = _json.dumps([{"ts": _datetime.utcnow().isoformat(), "text": text, "level": level}])
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE pr_pipeline_run_stages SET log_lines = log_lines || %s::jsonb WHERE id=%s",
            (entry, stage_id),
        )
    conn.commit()


async def _run_pipeline_bg(
    run_id: str,
    pipeline_name: str,
    task: str,
    project: str,
    input_files: list,
    linked_uc_id: str | None = None,
    linked_item_id: str | None = None,
) -> None:
    """Background coroutine: execute a pipeline and persist stage results to DB."""
    from agents.orchestrator import AgentWorkflow, PipelineDef
    from core.database import db
    import time as _time

    log.info("Async pipeline run starting: run_id=%s pipeline=%s", run_id, pipeline_name)

    if not db.is_available():
        log.error("DB unavailable for async pipeline run %s", run_id)
        return

    project_id = db.get_or_create_project_id(project)

    # Load pipeline + DB overrides
    try:
        pipeline_def = PipelineDef.load(pipeline_name)
    except FileNotFoundError as e:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pr_pipeline_runs SET status='error', error=%s, finished_at=NOW() WHERE id=%s",
                    (str(e), run_id),
                )
            conn.commit()
        return

    # Load DB property overrides
    continue_on_failure = False
    require_approval_after = None
    max_rejection_retries = pipeline_def.rejection_max_retries
    save_memory = pipeline_def.save_memory
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT max_rejection_retries, continue_on_failure, save_memory,
                              require_approval_after
                       FROM mng_agent_pipelines WHERE client_id=1 AND name=%s""",
                    (pipeline_name,),
                )
                row = cur.fetchone()
        if row:
            max_rejection_retries   = row[0] if row[0] is not None else max_rejection_retries
            continue_on_failure     = bool(row[1])
            save_memory             = bool(row[2])
            require_approval_after  = row[3]
    except Exception as e:
        log.warning("Could not load pipeline DB overrides: %s", e)

    # Pre-create all stage rows as 'pending'
    stage_ids: dict[str, int] = {}
    try:
        with db.conn() as conn:
            for stage in pipeline_def.stages:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO pr_pipeline_run_stages
                               (run_id, stage_key, role_name, status)
                           VALUES (%s, %s, %s, 'pending')
                           RETURNING id""",
                        (run_id, stage.key, stage.role),
                    )
                    stage_ids[stage.key] = cur.fetchone()[0]
            conn.commit()
    except Exception as e:
        log.error("Could not pre-create stage rows: %s", e)

    # Execute stages
    from agents.agent import Agent, AgentResult
    t_run_start = _time.monotonic()
    handoff = None
    stage_order = [s.key for s in pipeline_def.stages]
    stage_map   = {s.key: s for s in pipeline_def.stages}
    total_cost  = 0.0
    total_in    = 0
    total_out   = 0
    rejection_retries = 0
    final_verdict = "error"
    final_error   = None
    approval_gate_done = False

    i = 0
    while i < len(stage_order):
        stage_def = stage_map[stage_order[i]]
        stage_id  = stage_ids.get(stage_def.key)
        attempt   = 1 + (rejection_retries if stage_order[i] == pipeline_def.rejection_loops_back_to else 0)
        t0        = _time.monotonic()

        # Mark stage running
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE pr_pipeline_run_stages SET status='running', attempt=%s, started_at=NOW() WHERE id=%s",
                        (attempt, stage_id),
                    )
                conn.commit()
        except Exception:
            pass

        # Approval gate BEFORE this stage (if required after previous)
        if require_approval_after and stage_order[i - 1] == require_approval_after if i > 0 else False:
            try:
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE pr_pipeline_runs SET status='waiting_approval' WHERE id=%s",
                            (run_id,),
                        )
                    conn.commit()
            except Exception:
                pass

            event = _asyncio.Event()
            _approval_events[run_id] = event
            log.info("Approval gate waiting for run_id=%s before stage=%s", run_id, stage_def.key)
            try:
                await _asyncio.wait_for(event.wait(), timeout=600)
            except _asyncio.TimeoutError:
                log.warning("Approval gate timed out for run_id=%s", run_id)
                final_error = "Approval gate timed out after 600s"
                break

            result_info = _approval_results.pop(run_id, {})
            if not result_info.get("approved", False):
                final_error = f"Run rejected at approval gate: {result_info.get('feedback', '')}"
                break

            # Restore running status
            try:
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE pr_pipeline_runs SET status='running' WHERE id=%s",
                            (run_id,),
                        )
                    conn.commit()
            except Exception:
                pass

        if stage_id:
            try:
                with db.conn() as conn:
                    _append_stage_log(conn, stage_id, f"[{stage_def.key}] Stage starting (role={stage_def.role}, attempt={attempt})")
            except Exception:
                pass

        # Run the stage
        stage_result = None
        stage_error  = None
        max_attempts = max(1, stage_def.retry)
        for retry_num in range(max_attempts):
            try:
                agent = await Agent.from_role(stage_def.role)
                if stage_def.temperature_override is not None:
                    agent.temperature = stage_def.temperature_override
                if stage_def.max_iterations_override is not None:
                    agent.max_iterations = stage_def.max_iterations_override

                coro = agent.run_pipeline(task=task, handoff=handoff, project=project)
                if stage_def.timeout_seconds:
                    import asyncio
                    stage_result = await asyncio.wait_for(coro, timeout=stage_def.timeout_seconds)
                else:
                    stage_result = await coro

                if stage_result.status not in ("error",):
                    break
                stage_error = stage_result.error or stage_result.status
            except Exception as e:
                stage_error = str(e)
                log.exception("Stage '%s' raised exception: %s", stage_def.key, e)
                from agents.agent import AgentResult
                stage_result = AgentResult(output=str(e), status="error", error=str(e))

        dur_s = _time.monotonic() - t0

        # Log stage result
        if stage_id:
            try:
                with db.conn() as conn:
                    out_preview = (stage_result.output or "")[:500] if stage_result else ""
                    _append_stage_log(
                        conn, stage_id,
                        f"[{stage_def.key}] Stage {'done' if not stage_error else 'error'}. "
                        f"Cost=${stage_result.cost_usd if stage_result else 0:.4f} "
                        f"Tokens={stage_result.input_tokens + stage_result.output_tokens if stage_result else 0}"
                        + (f"\nError: {stage_error}" if stage_error else ""),
                        level="error" if stage_error else "info",
                    )
            except Exception:
                pass

        # Persist stage result
        if stage_result:
            total_cost += stage_result.cost_usd
            total_in   += stage_result.input_tokens
            total_out  += stage_result.output_tokens
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    so = _json.dumps(stage_result.structured_output) if (stage_result and stage_result.structured_output) else None
                    cur.execute(
                        """UPDATE pr_pipeline_run_stages
                           SET status=%s, output_text=%s, structured_out=%s::jsonb,
                               input_tokens=%s, output_tokens=%s, cost_usd=%s,
                               duration_s=%s, finished_at=NOW(),
                               temperature_used=%s
                           WHERE id=%s""",
                        (
                            "error" if stage_error else "done",
                            (stage_result.output or "")[:8000] if stage_result else "",
                            so,
                            stage_result.input_tokens if stage_result else 0,
                            stage_result.output_tokens if stage_result else 0,
                            float(stage_result.cost_usd) if stage_result else 0,
                            round(dur_s, 2),
                            stage_def.temperature_override,
                            stage_id,
                        ),
                    )
                conn.commit()
        except Exception as e:
            log.warning("Could not persist stage result: %s", e)

        # Handle stage error
        if stage_error:
            if continue_on_failure:
                log.warning("Stage '%s' failed (continue_on_failure=True): %s", stage_def.key, stage_error)
                i += 1
                continue
            else:
                final_error = f"Stage '{stage_def.key}' failed: {stage_error}"
                break

        # Update handoff
        handoff = (stage_result.structured_output if stage_result else None) or {
            "role": stage_def.role,
            "raw_output": (stage_result.output or "")[:2000] if stage_result else "",
        }

        # Reviewer rejection handling
        if stage_order[i] == "reviewer":
            verdict = (handoff or {}).get("verdict", "approved")
            if verdict in ("rejected", "needs_changes"):
                if rejection_retries < max_rejection_retries:
                    rejection_retries += 1
                    handoff["reviewer_feedback"] = handoff.get("issues", [])
                    handoff["suggested_fixes"]   = handoff.get("suggested_fixes", [])
                    i = stage_order.index(pipeline_def.rejection_loops_back_to)
                    continue
                else:
                    final_verdict = "rejected"
                    break
            else:
                final_verdict = "approved"

        i += 1

    if final_verdict == "error" and not final_error:
        final_verdict = "done"

    # Map verdict to score
    score_map = {"approved": 5, "needs_changes": 3, "rejected": 1, "error": 0}
    auto_score = score_map.get(final_verdict, None)
    dur_total  = _time.monotonic() - t_run_start

    # Finalize run row
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE pr_pipeline_runs
                       SET status=%s, final_verdict=%s, score=%s,
                           total_cost_usd=%s, total_input_tokens=%s, total_output_tokens=%s,
                           duration_s=%s, error=%s, finished_at=NOW()
                       WHERE id=%s""",
                    (
                        "done" if not final_error else "error",
                        final_verdict,
                        auto_score,
                        round(total_cost, 8),
                        total_in,
                        total_out,
                        round(dur_total, 2),
                        final_error,
                        run_id,
                    ),
                )
            conn.commit()
    except Exception as e:
        log.error("Could not finalize pipeline run: %s", e)

    # Post-completion: save final output to documents folder
    try:
        from core.project_paths import documents_dir as _docs_dir
        from datetime import datetime as _dt2
        import re as _re
        docs = _docs_dir(project)
        docs.mkdir(parents=True, exist_ok=True)
        safe_name = _re.sub(r"[^a-zA-Z0-9_-]", "_", pipeline_name)
        ts_file = _dt2.utcnow().strftime("%Y%m%d_%H%M%S")
        doc_path = docs / f"{safe_name}_pipeline_{ts_file}.md"
        final_output = (stage_result.output if stage_result else "") or ""
        # Collect all stage outputs for a comprehensive document
        stage_sections: list[str] = []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT stage_key, role_name, status, output_text, structured_out,
                                  duration_s, cost_usd
                           FROM pr_pipeline_run_stages WHERE run_id=%s ORDER BY id""",
                        (run_id,),
                    )
                    for row in cur.fetchall():
                        s_key, s_role, s_status, s_out, s_struct, s_dur, s_cost = row
                        section = [f"## Stage: {s_key} ({s_role}) — {s_status}"]
                        if s_dur: section.append(f"_Duration: {s_dur:.1f}s | Cost: ${s_cost or 0:.4f}_")
                        if s_out: section.append(f"\n{s_out}")
                        if s_struct: section.append(f"\n**Structured output:**\n```json\n{_json.dumps(s_struct, indent=2)[:2000]}\n```")
                        stage_sections.append("\n".join(section))
        except Exception:
            stage_sections = [final_output]
        doc_content = "\n\n---\n\n".join([
            f"# Pipeline Run: {pipeline_name}",
            f"**Run ID:** {run_id}  \n**Verdict:** {final_verdict}  \n**Duration:** {dur_total:.1f}s  \n**Cost:** ${total_cost:.4f}",
        ] + stage_sections)
        doc_path.write_text(doc_content, encoding="utf-8")
        log.info("Pipeline output saved to %s", doc_path)
    except Exception as _de:
        log.warning("Could not save pipeline output document: %s", _de)

    # NOTE: linked item/UC summary is NOT updated automatically.
    # The user reviews the run in the panel and clicks "Apply" to write their summary.

    log.info(
        "Async pipeline run done: run_id=%s verdict=%s cost=$%.4f dur=%.1fs",
        run_id, final_verdict, total_cost, dur_total,
    )


def _update_item_after_run(
    project_id: int,
    pipeline_name: str,
    verdict: str,
    duration_s: float,
    stage_output: str,
    linked_item_id: str | None,
    linked_uc_id: str | None,
) -> None:
    """Append execution summary to linked work item/UC and update score."""
    from core.database import db
    from datetime import datetime as _dt

    if not db.is_available():
        return

    now = _dt.utcnow()
    ts_str = now.strftime("%d/%m/%y %H:%M")
    dur_min = round(duration_s / 60, 1) if duration_s else 0
    # 1-2 line summary from final stage output
    preview = (stage_output or "")[:200].replace("\n", " ").strip()
    summary_line = f"\n{ts_str}: EXEC PIPELINE {pipeline_name} ({dur_min} min): {preview}"

    score_map = {"approved": 5, "needs_changes": 3, "rejected": 1, "error": 0}
    score = score_map.get(verdict, None)

    def _do_update(item_id: str) -> None:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT summary FROM mem_work_items WHERE id=%s AND project_id=%s",
                    (item_id, project_id),
                )
                row = cur.fetchone()
                if not row:
                    return
                old_summary = row[0] or ""
                new_summary = old_summary + summary_line
                update_parts = ["summary = %s"]
                update_vals: list = [new_summary]
                if score is not None:
                    update_parts.append("score_status = %s")
                    update_vals.append(score)
                update_vals.append(item_id)
                cur.execute(
                    f"UPDATE mem_work_items SET {', '.join(update_parts)} WHERE id=%s",
                    update_vals,
                )
            conn.commit()

    if linked_item_id:
        _do_update(linked_item_id)
    if linked_uc_id and linked_uc_id != linked_item_id:
        _do_update(linked_uc_id)


@router.post("/pipeline-runs")
async def start_pipeline_run(req: AsyncPipelineRunRequest) -> dict:
    """Start a pipeline run asynchronously. Returns run_id immediately."""
    from core.database import db
    import uuid as _uuid

    if not db.is_available():
        raise HTTPException(503, "Database not available")

    run_id     = str(_uuid.uuid4())
    project_id = db.get_or_create_project_id(req.project)

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO pr_pipeline_runs
                           (id, project_id, pipeline_name, task, input_files, status,
                            source, linked_uc_id, linked_item_id)
                       VALUES (%s, %s, %s, %s, %s::jsonb, 'running', %s, %s, %s)""",
                    (run_id, project_id, req.pipeline, req.task,
                     _json.dumps(req.input_files),
                     req.source, req.linked_uc_id, req.linked_item_id),
                )
            conn.commit()
    except Exception as e:
        log.exception("Could not create pipeline run row: %s", e)
        raise HTTPException(500, f"Could not create run: {e}")

    # Fire off background task
    _asyncio.create_task(
        _run_pipeline_bg(
            run_id, req.pipeline, req.task, req.project, req.input_files,
            linked_uc_id=req.linked_uc_id, linked_item_id=req.linked_item_id,
        )
    )

    return {"run_id": run_id, "status": "running"}


@router.get("/pipeline-runs/{run_id}")
async def get_pipeline_run(run_id: str) -> dict:
    """Poll status and stage details for a pipeline run."""
    from core.database import db

    if not db.is_available():
        raise HTTPException(503, "Database not available")

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, pipeline_name, task, status, final_verdict, score,
                              total_cost_usd, total_input_tokens, total_output_tokens,
                              duration_s, error, started_at, finished_at,
                              linked_uc_id, linked_item_id
                       FROM pr_pipeline_runs WHERE id=%s""",
                    (run_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(404, "Run not found")

                cur.execute(
                    """SELECT id, stage_key, role_name, status, attempt,
                              output_text, log_lines, input_tokens, output_tokens,
                              cost_usd, duration_s, temperature_used, started_at, finished_at
                       FROM pr_pipeline_run_stages
                       WHERE run_id=%s ORDER BY id""",
                    (run_id,),
                )
                stage_rows = cur.fetchall()

        stages = [
            {
                "id":              sr[0],
                "stage_key":       sr[1],
                "role_name":       sr[2],
                "status":          sr[3],
                "attempt":         sr[4],
                "output_preview":  (sr[5] or "")[:1500],
                "log_lines":       sr[6] or [],
                "input_tokens":    sr[7],
                "output_tokens":   sr[8],
                "cost_usd":        float(sr[9] or 0),
                "duration_s":      sr[10],
                "temperature_used":sr[11],
                "started_at":      sr[12].isoformat() if sr[12] else None,
                "finished_at":     sr[13].isoformat() if sr[13] else None,
            }
            for sr in stage_rows
        ]

        return {
            "run_id":              str(row[0]),
            "pipeline_name":       row[1],
            "task":                row[2],
            "status":              row[3],
            "final_verdict":       row[4],
            "score":               row[5],
            "total_cost_usd":      float(row[6] or 0),
            "total_input_tokens":  row[7],
            "total_output_tokens": row[8],
            "duration_s":          row[9],
            "error":               row[10],
            "started_at":          row[11].isoformat() if row[11] else None,
            "finished_at":         row[12].isoformat() if row[12] else None,
            "linked_uc_id":        str(row[13]) if row[13] else None,
            "linked_item_id":      str(row[14]) if row[14] else None,
            "stages":              stages,
        }
    except HTTPException:
        raise
    except Exception as e:
        log.exception("get_pipeline_run failed: %s", e)
        raise HTTPException(500, str(e))


@router.post("/pipeline-runs/{run_id}/approve")
async def approve_pipeline_run(run_id: str, body: dict) -> dict:
    """Resolve an approval gate — body: {approved: bool, feedback?: str}."""
    approved = bool(body.get("approved", True))
    feedback = str(body.get("feedback", ""))
    _approval_results[run_id] = {"approved": approved, "feedback": feedback}
    event = _approval_events.pop(run_id, None)
    if event:
        event.set()
    return {"ok": True, "run_id": run_id, "approved": approved}


@router.post("/pipeline-runs/{run_id}/apply")
async def apply_pipeline_run(run_id: str, body: dict) -> dict:
    """Write user-reviewed summary + score to the linked UC/item.

    Body: { summary: str, score: int (1-5) }
    Only writes when the run has a linked_uc_id or linked_item_id.
    """
    from core.database import db
    from datetime import datetime as _dt

    if not db.is_available():
        raise HTTPException(503, "Database not available")

    summary_text = str(body.get("summary", "")).strip()
    score_val    = int(body.get("score", 0)) if body.get("score") is not None else None

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT linked_uc_id, linked_item_id, project_id, pipeline_name
                       FROM pr_pipeline_runs WHERE id=%s""",
                    (run_id,),
                )
                row = cur.fetchone()
        if not row:
            raise HTTPException(404, "Run not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

    linked_uc_id, linked_item_id, project_id, pipeline_name = row

    if not linked_uc_id and not linked_item_id:
        return {"ok": True, "message": "No linked item to update"}

    if not summary_text:
        raise HTTPException(400, "summary is required")

    now_str = _dt.utcnow().strftime("%d/%m/%y %H:%M")
    summary_line = f"\n{now_str}: {summary_text}"

    def _do_update(item_id: str) -> None:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT summary FROM mem_work_items WHERE id=%s AND project_id=%s",
                    (item_id, project_id),
                )
                existing = cur.fetchone()
                if not existing:
                    return
                new_summary = (existing[0] or "") + summary_line
                update_parts = ["summary = %s"]
                update_vals: list = [new_summary]
                if score_val is not None:
                    update_parts.append("score_status = %s")
                    update_vals.append(score_val)
                update_vals.append(item_id)
                cur.execute(
                    f"UPDATE mem_work_items SET {', '.join(update_parts)} WHERE id=%s",
                    update_vals,
                )
            conn.commit()

    updated: list[str] = []
    try:
        if linked_item_id:
            _do_update(str(linked_item_id))
            updated.append(f"item:{linked_item_id}")
        if linked_uc_id and str(linked_uc_id) != str(linked_item_id):
            _do_update(str(linked_uc_id))
            updated.append(f"uc:{linked_uc_id}")
    except Exception as e:
        log.exception("apply_pipeline_run: DB update failed: %s", e)
        raise HTTPException(500, str(e))

    log.info("apply_pipeline_run: run_id=%s updated=%s score=%s", run_id, updated, score_val)
    return {"ok": True, "updated": updated}


@router.get("/pipeline-runs")
async def list_pipeline_runs(
    project: str = Query("aicli"),
    pipeline_name: str | None = Query(None),
    limit: int = Query(20),
) -> dict:
    """List recent pipeline runs for a project."""
    from core.database import db

    if not db.is_available():
        return {"runs": []}

    try:
        project_id = db.get_or_create_project_id(project)
        with db.conn() as conn:
            with conn.cursor() as cur:
                if pipeline_name:
                    cur.execute(
                        """SELECT id, pipeline_name, task, status, final_verdict, score,
                                  total_cost_usd, total_input_tokens, total_output_tokens,
                                  duration_s, error, started_at, finished_at
                           FROM pr_pipeline_runs
                           WHERE project_id=%s AND pipeline_name=%s
                           ORDER BY started_at DESC LIMIT %s""",
                        (project_id, pipeline_name, min(limit, 200)),
                    )
                else:
                    cur.execute(
                        """SELECT id, pipeline_name, task, status, final_verdict, score,
                                  total_cost_usd, total_input_tokens, total_output_tokens,
                                  duration_s, error, started_at, finished_at
                           FROM pr_pipeline_runs
                           WHERE project_id=%s
                           ORDER BY started_at DESC LIMIT %s""",
                        (project_id, min(limit, 200)),
                    )
                rows = cur.fetchall()

        runs = [
            {
                "run_id":              str(r[0]),
                "pipeline_name":       r[1],
                "task":                (r[2] or "")[:120],
                "status":              r[3],
                "final_verdict":       r[4],
                "score":               r[5],
                "total_cost_usd":      float(r[6] or 0),
                "total_input_tokens":  r[7],
                "total_output_tokens": r[8],
                "duration_s":          r[9],
                "error":               r[10],
                "started_at":          r[11].isoformat() if r[11] else None,
                "finished_at":         r[12].isoformat() if r[12] else None,
            }
            for r in rows
        ]
        return {"runs": runs}
    except Exception as e:
        log.exception("list_pipeline_runs failed: %s", e)
        return {"runs": []}


class ScorePatch(BaseModel):
    score: int


@router.patch("/pipeline-runs/{run_id}/score")
async def score_pipeline_run(run_id: str, body: ScorePatch) -> dict:
    """Set the user-adjusted score (0-5) for a pipeline run."""
    from core.database import db

    if not db.is_available():
        raise HTTPException(503, "Database not available")

    score = max(0, min(5, body.score))
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pr_pipeline_runs SET score=%s WHERE id=%s RETURNING id",
                    (score, run_id),
                )
                if not cur.fetchone():
                    raise HTTPException(404, "Run not found")
            conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))

    return {"ok": True, "run_id": run_id, "score": score}
