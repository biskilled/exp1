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

from core.config import settings
from core.database import db
from data.dl_seq import next_seq

# ── SQL ──────────────────────────────────────────────────────────────────────

# Base template — dynamic WHERE clauses are appended in list_work_items
_SQL_LIST_WORK_ITEMS_BASE = (
    """SELECT w.id, w.category_name, w.name, w.description,
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
       WHERE {where}
       ORDER BY w.created_at DESC
       LIMIT %s"""
)

_SQL_INSERT_WORK_ITEM = (
    """INSERT INTO pr_work_items
           (client_id, project, category_name, category_id, name, description,
            status, lifecycle_status, due_date, parent_id,
            acceptance_criteria, implementation_plan, tags, seq_num)
       VALUES (1, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
       ON CONFLICT (client_id, project, category_name, name) DO NOTHING
       RETURNING id, name, category_name, created_at, seq_num"""
)

_SQL_GET_WORK_ITEM = (
    """SELECT w.id, w.category_name, w.name, w.description,
              w.status, w.lifecycle_status, w.due_date,
              w.acceptance_criteria, w.implementation_plan,
              w.agent_run_id, w.agent_status, w.tags,
              w.created_at, w.updated_at, w.seq_num, w.entity_value_id
       FROM pr_work_items w
       WHERE w.client_id=1 AND w.project=%s AND w.id=%s::uuid"""
)

_SQL_DELETE_WORK_ITEM = (
    "DELETE FROM pr_work_items WHERE id=%s::uuid AND client_id=1 AND project=%s RETURNING id"
)

_SQL_GET_WORK_ITEM_BY_SEQ = (
    """SELECT w.id, w.category_name, w.name, w.description,
              w.status, w.lifecycle_status, w.due_date,
              w.acceptance_criteria, w.implementation_plan,
              w.agent_run_id, w.agent_status, w.tags,
              w.created_at, w.updated_at, w.seq_num, w.entity_value_id
       FROM pr_work_items w
       WHERE w.client_id=1 AND w.project=%s AND w.seq_num=%s
       LIMIT 1"""
)

_SQL_GET_CATEGORY_ID = (
    "SELECT id FROM mng_entity_categories WHERE client_id=1 AND project=%s AND name=%s"
)

_SQL_GET_INTERACTIONS = (
    """SELECT i.id, i.session_id, i.event_type, i.source_id,
              i.prompt, i.response, i.phase, i.created_at
       FROM pr_interaction_tags it
       JOIN pr_interactions i ON i.id = it.interaction_id
       WHERE it.work_item_id=%s::uuid AND i.client_id=1 AND i.project=%s
       ORDER BY i.created_at DESC LIMIT %s"""
)

_SQL_GET_FACTS = (
    """SELECT id, fact_key, fact_value, valid_from
       FROM pr_project_facts
       WHERE client_id=1 AND project=%s AND valid_until IS NULL
       ORDER BY fact_key"""
)

_SQL_GET_MEMORY_ITEMS = (
    """SELECT id, scope, scope_ref, content, reviewer_score, created_at
       FROM pr_memory_items
       WHERE {where}
       ORDER BY created_at DESC LIMIT %s"""
)

_SQL_GET_WORK_ITEM_FOR_PIPELINE = (
    "SELECT name, description, acceptance_criteria FROM pr_work_items WHERE id=%s::uuid AND client_id=1 AND project=%s"
)

_SQL_INSERT_PIPELINE_RUN = (
    """INSERT INTO pr_graph_runs (id, client_id, project, workflow_id, status, user_input)
       VALUES (%s, 1, %s, %s, 'running', %s)"""
)

_SQL_UPDATE_WORK_ITEM_RUNNING = (
    "UPDATE pr_work_items SET agent_status='running', agent_run_id=%s::uuid, updated_at=NOW() WHERE id=%s::uuid"
)

_SQL_UPDATE_WORK_ITEM_ERROR = (
    "UPDATE pr_work_items SET agent_status='error', updated_at=NOW() WHERE id=%s::uuid"
)

_SQL_UPDATE_WORK_ITEM_AGENT_RUNNING = (
    "UPDATE pr_work_items SET agent_status='running', updated_at=NOW() WHERE id=%s::uuid"
)

_SQL_UPDATE_WORK_ITEM_DONE = (
    """UPDATE pr_work_items
       SET agent_status='done',
           acceptance_criteria=COALESCE(NULLIF(%s,''), acceptance_criteria),
           implementation_plan=COALESCE(NULLIF(%s,''), implementation_plan),
           updated_at=NOW()
       WHERE id=%s::uuid"""
)

_SQL_UPDATE_WORK_ITEM_LIFECYCLE_DONE = (
    """UPDATE pr_work_items
       SET lifecycle_status='done', updated_at=NOW()
       WHERE id=%s::uuid AND lifecycle_status != 'done'"""
)

_SQL_EXPIRE_PIPELINE_FACT = (
    """UPDATE pr_project_facts SET valid_until=NOW()
       WHERE client_id=1 AND project=%s AND fact_key=%s AND valid_until IS NULL"""
)

_SQL_INSERT_PIPELINE_FACT = (
    "INSERT INTO pr_project_facts (client_id, project, fact_key, fact_value) VALUES (1, %s, %s, %s)"
)

_SQL_INSERT_PIPELINE_INTERACTION = (
    """INSERT INTO pr_interactions
       (id, client_id, project, role, content, source, session_id, work_item_id, created_at)
       VALUES (%s, 1, %s, 'assistant', %s, 'pipeline', %s, %s::uuid, NOW())"""
)

_SQL_INSERT_PIPELINE_INTERACTION_TAG = (
    """INSERT INTO pr_interaction_tags (interaction_id, work_item_id, auto_tagged)
       VALUES (%s::uuid, %s::uuid, TRUE) ON CONFLICT DO NOTHING"""
)

_SQL_PIPELINE_TAGGED_INTERACTIONS = (
    """SELECT i.role, i.content, i.created_at
       FROM pr_interactions i
       JOIN pr_interaction_tags t ON t.interaction_id = i.id
       WHERE t.work_item_id = %s::uuid
       ORDER BY i.created_at DESC LIMIT 30"""
)

_SQL_PIPELINE_TAGGED_COMMITS = (
    """SELECT c.commit_hash, c.message, c.committed_at
       FROM pr_commits c
       JOIN pr_event_tags et ON et.event_id = c.id
       JOIN mng_entity_values ev ON ev.id = et.entity_value_id
       JOIN pr_work_items wi ON wi.entity_value_id = ev.id
       WHERE wi.id = %s::uuid
       ORDER BY c.committed_at DESC LIMIT 10"""
)

_SQL_PIPELINE_MEMORY_ITEMS = (
    """SELECT summary FROM pr_memory_items
       WHERE client_id=1 AND project=%s AND scope_ref=%s
       ORDER BY created_at DESC LIMIT 3"""
)

_SQL_UPSERT_PIPELINE_WORKFLOW = (
    """INSERT INTO pr_graph_workflows
           (client_id, project, name, description, max_iterations,
            created_at, updated_at)
       VALUES (1, %s, %s, %s, 3, NOW(), NOW())
       ON CONFLICT (client_id, project, name) DO UPDATE
           SET updated_at=NOW()"""
)

_SQL_GET_PIPELINE_WORKFLOW_ID = (
    "SELECT id FROM pr_graph_workflows WHERE client_id=1 AND project=%s AND name=%s"
)

_SQL_DELETE_PIPELINE_EDGES = "DELETE FROM pr_graph_edges WHERE workflow_id=%s"
_SQL_DELETE_PIPELINE_NODES = "DELETE FROM pr_graph_nodes WHERE workflow_id=%s"

_SQL_INSERT_PIPELINE_NODE = (
    """INSERT INTO pr_graph_nodes
           (workflow_id, name, provider, model, role_id, role_prompt,
            inject_context, require_approval, approval_msg, stateless,
            position_x, position_y, created_at, updated_at)
       VALUES (%s,%s,%s,%s,%s,%s, TRUE, %s, %s, %s, %s, 100, NOW(), NOW())
       RETURNING id"""
)

_SQL_INSERT_PIPELINE_EDGE = (
    """INSERT INTO pr_graph_edges
           (workflow_id, source_node_id, target_node_id, condition, label,
            created_at, updated_at)
       VALUES (%s,%s,%s, NULL, '', NOW(), NOW())"""
)

_SQL_GET_ALL_AGENT_ROLES = (
    "SELECT id, name FROM mng_agent_roles WHERE client_id=1 AND is_active=TRUE"
)

_SQL_LIST_ENTITY_VALUES_ACTIVE = (
    """SELECT id, name FROM mng_entity_values
       WHERE client_id=1 AND project=%s AND status='active'
       ORDER BY name LIMIT 50"""
)

# ─────────────────────────────────────────────────────────────────────────────

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

    sql = _SQL_LIST_WORK_ITEMS_BASE.format(where=" AND ".join(where))
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params + [limit])
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
            cur.execute(_SQL_GET_CATEGORY_ID, (p, body.category_name))
            row = cur.fetchone()
            if row:
                category_id = row[0]

            seq = next_seq(cur, p, body.category_name)
            cur.execute(
                _SQL_INSERT_WORK_ITEM,
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
        from routers.route_projects import _summarize_feature_memory
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
            cur.execute(_SQL_DELETE_WORK_ITEM, (item_id, p))
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
            cur.execute(_SQL_GET_WORK_ITEM_BY_SEQ, (p, seq_num))
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
            cur.execute(_SQL_GET_INTERACTIONS, (item_id, p, limit))
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
            cur.execute(_SQL_GET_WORK_ITEM_FOR_PIPELINE, (item_id, p))
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
                    cur.execute(_SQL_INSERT_PIPELINE_RUN, (run_id_str, p, workflow_id, user_input))

            # Mark work item running — use run_id_str directly (it's the UUID we just inserted)
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_UPDATE_WORK_ITEM_RUNNING, (run_id_str, item_id))

            # Run in background via graph_runner
            from pipelines.pipeline_graph_runner import run_graph_workflow

            async def _run_graph():
                try:
                    ctx = await run_graph_workflow(str(workflow_id), user_input, run_id_str, p,
                                                   work_item_id=item_id)
                    # If paused at an approval gate, don't finalize yet — wait for user approval
                    if ctx.get("_waiting"):
                        log.info(f"Pipeline {run_id_str} paused for approval at "
                                 f"'{ctx['_waiting'].get('node_name')}' — awaiting user decision")
                        return
                    # Pipeline completed all stages — finalize the work item
                    _finalize_work_item_pipeline(p, item_id, run_id_str, name, ctx)
                except Exception as exc:
                    log.error(f"run_pipeline graph failed for {item_id}: {exc}", exc_info=True)
                    # Mark work item as error so it doesn't stay stuck at 'running'
                    try:
                        with db.conn() as conn_err:
                            with conn_err.cursor() as cur_err:
                                cur_err.execute(_SQL_UPDATE_WORK_ITEM_ERROR, (item_id,))
                    except Exception:
                        pass
                    # Fallback: standalone pipeline
                    try:
                        from pipelines.pipeline_work_items import trigger_work_item_pipeline
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
            cur.execute(_SQL_UPDATE_WORK_ITEM_AGENT_RUNNING, (item_id,))
    from pipelines.pipeline_work_items import trigger_work_item_pipeline
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
                cur.execute(_SQL_PIPELINE_TAGGED_INTERACTIONS, (item_id,))
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
                cur.execute(_SQL_PIPELINE_TAGGED_COMMITS, (item_id,))
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
                cur.execute(_SQL_PIPELINE_MEMORY_ITEMS, (project, item_id))
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
                    _SQL_INSERT_PIPELINE_INTERACTION,
                    (iid, project, content, run_id[:36], item_id),
                )
                cur.execute(_SQL_INSERT_PIPELINE_INTERACTION_TAG, (iid, item_id))
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
                    cur.execute(_SQL_UPDATE_WORK_ITEM_LIFECYCLE_DONE, (item_id,))
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
                cur.execute(_SQL_EXPIRE_PIPELINE_FACT, (project, f"pipeline/{item_name}"))
                # Insert fresh fact
                cur.execute(_SQL_INSERT_PIPELINE_FACT, (project, f"pipeline/{item_name}", summary))
    except Exception as _fe:
        log.debug(f"Could not upsert pipeline fact: {_fe}")


def _finalize_work_item_pipeline(
    project: str, item_id: str, run_id: str, item_name: str, ctx: dict
) -> None:
    """Finalize a completed work item pipeline run.

    Called after all approval gates pass and the pipeline is fully done.
    Updates the work item, saves a project fact, writes to interaction history,
    and closes the feature if the reviewer approved.
    """
    ac   = ctx.get("PM")       or ctx.get("pm")       or ""
    impl = ctx.get("Architect") or ctx.get("architect") or ""
    dev  = ctx.get("Developer") or ctx.get("developer") or ""
    rev  = ctx.get("Reviewer")  or ctx.get("reviewer")  or ""
    if isinstance(ac,   dict): ac   = ac.get("output",   str(ac))
    if isinstance(impl, dict): impl = impl.get("output", str(impl))
    if isinstance(dev,  dict): dev  = dev.get("output",  str(dev))
    if isinstance(rev,  dict): rev  = rev.get("output",  str(rev))
    if dev and impl:
        impl = f"{impl}\n\n## Implementation Output\n{dev}"

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_UPDATE_WORK_ITEM_DONE,
                    (str(ac), str(impl) if impl else "", item_id),
                )
    except Exception as e:
        log.error(f"Could not update work item {item_id} after pipeline: {e}")

    if ac:
        _upsert_pipeline_fact(project, item_name, ac, rev)

    try:
        from routers.route_projects import _summarize_feature_memory
        asyncio.create_task(_summarize_feature_memory(project, item_id))
    except Exception as _me:
        log.debug(f"Memory synthesis skipped: {_me}")

    # Run fact extraction in background after feature memory is synthesized
    try:
        from routers.route_projects import _extract_project_facts
        asyncio.create_task(_extract_project_facts(project))
    except Exception as _fe:
        log.debug(f"Fact extraction skipped: {_fe}")

    _save_pipeline_interaction(project, item_id, run_id, item_name, ac, rev)

    if rev:
        _maybe_close_feature(project, item_id, rev)


async def _ensure_pipeline_workflow(project: str) -> int | None:
    """Find or create the '_work_item_pipeline' workflow with approval gates.

    Stages:  PM (approval) → Architect (approval) → Developer → Reviewer (approval)
    All stages use pre-defined agent roles from the DB (matched via ILIKE).
    Nodes are always deleted and recreated on each trigger so any role/approval
    changes are applied immediately.
    """
    WF_NAME = "_work_item_pipeline"
    if not db.is_available():
        return None
    try:
        # ── 1. Look up agent roles via ILIKE pattern matching ─────────────────
        role_map: dict[str, int | None] = {
            "pm": None, "architect": None, "developer": None, "reviewer": None
        }
        ROLE_PATTERNS: dict[str, list[str]] = {
            "pm":        ["%product manager%", "%pm%"],
            "architect": ["%architect%"],
            "developer": ["%backend developer%", "%backend dev%", "%web developer%", "%developer%"],
            "reviewer":  ["%stateless reviewer%", "%reviewer%"],
        }
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_ALL_AGENT_ROLES)
                    all_roles = cur.fetchall()
            # Match each stage using patterns in order of specificity (most specific first).
            # For each pattern, scan all roles — first matching role wins.
            for key, patterns in ROLE_PATTERNS.items():
                for pat in patterns:
                    substr = pat.strip("%")
                    for rid, rname in all_roles:
                        if substr in (rname or "").lower():
                            role_map[key] = rid
                            break
                    if role_map[key] is not None:
                        break
        except Exception as _re:
            log.warning(f"Role lookup failed: {_re}")

        log.info(f"_work_item_pipeline role_map for {project}: {role_map}")
        claude_model = getattr(settings, "claude_model", settings.haiku_model)

        # ── 2. Stage definitions: role + approval + task instructions ─────────
        stages = [
            {
                "name": "PM", "provider": "claude", "model": settings.haiku_model,
                "role_key": "pm", "require_approval": True, "stateless": False,
                "approval_msg": (
                    "Review the PM analysis and acceptance criteria. "
                    "Approve to proceed to Architect, or Retry to regenerate."
                ),
                "task_instructions": (
                    "## Pipeline Task: Product Manager Analysis\n\n"
                    "You have received tagged context for this work item "
                    "(chat history, commits, prior summaries).\n\n"
                    "Your deliverable:\n"
                    "1. **Context Summary** — Briefly describe what you found "
                    "in the tagged history and commits.\n"
                    "2. **Feature Understanding** — What is this feature? "
                    "What problem does it solve?\n"
                    "3. **Acceptance Criteria** — Write 3-8 clear, testable criteria "
                    "(format: `- [ ] criterion`).\n"
                    "4. **Open Questions** — List anything unclear or missing.\n\n"
                    "> 📋 PM analysis complete. Awaiting approval before Architect phase."
                ),
            },
            {
                "name": "Architect", "provider": "claude", "model": settings.haiku_model,
                "role_key": "architect", "require_approval": True, "stateless": False,
                "approval_msg": (
                    "Review the technical implementation plan. "
                    "Approve to start development, or Retry to regenerate."
                ),
                "task_instructions": (
                    "## Pipeline Task: Technical Architecture\n\n"
                    "Based on the PM's acceptance criteria and the original work item "
                    "context, produce:\n\n"
                    "1. **Implementation Plan** — Numbered steps in execution order.\n"
                    "2. **Files to Change** — Specific paths and what changes are needed.\n"
                    "3. **New Components** — Functions, classes, endpoints, or DB changes.\n"
                    "4. **Risks & Dependencies** — Non-obvious decisions or risks.\n\n"
                    "Be precise. The Developer will follow this plan exactly.\n\n"
                    "> 🏗 Architecture plan complete. Awaiting approval before Developer phase."
                ),
            },
            {
                "name": "Developer", "provider": "claude", "model": claude_model,
                "role_key": "developer", "require_approval": False, "stateless": False,
                "approval_msg": "",
                "task_instructions": (
                    "## Pipeline Task: Implementation\n\n"
                    "Implement the work item based on:\n"
                    "- PM's acceptance criteria\n"
                    "- Architect's implementation plan\n"
                    "- Original work item context\n\n"
                    "Provide complete, runnable code with:\n"
                    "- File paths for each change\n"
                    "- Full function/class implementations (not pseudocode)\n"
                    "- Explanations for non-obvious decisions\n"
                    "- Coverage of all layers (backend, frontend, DB) as needed"
                ),
            },
            {
                "name": "Reviewer", "provider": "claude", "model": settings.haiku_model,
                "role_key": "reviewer", "require_approval": True, "stateless": False,
                "approval_msg": (
                    "Review the code assessment. "
                    "Approve to mark this feature as Done, or Retry for another review cycle."
                ),
                "task_instructions": (
                    "## Pipeline Task: Code Review (Stateless)\n\n"
                    "You are reviewing the Developer's implementation. "
                    "You have no prior conversation history.\n\n"
                    "Review the implementation against the PM's acceptance criteria:\n"
                    "1. Check each criterion — addressed? Yes/No.\n"
                    "2. List specific issues, gaps, or improvements needed.\n"
                    "3. Assign an overall quality score 1–10.\n\n"
                    "Respond with valid JSON only:\n"
                    '{"passed": true/false, "score": 1-10, '
                    '"issues": ["...", "..."], "summary": "One sentence verdict"}\n\n'
                    "Score ≥ 7 = passed. If the user approves this review, "
                    "the work item will be marked Done."
                ),
            },
        ]

        # ── 3. Upsert workflow; delete + recreate nodes so all changes apply ──
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_UPSERT_PIPELINE_WORKFLOW,
                    (project, WF_NAME,
                     "4-agent PM → Architect → Developer → Reviewer pipeline (approval gates)"),
                )
                cur.execute(_SQL_GET_PIPELINE_WORKFLOW_ID, (project, WF_NAME))
                wf_id = cur.fetchone()[0]

                # Always delete and recreate so role assignments + approval flags apply
                cur.execute(_SQL_DELETE_PIPELINE_EDGES, (wf_id,))
                cur.execute(_SQL_DELETE_PIPELINE_NODES, (wf_id,))

                node_ids = []
                for i, stage in enumerate(stages):
                    role_id = role_map.get(stage["role_key"])
                    cur.execute(
                        _SQL_INSERT_PIPELINE_NODE,
                        (wf_id, stage["name"], stage["provider"], stage["model"],
                         role_id, stage["task_instructions"],
                         stage["require_approval"], stage["approval_msg"],
                         stage["stateless"], i * 220),
                    )
                    node_ids.append(cur.fetchone()[0])

                # Linear edges: PM→Arch→Dev→Rev (no automatic loop-back; user controls retry)
                for src, tgt in zip(node_ids, node_ids[1:]):
                    cur.execute(_SQL_INSERT_PIPELINE_EDGE, (wf_id, src, tgt))

        log.info(f"_work_item_pipeline {wf_id} refreshed for {project} — role_map={role_map}")
        return wf_id
    except Exception as exc:
        log.warning(f"_ensure_pipeline_workflow failed: {exc}", exc_info=True)
        return None


# ── Project facts ─────────────────────────────────────────────────────────────

@router.get("/facts")
async def get_project_facts(project: str | None = Query(None)):
    """Return current (valid_until IS NULL) project facts."""
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_FACTS, (p,))
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
    where_parts = ["client_id=1", "project=%s"]
    params: list = [p]
    if scope:
        where_parts.append("scope=%s"); params.append(scope)

    sql = _SQL_GET_MEMORY_ITEMS.format(where=" AND ".join(where_parts))
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params + [limit])
            cols = [d[0] for d in cur.description]
            items = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                row["id"] = str(row["id"])
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
                items.append(row)
    return {"memory_items": items, "project": p, "total": len(items)}
