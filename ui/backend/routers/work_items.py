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
"""
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
    where = ["w.project=%s"]
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
                          ec.color, ec.icon,
                          (SELECT COUNT(*) FROM mng_interaction_tags it
                           WHERE it.work_item_id = w.id) AS interaction_count
                   FROM mng_work_items w
                   LEFT JOIN mng_entity_categories ec ON ec.project=w.project AND ec.name=w.category_name
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
    """Create a new work item."""
    _require_db()
    p = _project(project or body.project)

    # Resolve category_id from mng_entity_categories if it exists
    category_id = None
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM mng_entity_categories WHERE project=%s AND name=%s",
                (p, body.category_name),
            )
            row = cur.fetchone()
            if row:
                category_id = row[0]

            cur.execute(
                """INSERT INTO mng_work_items
                       (project, category_name, category_id, name, description,
                        status, lifecycle_status, due_date, parent_id,
                        acceptance_criteria, implementation_plan, tags)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id, name, category_name, created_at""",
                (p, body.category_name, category_id, body.name, body.description,
                 body.status, body.lifecycle_status, body.due_date or None,
                 body.parent_id or None,
                 body.acceptance_criteria, body.implementation_plan,
                 body.tags),
            )
            r = cur.fetchone()
    return {
        "id": str(r[0]), "name": r[1], "category_name": r[2],
        "created_at": r[3].isoformat(), "project": p,
    }


@router.patch("/{item_id}")
async def patch_work_item(
    item_id: str,
    body: WorkItemPatch,
    project: str | None = Query(None),
    background: BackgroundTasks = BackgroundTasks(),
):
    """Update work item fields. Triggers feature memory synthesis when lifecycle → done."""
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
                f"UPDATE mng_work_items SET {','.join(fields)} WHERE id=%s::uuid AND project=%s RETURNING id",
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
    """Delete a work item and all its interaction_tags."""
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM mng_work_items WHERE id=%s::uuid AND project=%s RETURNING id",
                (item_id, p),
            )
            if not cur.fetchone():
                raise HTTPException(404, "Work item not found")
    return {"ok": True}


# ── Interactions for a work item ──────────────────────────────────────────────

@router.get("/{item_id}/interactions")
async def get_work_item_interactions(
    item_id: str,
    project: str | None = Query(None),
    limit:   int        = Query(20),
):
    """Return recent interactions tagged to this work item."""
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT i.id, i.session_id, i.event_type, i.source_id,
                          i.prompt, i.response, i.phase, i.created_at
                   FROM mng_interaction_tags it
                   JOIN mng_interactions i ON i.id = it.interaction_id
                   WHERE it.work_item_id=%s::uuid AND i.project_id=%s
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
    """Copy feature/bug/task entity_values → work_items. Idempotent."""
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
    """
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name, description, acceptance_criteria FROM mng_work_items WHERE id=%s::uuid AND project=%s",
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
        # Build user_input for the pipeline nodes
        user_input = (
            f"Work item: **{name}**\n"
            f"Description: {desc or 'No description provided.'}\n"
            + (f"Existing criteria:\n{existing_ac}\n" if existing_ac else "")
        )
        try:
            run_id_str = str(uuid.uuid4())
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO mng_graph_runs (id, workflow_id, project, status, user_input)
                           VALUES (%s, %s, %s, 'running', %s)""",
                        (run_id_str, workflow_id, p, user_input),
                    )
                    # Get the int id of the inserted run
                    cur.execute("SELECT id FROM mng_graph_runs WHERE workflow_id=%s AND project=%s ORDER BY id DESC LIMIT 1", (workflow_id, p))
                    run_row = cur.fetchone()
                    run_id = run_row[0] if run_row else None

            # Mark work item running
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE mng_work_items SET agent_status='running', agent_run_id=%s, updated_at=NOW() WHERE id=%s::uuid",
                        (run_id, item_id),
                    )

            # Run in background via graph_runner
            from core.graph_runner import run_graph_workflow

            async def _run_graph():
                try:
                    ctx = await run_graph_workflow(str(workflow_id), user_input, run_id_str, p)
                    ac   = ctx.get("PM") or ctx.get("pm") or ""
                    impl = ctx.get("Architect") or ctx.get("architect") or ""
                    dev  = ctx.get("Developer") or ctx.get("developer") or ""
                    if dev and impl:
                        impl = f"{impl}\n\n## Implementation Output\n{dev}"
                    with db.conn() as conn2:
                        with conn2.cursor() as cur2:
                            cur2.execute(
                                """UPDATE mng_work_items
                                   SET agent_status='done',
                                       acceptance_criteria=COALESCE(NULLIF(%s,''), acceptance_criteria),
                                       implementation_plan=COALESCE(NULLIF(%s,''), implementation_plan),
                                       updated_at=NOW()
                                   WHERE id=%s::uuid""",
                                (ac, impl, item_id),
                            )
                except Exception as exc:
                    log.error(f"run_pipeline graph failed for {item_id}: {exc}")
                    # Fallback: standalone pipeline
                    from core.work_item_pipeline import trigger_work_item_pipeline
                    await trigger_work_item_pipeline(item_id, p, name, desc, existing_ac)

            asyncio.create_task(_run_graph())
            return {"status": "pipeline started", "work_item_id": item_id,
                    "workflow_id": workflow_id, "run_id": run_id, "project": p}

        except Exception as e:
            log.warning(f"Graph pipeline setup failed ({e}), falling back to standalone")

    # Fallback: standalone pipeline (no DB graph)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE mng_work_items SET agent_status='running', updated_at=NOW() WHERE id=%s::uuid",
                (item_id,),
            )
    from core.work_item_pipeline import trigger_work_item_pipeline
    asyncio.create_task(trigger_work_item_pipeline(item_id, p, name, desc, existing_ac))
    return {"status": "pipeline started", "work_item_id": item_id, "project": p}


async def _ensure_pipeline_workflow(project: str) -> int | None:
    """Find or create the '_work_item_pipeline' graph workflow for this project.

    Returns the workflow id (int), or None if DB is unavailable.
    Seeds the workflow with 4 nodes (PM, Architect, Developer, Reviewer) using
    agent_roles if they exist, otherwise inline prompts.
    """
    WF_NAME = "_work_item_pipeline"
    if not db.is_available():
        return None
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM mng_graph_workflows WHERE project=%s AND name=%s",
                    (project, WF_NAME),
                )
                row = cur.fetchone()
                if row:
                    return row[0]

        # Load agent_roles for the 4 stages
        role_ids: dict[str, int] = {}
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT name, id FROM mng_agent_roles
                           WHERE is_active=TRUE AND project='_global'
                           AND name IN ('Product Manager','Sr. Architect','Web Developer','Code Reviewer')"""
                    )
                    for r in cur.fetchall():
                        role_ids[r[0]] = r[1]
        except Exception:
            pass

        claude_model = getattr(settings, "claude_model", settings.haiku_model)

        stages = [
            ("PM",        "claude", settings.haiku_model, role_ids.get("Product Manager"),
             "You are a Product Manager. Write 3-8 clear, testable acceptance criteria (bullet points starting '- [ ]') for the work item."),
            ("Architect", "claude", settings.haiku_model, role_ids.get("Sr. Architect"),
             "You are a Senior Architect. Write a concise technical implementation plan (numbered steps, specific files/functions)."),
            ("Developer", "claude", claude_model,           role_ids.get("Web Developer"),
             "You are a Senior Developer. Implement the work item per the acceptance criteria and implementation plan. Provide detailed code changes."),
            ("Reviewer",  "claude", settings.haiku_model, role_ids.get("Code Reviewer"),
             'You are a Code Reviewer. Review only against the acceptance criteria. Return JSON: {"passed": true/false, "score": 1-10, "issues": []}.'),
        ]

        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO mng_graph_workflows (project, name, description, max_iterations, created_at, updated_at)
                       VALUES (%s, %s, %s, 3, NOW(), NOW()) RETURNING id""",
                    (project, WF_NAME, "4-agent PM → Architect → Developer → Reviewer pipeline for work items"),
                )
                wf_id = cur.fetchone()[0]

                node_ids = []
                for i, (node_name, provider, model, role_id, fallback_prompt) in enumerate(stages):
                    cur.execute(
                        """INSERT INTO mng_graph_nodes
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
                        """INSERT INTO mng_graph_edges
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
                   FROM mng_project_facts
                   WHERE project_id=%s AND valid_until IS NULL
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
    """Return recent memory_items (distilled session/feature summaries)."""
    _require_db()
    p = _project(project)
    where = ["project_id=%s"]
    params: list = [p]
    if scope:
        where.append("scope=%s"); params.append(scope)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT id, scope, scope_ref, content, reviewer_score, created_at
                   FROM mng_memory_items
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
