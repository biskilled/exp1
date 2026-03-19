"""
work_items.py — Work item management with 4-agent pipeline support.

Replaces entity_values for feature/bug/task categories. Adds:
  - acceptance_criteria / implementation_plan fields
  - agent pipeline (PM → Architect → Developer → Reviewer) via graph DAG
  - project_facts (durable extracted facts)
  - memory_items (Trycycle-reviewed session/feature summaries)

Endpoints:
    GET    /work-items                    ?project=&category=&status=
    POST   /work-items                    {category_name, name, description, ...}
    PATCH  /work-items/{id}               {name?, description?, lifecycle_status?, ...}
    DELETE /work-items/{id}
    GET    /work-items/{id}/interactions  ?limit=20
    POST   /work-items/migrate-from-tags  ?project=
    POST   /work-items/{id}/run-pipeline  ?project=
    GET    /work-items/facts              ?project=
    GET    /work-items/memory-items       ?project=&scope=session|feature
f"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from config import settings
from core.database import db
from core.seq import next_seq

router = APIRouter()
log = logging.getLogger(__name__)


def _require_db():
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")


def _project(p: str | None) -> str:
    return p or settings.active_project or "default"


# ── Models ────────────────────────────────────────────────────────────────────

class WorkItemCreate(BaseModel):
    category_name:       str
    name:                str
    description:         str = ""
    project:             Optional[str] = None
    status:              str = "active"
    lifecycle_status:    str = "idea"
    due_date:            Optional[str] = None
    parent_id:           Optional[str] = None
    acceptance_criteria: str = ""
    implementation_plan: str = ""
    tags:                list[str] = []


class WorkItemPatch(BaseModel):
    name:                Optional[str] = None
    description:         Optional[str] = None
    status:              Optional[str] = None
    lifecycle_status:    Optional[str] = None
    due_date:            Optional[str] = None
    acceptance_criteria: Optional[str] = None
    implementation_plan: Optional[str] = None
    agent_status:        Optional[str] = None
    tags:                Optional[list[str]] = None


# ── CRUD ─────────────────────────────────────────────────────────────────────

@router.get("")
async def list_work_items(
    project:  str | None = Query(None),
    category: str | None = Query(None),
    status:   str | None = Query(None),
    name:     str | None = Query(None),
    limit:    int        = Query(100),
):
    """List work items, optionally filtered by category, status, or exact name."""
    _require_db()
    p = _project(project)
    where = ["w.client_id=1", "w.project=%s"]
    params: list = [p]
    if category:
        where.append("w.category_name=%s"); params.append(category)
    if status:
        where.append("w.status=%s"); params.append(status)
    if name:
        where.append("w.name=%s"); params.append(name)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT w.id, w.category_name, w.name, w.description,
                          w.status, w.lifecycle_status, w.due_date,
                          w.parent_id, w.acceptance_criteria, w.implementation_plan,
                          w.agent_run_id, w.agent_status, w.tags,
                          w.created_at, w.updated_at,
                          w.seq_num, w.entity_value_id,
                          ec.color, ec.icon,
                          (SELECT COUNT(*) FROM pr_interaction_tags it
                           WHERE it.work_item_id = w.id) AS interaction_count
                   FROM pr_work_items w
                   LEFT JOIN mng_entity_categories ec ON ec.client_id=1 AND ec.project=w.project AND ec.name=w.category_name
                   WHERE {' AND '.join(where)}
                   ORDER BY w.category_name, w.status, w.created_at DESC
                   LIMIT %s""",
                params + [limit],
            )
            cols = [d[0] for d in cur.description]
            rows = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                for dt_field in ("created_at", "updated_at"):
                    if row.get(dt_field):
                        row[dt_field] = row[dt_field].isoformat()
                if row.get("due_date"):
                    row["due_date"] = row["due_date"].isoformat()
                row["id"] = str(row["id"])
                if row.get("parent_id"):
                    row["parent_id"] = str(row["parent_id"])
                if row.get("agent_run_id"):
                    row["agent_run_id"] = str(row["agent_run_id"])
                if row.get("tags") is None:
                    row["tags"] = []
                rows.append(row)
    return {"work_items": rows, "project": p, "total": len(rows)}


@router.post("", status_code=201)
async def create_work_item(body: WorkItemCreate, project: str | None = Query(None)):
    f"""Create a new work item."""
    _require_db()
    p = _project(project or body.project)

    # Resolve category_id from mng_entity_categories if it exists
    category_id = None
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM mng_entity_categories WHERE client_id=1 AND project=%s AND name=%s",
                (p, body.category_name),
            )
            row = cur.fetchone()
            if row:
                category_id = row[0]

            seq = next_seq(cur, p, body.category_name)
            cur.execute(
                """INSERT INTO pr_work_items
                       (client_id, project, category_name, category_id, name, description,
                        status, lifecycle_status, due_date, parent_id,
                        acceptance_criteria, implementation_plan, tags, seq_num)
                   VALUES (1, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (client_id, project, category_name, name) DO NOTHING
                   RETURNING id, name, category_name, created_at, seq_num""",
                (p, body.category_name, category_id, body.name, body.description,
                 body.status, body.lifecycle_status, body.due_date or None,
                 body.parent_id or None,
                 body.acceptance_criteria, body.implementation_plan,
                 body.tags, seq),
            )
            r = cur.fetchone()
    return {
        "id": str(r[0]), "name": r[1], "category_name": r[2],
        "created_at": r[3].isoformat(), "project": p,
        "seq_num": r[4],
    }


@router.patch("/{item_id}")
async def patch_work_item(
    item_id: str,
    body: WorkItemPatch,
    project: str | None = Query(None),
    background: BackgroundTasks = BackgroundTasks(),
):
    f"""Update work item fields. Triggers feature memory synthesis when lifecycle → done.f"""
    _require_db()
    p = _project(project)
    fields, params = [], []
    if body.name                is not None: fields.append("name=%s");                params.append(body.name)
    if body.description         is not None: fields.append("description=%s");         params.append(body.description)
    if body.status              is not None: fields.append("status=%s");              params.append(body.status)
    if body.lifecycle_status    is not None: fields.append("lifecycle_status=%s");    params.append(body.lifecycle_status)
    if body.due_date            is not None: fields.append("due_date=%s");            params.append(body.due_date or None)
    if body.acceptance_criteria is not None: fields.append("acceptance_criteria=%s"); params.append(body.acceptance_criteria)
    if body.implementation_plan is not None: fields.append("implementation_plan=%s"); params.append(body.implementation_plan)
    if body.agent_status        is not None: fields.append("agent_status=%s");        params.append(body.agent_status)
    if body.tags                is not None: fields.append("tags=%s");                params.append(body.tags)

    if not fields:
        raise HTTPException(400, "Nothing to update")

    fields.append("updated_at=NOW()")
    params.append(item_id)
    params.append(p)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE pr_work_items SET {','.join(fields)} WHERE id=%s::uuid AND client_id=1 AND project=%s RETURNING id",
                params,
            )
            if not cur.fetchone():
                raise HTTPException(404, "Work item not found")

    # When lifecycle → done, synthesize feature memory in background
    if body.lifecycle_status == "done":
        from routers.projects import _summarize_feature_memory
        try:
            asyncio.create_task(_summarize_feature_memory(p, item_id))
        except Exception:
            pass

    return {"ok": True, "id": item_id}


@router.delete("/{item_id}")
async def delete_work_item(item_id: str, project: str | None = Query(None)):
    """Delete a work item and all its interaction_tags.f"""
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM pr_work_items WHERE id=%s::uuid AND client_id=1 AND project=%s RETURNING id",
                (item_id, p),
            )
            if not cur.fetchone():
                raise HTTPException(404, "Work item not found")
    return {"ok": True}


# ── Lookup by sequential number ───────────────────────────────────────────────

@router.get("/number/{seq_num}")
async def get_work_item_by_number(seq_num: int, project: str | None = Query(None)):
    """Resolve a short sequential number (e.g. #10005) to the full work item."""
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT w.id, w.category_name, w.name, w.description,
                          w.status, w.lifecycle_status, w.due_date,
                          w.acceptance_criteria, w.implementation_plan,
                          w.agent_run_id, w.agent_status, w.tags,
                          w.created_at, w.updated_at, w.seq_num, w.entity_value_id
                   FROM pr_work_items w
                   WHERE w.client_id=1 AND w.project=%s AND w.seq_num=%s
                   LIMIT 1""",
                (p, seq_num),
            )
            r = cur.fetchone()
            if not r:
                raise HTTPException(404, f"Work item #{seq_num} not found in project {p!r}")
            cols = [d[0] for d in cur.description]
            row = dict(zip(cols, r))
            row["id"] = str(row["id"])
            for dt_field in ("created_at", "updated_at"):
                if row.get(dt_field):
                    row[dt_field] = row[dt_field].isoformat()
            if row.get("due_date"):
                row["due_date"] = row["due_date"].isoformat()
            if row.get("agent_run_id"):
                row["agent_run_id"] = str(row["agent_run_id"])
            if row.get("tags") is None:
                row["tags"] = []
            return row


# ── Interactions for a work item ──────────────────────────────────────────────

@router.get("/{item_id}/interactions")
async def get_work_item_interactions(
    item_id: str,
    project: str | None = Query(None),
    limit:   int        = Query(20),
):
    """Return recent interactions tagged to this work item.f"""
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT i.id, i.session_id, i.event_type, i.source_id,
                          i.prompt, i.response, i.phase, i.created_at
                   FROM pr_interaction_tags it
                   JOIN pr_interactions i ON i.id = it.interaction_id
                   WHERE it.work_item_id=%s::uuid AND i.client_id=1 AND i.project=%s
                   ORDER BY i.created_at DESC LIMIT %s""",
                (item_id, p, limit),
            )
            cols = [d[0] for d in cur.description]
            rows = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                row["id"] = str(row["id"])
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
                rows.append(row)
    return {"interactions": rows, "work_item_id": item_id, "project": p}


# ── Migrate from mng_entity_values ────────────────────────────────────────────────

@router.post("/migrate-from-tags")
async def migrate_from_tags(project: str | None = Query(None)):
    f"""Copy feature/bug/task entity_values → work_items. Idempotent."""
    _require_db()
    p = _project(project)
    from core.migrations.migrate_to_memory_layers import run_migration
    asyncio.create_task(run_migration(p))
    return {"status": "migration started", "project": p}


# ── Agent pipeline ────────────────────────────────────────────────────────────

@router.post("/{item_id}/run-pipeline")
async def run_pipeline(item_id: str, project: str | None = Query(None)):
    """Start the 4-agent PM→Architect→Developer→Reviewer pipeline for a work item.

    Finds or creates the '_work_item_pipeline' graph workflow for this project,
    then runs it via the graph_runner so the run is visible in the Workflow tab.
    Falls back to the standalone pipeline if graph_runner fails.
    f"""
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name, description, acceptance_criteria FROM pr_work_items WHERE id=%s::uuid AND client_id=1 AND project=%s",
                (item_id, p),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Work item not found")

    name, desc, existing_ac = row

    # ── Ensure the pipeline graph workflow exists ─────────────────────────────
    workflow_id = await _ensure_pipeline_workflow(p)
    run_id = None

    if workflow_id:
        # Build user_input: work item + all tagged context (interactions + commits)
        user_input = _build_pipeline_context(p, item_id, name, desc, existing_ac)
        try:
            run_id_str = str(uuid.uuid4())
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO pr_graph_runs (id, client_id, project, workflow_id, status, user_input)
                           VALUES (%s, 1, %s, %s, 'running', %s)""",
                        (run_id_str, p, workflow_id, user_input),
                    )

            # Mark work item running — use run_id_str directly (it's the UUID we just inserted)
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE pr_work_items SET agent_status='running', agent_run_id=%s::uuid, updated_at=NOW() WHERE id=%s::uuid",
                        (run_id_str, item_id),
                    )

            # Run in background via graph_runner
            from core.graph_runner import run_graph_workflow

            async def _run_graph():
                try:
                    ctx = await run_graph_workflow(str(workflow_id), user_input, run_id_str, p,
                                                   work_item_id=item_id)
                    # Extract node outputs by actual node names from _ensure_pipeline_workflow
                    ac   = ctx.get("PM") or ctx.get("pm") or ctx.get("planner") or ""
                    impl = ctx.get("Architect") or ctx.get("architect") or ""
                    dev  = ctx.get("Developer") or ctx.get("developer") or ""
                    rev  = ctx.get("Reviewer") or ctx.get("reviewer") or ""
                    if isinstance(ac, dict):   ac   = ac.get("output", str(ac))
                    if isinstance(impl, dict): impl = impl.get("output", str(impl))
                    if isinstance(dev, dict):  dev  = dev.get("output", str(dev))
                    if dev and impl:
                        impl = f"{impl}\n\n## Implementation Output\n{dev}"
                    with db.conn() as conn2:
                        with conn2.cursor() as cur2:
                            cur2.execute(
                                """UPDATE pr_work_items
                                   SET agent_status='done',
                                       acceptance_criteria=COALESCE(NULLIF(%s,''), acceptance_criteria),
                                       implementation_plan=COALESCE(NULLIF(%s,''), implementation_plan),
                                       updated_at=NOW()
                                   WHERE id=%s::uuid""",
                                (str(ac), str(impl) if impl else "", item_id),
                            )
                    # Upsert a project fact so MCP / /memory picks this up
                    if ac:
                        _upsert_pipeline_fact(p, name, ac, rev)
                    # Trigger feature memory synthesis in background
                    try:
                        from routers.projects import _summarize_feature_memory
                        asyncio.create_task(_summarize_feature_memory(p, item_id))
                    except Exception as _me:
                        log.debug(f"Memory synthesis skipped: {_me}")
                    # Save pipeline run as an interaction in history
                    _save_pipeline_interaction(p, item_id, run_id_str, name, ac, rev)
                    # If reviewer approved → close the feature
                    if rev:
                        _maybe_close_feature(p, item_id, rev)
                except Exception as exc:
                    log.error(f"run_pipeline graph failed for {item_id}: {exc}", exc_info=True)
                    # Mark work item as error so it doesn't stay stuck at 'running'
                    try:
                        with db.conn() as conn_err:
                            with conn_err.cursor() as cur_err:
                                cur_err.execute(
                                    "UPDATE pr_work_items SET agent_status='error', updated_at=NOW() WHERE id=%s::uuid",
                                    (item_id,),
                                )
                    except Exception:
                        pass
                    # Fallback: standalone pipeline
                    try:
                        from core.work_item_pipeline import trigger_work_item_pipeline
                        await trigger_work_item_pipeline(item_id, p, name, desc, existing_ac)
                    except Exception as fb_exc:
                        log.error(f"Standalone fallback also failed: {fb_exc}")

            asyncio.create_task(_run_graph())
            return {"status": "pipeline started", "work_item_id": item_id,
                    "workflow_id": str(workflow_id), "run_id": run_id_str, "project": p}

        except Exception as e:
            log.warning(f"Graph pipeline setup failed ({e}), falling back to standalone")

    # Fallback: standalone pipeline (no DB graph)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE pr_work_items SET agent_status='running', updated_at=NOW() WHERE id=%s::uuid",
                (item_id,),
            )
    from core.work_item_pipeline import trigger_work_item_pipeline
    asyncio.create_task(trigger_work_item_pipeline(item_id, p, name, desc, existing_ac))
    return {"status": "pipeline started", "work_item_id": item_id, "project": p}


def _build_pipeline_context(
    project: str, item_id: str, name: str, desc: str, existing_ac: str
) -> str:
    """Build rich user_input for the pipeline: work item + all tagged history.

    Fetches tagged interactions and commits so the PM agent has full context.
    """
    lines = [
        f"# Work Item: {name}",
        f"**Description:** {desc or 'No description provided.'}",
    ]
    if existing_ac:
        lines += ["", "**Existing Acceptance Criteria:**", existing_ac]

    if not db.is_available():
        return "\n".join(lines)

    # Tagged interactions (chat prompts/responses linked to this work item)
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT i.role, i.content, i.created_at
                       FROM pr_interactions i
                       JOIN pr_interaction_tags t ON t.interaction_id = i.id
                       WHERE t.work_item_id = %s::uuid
                       ORDER BY i.created_at DESC LIMIT 30""",
                    (item_id,),
                )
                rows = cur.fetchall()
        if rows:
            lines += ["", "## Tagged Interactions (most recent first)"]
            for role, content, ts in reversed(rows):
                short = (content or "")[:400]
                lines.append(f"[{role}] {short}")
    except Exception as _e:
        log.debug(f"Could not fetch tagged interactions: {_e}")

    # Tagged commits
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT c.commit_hash, c.message, c.committed_at
                       FROM pr_commits c
                       JOIN pr_event_tags et ON et.event_id = c.id
                       JOIN mng_entity_values ev ON ev.id = et.entity_value_id
                       JOIN pr_work_items wi ON wi.entity_value_id = ev.id
                       WHERE wi.id = %s::uuid
                       ORDER BY c.committed_at DESC LIMIT 10""",
                    (item_id,),
                )
                commits = cur.fetchall()
        if commits:
            lines += ["", "## Related Commits"]
            for h, msg, ts in commits:
                lines.append(f"- {str(h)[:8]} {msg or ''}")
    except Exception as _e:
        log.debug(f"Could not fetch tagged commits: {_e}")

    # Memory items for this work item
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT summary FROM pr_memory_items
                       WHERE client_id=1 AND project=%s AND scope_ref=%s
                       ORDER BY created_at DESC LIMIT 3""",
                    (project, item_id),
                )
                mems = cur.fetchall()
        if mems:
            lines += ["", "## Previous Memory Summaries"]
            for (s,) in mems:
                lines.append((s or "")[:500])
    except Exception as _e:
        log.debug(f"Could not fetch memory items: {_e}")

    return "\n".join(lines)


def _save_pipeline_interaction(
    project: str, item_id: str, run_id: str, item_name: str, ac: str, reviewer_out: str
) -> None:
    """Save the pipeline run as an interaction in pr_interactions + tag it to the work item."""
    if not db.is_available():
        return
    summary = f"Pipeline run for: {item_name}"
    content = ""
    if ac:
        content += f"**Acceptance Criteria:**\n{ac[:600]}\n\n"
    if reviewer_out:
        content += f"**Reviewer Output:**\n{reviewer_out[:400]}"
    if not content:
        content = "Pipeline completed."
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                iid = str(uuid.uuid4())
                cur.execute(
                    """INSERT INTO pr_interactions
                       (id, client_id, project, role, content, source, session_id, work_item_id, created_at)
                       VALUES (%s, 1, %s, 'assistant', %s, 'pipeline', %s, %s::uuid, NOW())""",
                    (iid, project, content, run_id[:36], item_id),
                )
                cur.execute(
                    """INSERT INTO pr_interaction_tags (interaction_id, work_item_id, auto_tagged)
                       VALUES (%s::uuid, %s::uuid, TRUE) ON CONFLICT DO NOTHING""",
                    (iid, item_id),
                )
    except Exception as _e:
        log.debug(f"Could not save pipeline interaction: {_e}")


def _maybe_close_feature(project: str, item_id: str, reviewer_output: str) -> None:
    """If reviewer output indicates approval, mark work item lifecycle_status='done'."""
    if not db.is_available():
        return
    rev_lower = reviewer_output.lower() if isinstance(reviewer_output, str) else ""
    # Check for explicit approval signals in reviewer JSON or text
    approved = False
    import re as _re, json as _json
    try:
        m = _re.search(r'"passed"\s*:\s*(true|false)', rev_lower)
        if m:
            approved = m.group(1) == "true"
        else:
            score_m = _re.search(r'"score"\s*:\s*(\d+)', rev_lower)
            if score_m:
                approved = int(score_m.group(1)) >= 7
            else:
                approved = any(w in rev_lower for w in ["approved", "lgtm", "looks good", "passes"])
    except Exception:
        pass
    if approved:
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """UPDATE pr_work_items
                           SET lifecycle_status='done', updated_at=NOW()
                           WHERE id=%s::uuid AND lifecycle_status != 'done'""",
                        (item_id,),
                    )
            log.info(f"Work item {item_id} marked as done by reviewer")
        except Exception as _e:
            log.debug(f"Could not close feature: {_e}")


def _upsert_pipeline_fact(project: str, item_name: str, ac: str, reviewer_output: str) -> None:
    """Save a durable project fact after a pipeline run completes.

    This ensures MCP / /memory synthesis picks up the result without waiting
    for a full memory run.  Fact key: pipeline/{item_name}
    """
    if not db.is_available():
        return
    try:
        summary = f"Acceptance criteria:\n{str(ac)[:400]}"
        if reviewer_output:
            summary += f"\n\nReviewer: {str(reviewer_output)[:200]}"
        with db.conn() as conn:
            with conn.cursor() as cur:
                # Expire any existing current fact for this item
                cur.execute(
                    """UPDATE pr_project_facts SET valid_until=NOW()
                       WHERE client_id=1 AND project=%s AND fact_key=%s AND valid_until IS NULL""",
                    (project, f"pipeline/{item_name}"),
                )
                # Insert fresh fact
                cur.execute(
                    """INSERT INTO pr_project_facts (client_id, project, fact_key, fact_value)
                       VALUES (1, %s, %s, %s)""",
                    (project, f"pipeline/{item_name}", summary),
                )
    except Exception as _fe:
        log.debug(f"Could not upsert pipeline fact: {_fe}")


async def _ensure_pipeline_workflow(project: str) -> int | None:
    """Find or create the '_work_item_pipeline' graph workflow for this project.

    Returns the workflow id (int), or None if DB is unavailable.
    Seeds the workflow with 4 nodes (PM, Architect, Developer, Reviewer) using
    agent_roles if they exist, otherwise inline prompts.
    f"""
    WF_NAME = "_work_item_pipeline"
    if not db.is_available():
        return None
    try:
        existing_wf_id = None
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM pr_graph_workflows WHERE client_id=1 AND project=%s AND name=%s",
                    (project, WF_NAME),
                )
                row = cur.fetchone()
                if row:
                    existing_wf_id = row[0]

        # Load agent_roles for the 4 stages
        role_ids: dict[str, int] = {}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT name, id FROM mng_agent_roles
                           WHERE client_id=1 AND is_active=TRUE AND project='_global'
                           AND name IN ('Product Manager','Sr. Architect','Web Developer','Code Reviewer')"""
                    )
                    for r in cur.fetchall():
                        role_ids[r[0]] = r[1]
        except Exception:
            pass

        claude_model = getattr(settings, "claude_model", settings.haiku_model)

        stages = [
            ("PM", "claude", settings.haiku_model, role_ids.get("Product Manager"),
             """You are a Product Manager analyzing a work item. You will receive:
- The work item name, description, and any existing criteria
- Tagged chat history, commits, and memory summaries related to this feature

Your job:
1. Briefly summarize what context you received (mention the tagged history/commits you found)
2. Identify any ambiguities or missing information
3. Write 3-8 clear, testable acceptance criteria (bullet list starting with '- [ ]')
4. If critical information is missing, state what questions you would ask the team

Be concise but thorough. Your output feeds directly into the Architect and Developer stages."""),
            ("Architect", "claude", settings.haiku_model, role_ids.get("Sr. Architect"),
             """You are a Senior Software Architect. Based on the PM's acceptance criteria and the original work item context, write a concise technical implementation plan:
- Numbered steps
- Specific files/modules to change or create
- Key functions/classes to add or modify
- Any dependencies or risks to flag
Keep it actionable for a developer."""),
            ("Developer", "claude", claude_model, role_ids.get("Web Developer"),
             """You are a Senior Developer. Implement the work item according to:
- The acceptance criteria (from PM)
- The implementation plan (from Architect)
- The original work item context

Provide specific code changes, file edits, and explanations. If the task requires UI + backend + DB changes, cover all layers. Be concrete and complete."""),
            ("Reviewer", "claude", settings.haiku_model, role_ids.get("Code Reviewer"),
             """You are a Code Reviewer evaluating the Developer's output against the acceptance criteria.

1. Check each acceptance criterion — is it addressed?
2. Note any issues, gaps, or improvements needed
3. Give an overall score 1-10

Respond with valid JSON:
{"passed": true/false, "score": 1-10, "issues": ["...", "..."], "summary": "One sentence verdict"}

If score >= 7, the feature is considered done. If score < 7, list specific issues for the Developer to fix."""),
        ]

        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO pr_graph_workflows (client_id, project, name, description, max_iterations, created_at, updated_at)
                       VALUES (1, %s, %s, %s, 3, NOW(), NOW())
                       ON CONFLICT (client_id, project, name) DO UPDATE SET updated_at=NOW()""",
                    (project, WF_NAME, "4-agent PM → Architect → Developer → Reviewer pipeline for work items"),
                )
                cur.execute(
                    "SELECT id FROM pr_graph_workflows WHERE client_id=1 AND project=%s AND name=%s",
                    (project, WF_NAME),
                )
                wf_id = cur.fetchone()[0]

                # If workflow already existed, update node prompts (refresh with improved prompts)
                if existing_wf_id:
                    for node_name, provider, model, role_id, fallback_prompt in stages:
                        prompt_to_use = "" if role_id else fallback_prompt
                        cur.execute(
                            """UPDATE pr_graph_nodes SET role_prompt=%s, model=%s, updated_at=NOW()
                               WHERE workflow_id=%s AND name=%s AND (role_id IS NULL OR role_id=%s)""",
                            (prompt_to_use, model, wf_id, node_name, role_id or 0),
                        )
                    log.info(f"Refreshed _work_item_pipeline node prompts for project {project}")
                    return wf_id

                node_ids = []
                for i, (node_name, provider, model, role_id, fallback_prompt) in enumerate(stages):
                    cur.execute(
                        """INSERT INTO pr_graph_nodes
                               (workflow_id, name, provider, model, role_id, role_prompt,
                                inject_context, require_approval, approval_msg,
                                position_x, position_y, created_at, updated_at)
                           VALUES (%s,%s,%s,%s,%s,%s, TRUE, FALSE, '', %s, 100, NOW(), NOW())
                           RETURNING id""",
                        (wf_id, node_name, provider, model,
                         role_id, "" if role_id else fallback_prompt,
                         i * 220),
                    )
                    node_ids.append(cur.fetchone()[0])

                # Edges: PM→Arch, Arch→Dev, Dev→Rev, Rev→Dev (loop if score<7)
                edge_defs = [
                    (node_ids[0], node_ids[1], None, ""),
                    (node_ids[1], node_ids[2], None, ""),
                    (node_ids[2], node_ids[3], None, ""),
                    (node_ids[3], node_ids[2],
                     json.dumps({"op": "lt", "field": "score", "value": 7}), "retry"),
                ]
                for src, tgt, cond, label in edge_defs:
                    cur.execute(
                        """INSERT INTO pr_graph_edges
                               (workflow_id, source_node_id, target_node_id, condition, label,
                                created_at, updated_at)
                           VALUES (%s,%s,%s,%s,%s, NOW(), NOW())""",
                        (wf_id, src, tgt, cond, label),
                    )

        log.info(f"Created _work_item_pipeline workflow {wf_id} for project {project}")
        return wf_id
    except Exception as exc:
        log.warning(f"_ensure_pipeline_workflow failed: {exc}")
        return None


# ── Project facts ─────────────────────────────────────────────────────────────

@router.get("/facts")
async def get_project_facts(project: str | None = Query(None)):
    """Return current (valid_until IS NULL) project facts."""
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, fact_key, fact_value, valid_from
                   FROM pr_project_facts
                   WHERE client_id=1 AND project=%s AND valid_until IS NULL
                   ORDER BY fact_key""",
                (p,),
            )
            cols = [d[0] for d in cur.description]
            facts = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                row["id"] = str(row["id"])
                if row.get("valid_from"):
                    row["valid_from"] = row["valid_from"].isoformat()
                facts.append(row)
    return {"facts": facts, "project": p, "total": len(facts)}


# ── Memory items ──────────────────────────────────────────────────────────────

@router.get("/memory-items")
async def get_memory_items(
    project: str | None = Query(None),
    scope:   str | None = Query(None),   # "session" | "feature"
    limit:   int        = Query(20),
):
    f"""Return recent memory_items (distilled session/feature summaries)."""
    _require_db()
    p = _project(project)
    where = ["client_id=1", "project=%s"]
    params: list = [p]
    if scope:
        where.append("scope=%s"); params.append(scope)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT id, scope, scope_ref, content, reviewer_score, created_at
                   FROM pr_memory_items
                   WHERE {' AND '.join(where)}
                   ORDER BY created_at DESC LIMIT %s""",
                params + [limit],
            )
            cols = [d[0] for d in cur.description]
            items = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                row["id"] = str(row["id"])
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
                items.append(row)
    return {"memory_items": items, "project": p, "total": len(items)}
