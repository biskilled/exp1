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


# ── Task enrichment ───────────────────────────────────────────────────────────

def _enrich_task_from_db(
    project_id: int,
    original_task: str,
    linked_uc_id: str | None,
    linked_item_id: str | None,
) -> str:
    """Append full UC/item context from DB to the pipeline task string.

    Adds: UC summary, acceptance criteria, implementation plan, all children
    (open + done), per-item scores, related activity counts, and clear
    instructions so each agent knows what to produce.
    """
    from core.database import db
    if not db.is_available() or (not linked_uc_id and not linked_item_id):
        return original_task

    sections: list[str] = [original_task.strip()]

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:

                uc_row = None  # set if linked_uc_id branch executes
                ir     = None  # set if linked_item_id branch executes

                if linked_uc_id:
                    # ── Full UC data ─────────────────────────────────────────
                    cur.execute(
                        """SELECT name, wi_id, summary, acceptance_criteria,
                                  implementation_plan, score_status, user_status
                           FROM mem_work_items WHERE id=%s""",
                        (str(linked_uc_id),),
                    )
                    uc_row = cur.fetchone()
                    if uc_row:
                        uc_name, uc_wi_id, uc_sum, uc_ac, uc_impl, uc_score, uc_status = uc_row
                        uc_sec = [
                            "\n## USE CASE",
                            f"**{uc_name}** [{uc_wi_id}]  "
                            f"status={uc_status or 'open'}  score={uc_score or 0}/5",
                        ]
                        if uc_sum:
                            uc_sec.append(f"\n**Summary:**\n{uc_sum[:800]}")
                        if uc_ac:
                            uc_sec.append(f"\n**Acceptance Criteria:**\n{uc_ac[:600]}")
                        if uc_impl:
                            uc_sec.append(f"\n**Implementation Plan:**\n{uc_impl[:600]}")
                        sections.append("\n".join(uc_sec))

                    # ── All children ─────────────────────────────────────────
                    cur.execute(
                        """SELECT name, wi_id, wi_type, user_status, score_status,
                                  summary, acceptance_criteria
                           FROM mem_work_items
                           WHERE wi_parent_id=%s AND deleted_at IS NULL
                           ORDER BY COALESCE(score_status,0) DESC, created_at""",
                        (str(linked_uc_id),),
                    )
                    children = cur.fetchall()
                    if children:
                        open_ch  = [c for c in children if (c[3] or "open") not in ("done",)]
                        done_ch  = [c for c in children if (c[3] or "open") in ("done",)]
                        item_sec = [
                            f"\n## WORK ITEMS  "
                            f"({len(children)} total · {len(open_ch)} open · {len(done_ch)} done)",
                        ]
                        if open_ch:
                            item_sec.append("\n### Open Items (must be implemented):")
                            for c in open_ch:
                                n, wid, wtype, st, sc, sm, ac = c
                                item_sec.append(
                                    f"\n**[{(wtype or 'task').upper()}] "
                                    f"{wid or 'pending'} — {n}**\n"
                                    f"status={st or 'open'}  current_score={sc or 0}/5"
                                    + (f"\nSummary: {sm[:300]}" if sm else "")
                                    + (f"\nAcceptance Criteria: {ac[:300]}" if ac else "")
                                )
                        if done_ch:
                            item_sec.append(f"\n### Completed Items ({len(done_ch)}):")
                            for c in done_ch[:15]:
                                item_sec.append(f"- ✓ [{c[2]}] {c[1] or ''} {c[0]}")
                        sections.append("\n".join(item_sec))

                elif linked_item_id:
                    # ── Single item ──────────────────────────────────────────
                    cur.execute(
                        """SELECT w.name, w.wi_id, w.wi_type, w.user_status,
                                  w.score_status, w.summary, w.acceptance_criteria,
                                  w.implementation_plan, w.due_date,
                                  p.name, p.wi_id, p.summary
                           FROM mem_work_items w
                           LEFT JOIN mem_work_items p ON p.id = w.wi_parent_id
                           WHERE w.id=%s""",
                        (str(linked_item_id),),
                    )
                    ir = cur.fetchone()
                    if ir:
                        (n, wid, wtype, st, sc, sm, ac, impl, due,
                         p_name, p_wid, p_sum) = ir
                        it_sec = [
                            "\n## ITEM",
                            f"**[{(wtype or 'task').upper()}] {wid or 'pending'} — {n}**\n"
                            f"status={st or 'open'}  current_score={sc or 0}/5",
                        ]
                        if sm:   it_sec.append(f"\n**Summary:**\n{sm[:600]}")
                        if ac:   it_sec.append(f"\n**Acceptance Criteria:**\n{ac[:600]}")
                        if impl: it_sec.append(f"\n**Implementation Plan:**\n{impl[:400]}")
                        if due:  it_sec.append(f"\n**Due:** {due}")
                        if p_name:
                            it_sec.append(f"\n**Parent UC:** {p_name} [{p_wid}]")
                            if p_sum:
                                it_sec.append(f"UC Summary: {p_sum[:400]}")
                        sections.append("\n".join(it_sec))

                # ── Linked prompts/commits (wi_id column ties mirror rows to items) ─
                # Determine the text wi_id (e.g. "UC0001") for linking.
                # Use Python's scoping: uc_wi_id / wid set in branches above.
                _link_wi_id = (
                    (uc_row[1] if linked_uc_id and uc_row else None)   # uc_wi_id
                    or (ir[1] if linked_item_id and ir else None)       # wid
                )
                _link_uuid = str(linked_uc_id or linked_item_id)

                try:
                    if _link_wi_id:
                        # Recent prompts/responses tied to this UC or item
                        cur.execute(
                            """SELECT left(prompt, 400), left(response, 400), created_at
                               FROM mem_mrr_prompts
                               WHERE project_id=%s AND wi_id=%s
                               ORDER BY created_at DESC LIMIT 5""",
                            (project_id, _link_wi_id),
                        )
                        prows = cur.fetchall()
                        if prows:
                            psec = [f"\n## PRIOR WORK — Prompts linked to {_link_wi_id}:"]
                            for p_txt, r_txt, ts in prows:
                                ts_str = ts.strftime("%d/%m/%y %H:%M") if ts else "?"
                                psec.append(f"\n[{ts_str}]")
                                if p_txt: psec.append(f"User: {p_txt}")
                                if r_txt: psec.append(f"AI: {r_txt}")
                            sections.append("\n".join(psec))

                        # Commits tied to this UC or item
                        cur.execute(
                            """SELECT commit_msg, diff_summary, created_at
                               FROM mem_mrr_commits
                               WHERE project_id=%s AND wi_id=%s
                               ORDER BY created_at DESC LIMIT 5""",
                            (project_id, _link_wi_id),
                        )
                        crows = cur.fetchall()
                        if crows:
                            csec = [f"\n## PRIOR WORK — Commits linked to {_link_wi_id}:"]
                            for msg, diff, ts in crows:
                                ts_str = ts.strftime("%d/%m/%y %H:%M") if ts else "?"
                                csec.append(f"\n[{ts_str}] {msg or ''}")
                                if diff: csec.append(f"  Summary: {diff[:300]}")
                            sections.append("\n".join(csec))

                    # Previous successful pipeline run for this item/UC
                    cur.execute(
                        """SELECT s.role_name, s.status, left(s.output_text, 500), r.created_at
                           FROM pr_pipeline_run_stages s
                           JOIN pr_pipeline_runs r ON r.id = s.run_id
                           WHERE (r.linked_uc_id=%s::uuid OR r.linked_item_id=%s::uuid)
                             AND r.status = 'done'
                           ORDER BY r.created_at DESC, s.id
                           LIMIT 16""",
                        (_link_uuid, _link_uuid),
                    )
                    prev_stages = cur.fetchall()
                    if prev_stages:
                        prev_sec = ["\n## PREVIOUS PIPELINE RUN OUTPUT (most recent completed):"]
                        seen_run_ts: str | None = None
                        for role, status, output, ts in prev_stages:
                            ts_str = ts.strftime("%d/%m/%y %H:%M") if ts else "?"
                            if ts_str != seen_run_ts:
                                seen_run_ts = ts_str
                                prev_sec.append(f"\n### Run from {ts_str}:")
                            if output:
                                prev_sec.append(f"\n**{role}** ({status}):\n{output}")
                        sections.append("\n".join(prev_sec))

                except Exception as _e:
                    log.debug("linked context query failed: %s", _e)

    except Exception as e:
        log.warning("_enrich_task_from_db failed: %s", e)

    # ── Pipeline instructions ─────────────────────────────────────────────────
    if linked_uc_id:
        sections.append(
            "\n## PIPELINE INSTRUCTIONS\n"
            "All pipeline stages must:\n"
            "1. **PM**: break down open items into sub-tasks; query search_memory for prior decisions\n"
            "2. **Architect**: design implementation; read relevant files with read_file/list_dir\n"
            "3. **Developer**: implement EVERY open item using tools:\n"
            "   - search_memory → read_file → write_file → git_diff (verify) → git_commit\n"
            "   - Score each item 0-5 in structured output (changes_made list)\n"
            "4. **Reviewer**: verify actual file changes with git_diff; approve/reject per item\n"
            "\nOutput must include per-item scores (0-5) in structured JSON."
        )
    elif linked_item_id:
        sections.append(
            "\n## PIPELINE INSTRUCTIONS\n"
            "Implement the single item above:\n"
            "1. search_memory → check past decisions\n"
            "2. read_file → understand current code\n"
            "3. write_file → implement changes\n"
            "4. git_diff → verify correctness\n"
            "5. git_commit → commit changes\n"
            "Score the item 0-5 in structured output."
        )

    return "\n\n".join(sections)


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
    output_md_name:  str           = ""         # custom filename for the MD report (e.g. "my_feature.md")


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
    output_md_name: str = "",
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

    # Enrich task with full UC/item context from DB
    if linked_uc_id or linked_item_id:
        task = _enrich_task_from_db(project_id, task, linked_uc_id, linked_item_id)
        log.info("Task enriched for run_id=%s (%d chars)", run_id, len(task))

    # In-memory stage data for report (avoids fragile DB re-query at the end)
    _stage_mem: list[dict] = []

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

        # Approval gate BEFORE this stage — triggered by per-stage flag OR DB setting
        _gate_by_stage = stage_def.approval_gate
        _gate_by_db    = bool(require_approval_after and i > 0 and stage_order[i - 1] == require_approval_after)
        if _gate_by_stage or _gate_by_db:
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

            # Inject user feedback into handoff so next stage sees it
            user_fb = result_info.get("feedback", "").strip()
            if user_fb and isinstance(handoff, dict):
                handoff["user_approval_feedback"] = user_fb
                log.info("Approval gate: injecting user feedback (%d chars) into handoff", len(user_fb))

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
        # Capture handoff BEFORE running (for report — avoids DB re-query)
        _input_handoff_snap = dict(handoff) if isinstance(handoff, dict) else handoff
        max_attempts = max(1, stage_def.retry)
        for retry_num in range(max_attempts):
            try:
                agent = await Agent.from_role(stage_def.role)
                if stage_def.temperature_override is not None:
                    agent.temperature = stage_def.temperature_override
                if stage_def.max_iterations_override is not None:
                    agent.max_iterations = stage_def.max_iterations_override

                # Snapshot what we're passing into this stage (for display)
                input_snap = _json.dumps(handoff) if handoff else None

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

        # Log stage result + ReAct steps
        if stage_id:
            try:
                with db.conn() as conn:
                    # Write each ReAct step so the log shows the thinking process
                    if stage_result and stage_result.steps:
                        for st in stage_result.steps:
                            thought_preview = (st.thought or "")[:300].strip()
                            step_txt = f"Step {st.step_num}"
                            if thought_preview:
                                step_txt += f": {thought_preview}"
                            if st.action_name:
                                args_preview = ", ".join(
                                    f"{k}={str(v)[:60]}"
                                    for k, v in list((st.action_args or {}).items())[:3]
                                )
                                step_txt += f"\n  → {st.action_name}({args_preview})"
                            if st.observation:
                                step_txt += f"\n  ← {st.observation[:200]}"
                            _append_stage_log(conn, stage_id, step_txt)
                    # Final status line
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

        # Collect stage data in memory (used for report — no DB re-query needed)
        _stage_mem.append({
            "key":          stage_def.key,
            "role":         stage_def.role,
            "status":       "error" if stage_error else "done",
            "input_handoff": _input_handoff_snap,
            "output_text":  (stage_result.output or "")[:10000] if stage_result else "",
            "structured_out": stage_result.structured_output if stage_result else None,
            "steps":        list(stage_result.steps) if stage_result and stage_result.steps else [],
            "cost":         stage_result.cost_usd if stage_result else 0.0,
            "in_tok":       stage_result.input_tokens if stage_result else 0,
            "out_tok":      stage_result.output_tokens if stage_result else 0,
            "dur":          dur_s,
            "error":        stage_error,
        })

        # Persist stage result
        if stage_result:
            total_cost += stage_result.cost_usd
            total_in   += stage_result.input_tokens
            total_out  += stage_result.output_tokens
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    so = _json.dumps(stage_result.structured_output) if (stage_result and stage_result.structured_output) else None
                    # Serialize ReAct steps for display in UI
                    steps_data = None
                    if stage_result and stage_result.steps:
                        steps_data = _json.dumps([
                            {
                                "step": s.step_num,
                                "thought": s.thought[:500] if s.thought else "",
                                "tool": s.action_name,
                                "args": {k: str(v)[:200] for k, v in (s.action_args or {}).items()},
                                "observation": s.observation[:800] if s.observation else "",
                            }
                            for s in stage_result.steps
                        ])
                    cur.execute(
                        """UPDATE pr_pipeline_run_stages
                           SET status=%s, output_text=%s, structured_out=%s::jsonb,
                               input_tokens=%s, output_tokens=%s, cost_usd=%s,
                               duration_s=%s, finished_at=NOW(),
                               temperature_used=%s,
                               input_snapshot=%s::jsonb,
                               steps_json=%s::jsonb
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
                            input_snap,
                            steps_data,
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

        # Reviewer rejection handling + per-item score updates
        if stage_order[i] == "reviewer":
            verdict = (handoff or {}).get("verdict", "approved")

            # Update individual work item scores from work_items_reviewed
            reviewed_items = (handoff or {}).get("work_items_reviewed", [])
            if reviewed_items and (linked_uc_id or linked_item_id):
                try:
                    with db.conn() as conn:
                        with conn.cursor() as cur:
                            for ri in reviewed_items:
                                wi_id_str = ri.get("wi_id") or ""
                                score     = ri.get("score")
                                summary   = (ri.get("summary") or "")[:300]
                                if not wi_id_str or score is None:
                                    continue
                                cur.execute(
                                    "UPDATE mem_work_items SET score_status=%s "
                                    "WHERE wi_id=%s AND project_id=%s",
                                    (int(score), wi_id_str, project_id),
                                )
                                if summary:
                                    cur.execute(
                                        "UPDATE mem_work_items "
                                        "SET summary = COALESCE(summary,'') || %s "
                                        "WHERE wi_id=%s AND project_id=%s",
                                        (f"\n[REVIEW {_datetime.utcnow().strftime('%d/%m/%y')}] {summary}",
                                         wi_id_str, project_id),
                                    )
                        conn.commit()
                    log.info("Updated %d item scores from reviewer (run_id=%s)",
                             len(reviewed_items), run_id)
                except Exception as _re:
                    log.warning("Could not update item scores from reviewer: %s", _re)

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

    # Post-completion: save execution report (built from in-memory _stage_mem)
    try:
        from core.project_paths import documents_dir as _docs_dir
        from datetime import datetime as _dt2
        import re as _re
        safe_name = _re.sub(r"[^a-zA-Z0-9_-]", "_", pipeline_name)
        ts_file = _dt2.utcnow().strftime("%d%m%y_%H%M")

        # Re-read output_md_path from DB — user may have updated it mid-run via PATCH
        _db_md_path = None
        try:
            with db.conn() as _c:
                with _c.cursor() as _cr:
                    _cr.execute("SELECT output_md_path FROM pr_pipeline_runs WHERE id=%s", (run_id,))
                    _row = _cr.fetchone()
                    _db_md_path = (_row[0] if _row else None) or output_md_name or None
        except Exception:
            _db_md_path = output_md_name or None

        # Determine doc_path from (in priority order):
        #  1. _db_md_path — user may have updated via PATCH; can be "folder/file.md" or just "file.md"
        #  2. auto-generated: documents/pipelines/{pipeline}/{ts}_{uc_slug}.md
        _default_run_dir = _docs_dir(project) / "pipelines" / safe_name
        if _db_md_path:
            _clean = _re.sub(r"[^a-zA-Z0-9_.\-/]", "_", _db_md_path.strip())
            if not _clean.lower().endswith(".md"):
                _clean += ".md"
            if "/" in _clean:
                # Treat as path relative to workspace root (documents dir parent)
                doc_path = _docs_dir(project).parent / _clean
            else:
                doc_path = _default_run_dir / _clean
        else:
            _uc_slug = None
            if linked_uc_id:
                try:
                    with db.conn() as _cn:
                        with _cn.cursor() as _cr:
                            _cr.execute("SELECT name FROM mem_work_items WHERE id=%s", (str(linked_uc_id),))
                            _r = _cr.fetchone()
                            _uc_slug = _re.sub(r"[^a-zA-Z0-9_-]", "_", (_r[0] if _r else "run"))[:40]
                except Exception:
                    _uc_slug = "run"
            doc_path = _default_run_dir / (f"{ts_file}_{_uc_slug}.md" if _uc_slug else f"{ts_file}.md")
        doc_path.parent.mkdir(parents=True, exist_ok=True)

        # Build stage sections from in-memory data (no DB re-query needed)
        stage_sections: list[str] = []
        for sm in _stage_mem:
            lines: list[str] = [
                f"## Stage: {sm['key']} ({sm['role']}) — {sm['status'].upper()}",
                f"_Duration: {sm['dur']:.1f}s | "
                f"Tokens: {sm['in_tok']:,} in / {sm['out_tok']:,} out | "
                f"Cost: ${sm['cost']:.4f}_",
            ]
            # ── Input received ────────────────────────────────────────────────
            snap = sm["input_handoff"]
            if snap and isinstance(snap, dict):
                snap_parts: list[str] = []
                if snap.get("role"):    snap_parts.append(f"From role: **{snap['role']}**")
                if snap.get("verdict"): snap_parts.append(f"Verdict: {snap['verdict']}")
                for _k in ("summary", "plan", "description"):
                    if snap.get(_k): snap_parts.append(f"{_k.title()}: {str(snap[_k])[:500]}")
                if snap.get("issues"):
                    snap_parts.append("Issues:\n" + "\n".join(f"  - {x}" for x in snap["issues"][:5]))
                if snap.get("work_items"):
                    snap_parts.append(f"Work items: {_json.dumps(snap['work_items'])[:400]}")
                if snap.get("changes_made"):
                    snap_parts.append(f"Changes: {_json.dumps(snap['changes_made'])[:400]}")
                if snap.get("suggested_fixes"):
                    snap_parts.append("Suggested fixes:\n" + "\n".join(f"  - {x}" for x in snap["suggested_fixes"][:5]))
                if snap.get("raw_output"):
                    snap_parts.append(f"Raw preview: {str(snap['raw_output'])[:400]}")
                if snap_parts:
                    lines.append("\n**Input from previous stage:**\n" + "\n".join(f"- {p}" for p in snap_parts))
            else:
                lines.append("\n**Input:** _(first stage — receives task directly)_")

            # ── Tool calls ────────────────────────────────────────────────────
            steps = sm["steps"]
            if steps:
                tool_lines: list[str] = []
                for st in steps:
                    args = getattr(st, "action_args", None) or {}
                    obs  = (getattr(st, "observation", None) or "")[:300]
                    args_str = ", ".join(
                        f"{k}={str(v)[:80]}" for k, v in list(args.items())[:4]
                    )
                    tool_lines.append(
                        f"  {getattr(st,'step_num','')}. "
                        f"`{getattr(st,'action_name','?')}`({args_str})"
                    )
                    if obs:
                        tool_lines.append(f"     → {obs}")
                lines.append(f"\n**Tool calls ({len(steps)}):**\n" + "\n".join(tool_lines))
            else:
                lines.append("\n**Tool calls:** None")

            # ── Output ────────────────────────────────────────────────────────
            sout = sm["structured_out"]
            if sout:
                lines.append(
                    f"\n**Structured Output:**\n```json\n"
                    f"{_json.dumps(sout, indent=2)[:3000]}\n```"
                )
            elif sm["output_text"]:
                cleaned = sm["output_text"].replace("Thought:", "\nThought:")[:3000].strip()
                lines.append(f"\n**Output:**\n```\n{cleaned}\n```")

            if sm["error"]:
                lines.append(f"\n**ERROR:** {sm['error']}")

            stage_sections.append("\n".join(lines))

        # ── Report header ─────────────────────────────────────────────────────
        header_lines = [
            f"# Pipeline Execution Report: {pipeline_name}",
            f"**Run ID:** {run_id}",
            f"**Project:** {project}",
            f"**Date:** {_dt2.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Verdict:** {final_verdict.upper()}",
            f"**Duration:** {dur_total:.1f}s",
            f"**Total Tokens:** {total_in:,} in / {total_out:,} out",
            f"**Total Cost:** ${total_cost:.4f}",
        ]
        if linked_uc_id:  header_lines.append(f"**Linked UC:** {linked_uc_id}")
        if linked_item_id: header_lines.append(f"**Linked Item:** {linked_item_id}")
        header_lines.append(f"\n## Task Input\n```\n{task[:2000]}\n```")

        doc_content = "\n".join(header_lines) + "\n\n---\n\n" + "\n\n---\n\n".join(stage_sections)
        doc_path.write_text(doc_content, encoding="utf-8")
        log.info("Execution report saved: %s", doc_path)
    except Exception as _de:
        log.warning("Could not save execution report: %s", _de, exc_info=True)

    # Post-completion: log aggregate usage to mng_usage_logs
    if total_in > 0:
        try:
            from routers.route_usage import log_usage as _log_usage
            _log_usage(
                user_id="pipeline",
                provider="claude",
                model=f"pipeline:{pipeline_name}",
                input_tokens=total_in,
                output_tokens=total_out,
                charged_usd=round(total_cost, 8),
                source="pipeline",
                metadata={"run_id": run_id, "project": project, "verdict": final_verdict},
            )
        except Exception as _ue:
            log.debug("Could not log pipeline usage: %s", _ue)

    # NOTE: linked item/UC summary is NOT updated automatically.
    # The user reviews the run in the panel and clicks "Apply" to write their summary.

    log.info(
        "Async pipeline run done: run_id=%s verdict=%s cost=$%.4f dur=%.1fs in=%d out=%d",
        run_id, final_verdict, total_cost, dur_total, total_in, total_out,
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
                            source, linked_uc_id, linked_item_id, output_md_path)
                       VALUES (%s, %s, %s, %s, %s::jsonb, 'running', %s, %s, %s, %s)""",
                    (run_id, project_id, req.pipeline, req.task,
                     _json.dumps(req.input_files),
                     req.source, req.linked_uc_id, req.linked_item_id,
                     req.output_md_name or None),
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
            output_md_name=req.output_md_name,
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
                              linked_uc_id, linked_item_id, source, output_md_path
                       FROM pr_pipeline_runs WHERE id=%s""",
                    (run_id,),
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(404, "Run not found")

                cur.execute(
                    """SELECT id, stage_key, role_name, status, attempt,
                              output_text, log_lines, input_tokens, output_tokens,
                              cost_usd, duration_s, temperature_used, started_at, finished_at,
                              structured_out, steps_json, input_snapshot
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
                "structured_out":  sr[14],   # parsed JSON handoff (if model emitted one)
                "steps_json":      sr[15],   # ReAct trace steps
                "input_snapshot":  sr[16],   # handoff passed INTO this stage
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
            "source":              row[15] or "direct",
            "output_md_path":      row[16],
            "stages":              stages,
        }
    except HTTPException:
        raise
    except Exception as e:
        log.exception("get_pipeline_run failed: %s", e)
        raise HTTPException(500, str(e))


@router.patch("/pipeline-runs/{run_id}")
async def patch_pipeline_run(run_id: str, body: dict) -> dict:
    """Update mutable fields on a pipeline run (output_md_path for now)."""
    from core.database import db
    import re as _re2
    if not db.is_available():
        raise HTTPException(503, "Database not available")
    updates: dict[str, object] = {}
    if "output_md_path" in body:
        raw = (body["output_md_path"] or "").strip()
        if raw:
            # Allow folder separators; sanitise everything else
            raw = _re2.sub(r"[^a-zA-Z0-9_.\-/]", "_", raw)
        updates["output_md_path"] = raw or None
    if not updates:
        raise HTTPException(422, "No updatable fields provided")
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                set_clause = ", ".join(f"{k}=%s" for k in updates)
                cur.execute(
                    f"UPDATE pr_pipeline_runs SET {set_clause} WHERE id=%s",
                    [*updates.values(), run_id],
                )
                if cur.rowcount == 0:
                    raise HTTPException(404, "Run not found")
            conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        log.exception("patch_pipeline_run failed: %s", e)
        raise HTTPException(500, str(e))
    return {"ok": True, "run_id": run_id, **updates}


@router.patch("/pipelines/{name}/settings")
async def patch_pipeline_settings(name: str, body: dict) -> dict:
    """Update mutable pipeline settings: require_approval_after, continue_on_failure."""
    from core.database import db
    if not db.is_available():
        raise HTTPException(503, "Database not available")
    updates: dict[str, object] = {}
    if "require_approval_after" in body:
        v = body["require_approval_after"]
        updates["require_approval_after"] = str(v) if v else None
    if "continue_on_failure" in body:
        updates["continue_on_failure"] = bool(body["continue_on_failure"])
    if not updates:
        raise HTTPException(422, "No updatable fields")
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                set_clause = ", ".join(f"{k}=%s" for k in updates)
                cur.execute(
                    f"INSERT INTO mng_agent_pipelines (client_id, name, {', '.join(updates)}) "
                    f"VALUES (1, %s, {', '.join(['%s']*len(updates))}) "
                    f"ON CONFLICT (client_id, name) DO UPDATE SET {set_clause}",
                    [name, *updates.values(), *updates.values()],
                )
            conn.commit()
    except Exception as e:
        log.exception("patch_pipeline_settings failed: %s", e)
        raise HTTPException(500, str(e))
    return {"ok": True, "pipeline": name, **updates}


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
