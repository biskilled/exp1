f"""
migrate_to_memory_layers.py — One-time migration from per-project tables to shared tables.

Migrates:
  1. mng_entity_values (feature/bug/task)  → {tbl_wi}  (INSERT ON CONFLICT DO NOTHING)
  2. events_{p}                        → {tbl_int} (source_id compat; ON CONFLICT DO NOTHING)
  3. history.jsonl                     → {tbl_int} (fill any gaps by source_id)
  4. event_tags_{p}                    → {tbl_itag} (via source_id → interaction + name → work_item)
  5. UPDATE {tbl_int} SET work_item_id from metadata feature field

Run via: POST /admin/migrate-to-memory-layers?project=X
Idempotent — safe to run multiple times.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from config import settings
from core.database import db

log = logging.getLogger(__name__)


async def run_migration(project: str) -> dict[str, int]:
    tbl_wi   = db.project_table("work_items",        project)
    tbl_int  = db.project_table("interactions",      project)
    tbl_itag = db.project_table("interaction_tags",  project)
    tbl_mi   = db.project_table("memory_items",      project)
    tbl_pf   = db.project_table("project_facts",     project)
    """Migrate per-project tables → shared memory layer tables. Returns row counts."""
    if not db.is_available():
        return {"error": "PostgreSQL not available"}

    counts: dict[str, int] = {
        "{tbl_wi}": 0,
        "interactions_from_events": 0,
        "interactions_from_history": 0,
        "{tbl_itag}": 0,
        "work_item_links": 0,
    }

    ev_table = db.project_table("events",      project)
    et_table = db.project_table("event_tags",  project)
    c_table  = db.project_table("commits",     project)

    ws_dir  = Path(settings.workspace_dir) / project / "_system"
    hist    = ws_dir / "history.jsonl"

    def _table_exists(cur, table: str) -> bool:
        cur.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='public' AND table_name=%s",
            (table,),
        )
        return cur.fetchone() is not None

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:

                # ── Step 1: mng_entity_values (feature/bug/task) → {tbl_wi} ─────────
                cur.execute(
                    """SELECT v.id, c.name AS cat_name, c.id AS cat_id,
                              v.name, v.description, v.status, v.lifecycle_status,
                              v.due_date, v.parent_id, v.created_at
                       FROM mng_entity_values v
                       JOIN mng_entity_categories c ON c.id = v.category_id
                       WHERE v.project=%s
                         AND c.name IN ('feature','bug','task')""",
                    (project,),
                )
                ev_rows = cur.fetchall()
                old_id_to_wi: dict[int, str] = {}  # entity_value.id → work_item UUID
                for (old_id, cat_name, cat_id, name, desc, status, lc, due, parent_ev_id, created_at) in ev_rows:
                    cur.execute(
                        f"""INSERT INTO {tbl_wi}
                               (project, category_name, category_id, name, description,
                                status, lifecycle_status, due_date, created_at, updated_at)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT (project, category_name, name) DO NOTHING
                           RETURNING id""",
                        (project, cat_name, cat_id, name, desc or "",
                         status or "active", lc or "idea", due, created_at, created_at),
                    )
                    row = cur.fetchone()
                    if row:
                        old_id_to_wi[old_id] = str(row[0])
                        counts["{tbl_wi}"] += 1
                    else:
                        # Already exists — look up UUID
                        cur.execute(
                            "SELECT id FROM {tbl_wi} WHERE project=%s AND category_name=%s AND name=%s",
                            (project, cat_name, name),
                        )
                        r2 = cur.fetchone()
                        if r2:
                            old_id_to_wi[old_id] = str(r2[0])

                # ── Step 2: events_{p} → {tbl_int} ────────────────────────────
                source_id_to_interaction: dict[str, str] = {}
                if _table_exists(cur, ev_table):
                    cur.execute(
                        f"""SELECT id, event_type, source_id, title, content,
                                   phase, feature, session_id, metadata, created_at
                            FROM {ev_table} ORDER BY created_at""",
                    )
                    for (eid, etype, source_id, title, content, phase, feature, session_id, meta, created_at) in cur.fetchall():
                        if not source_id:
                            continue
                        prompt_text = content or title or ""
                        cur.execute(
                            f"""INSERT INTO {tbl_int}
                                   (project_id, session_id, event_type, source_id,
                                    prompt, phase, metadata, created_at)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                               ON CONFLICT DO NOTHING
                               RETURNING id""",
                            (project, session_id, etype or "prompt", source_id,
                             prompt_text[:4000], phase, json.dumps(meta) if isinstance(meta, dict) else (meta or "{}"),
                             created_at),
                        )
                        r = cur.fetchone()
                        if r:
                            source_id_to_interaction[source_id] = str(r[0])
                            counts["interactions_from_events"] += 1
                        else:
                            cur.execute(
                                "SELECT id FROM {tbl_int} WHERE project_id=%s AND source_id=%s LIMIT 1",
                                (project, source_id),
                            )
                            r2 = cur.fetchone()
                            if r2:
                                source_id_to_interaction[source_id] = str(r2[0])

                # ── Step 3: history.jsonl → {tbl_int} (fill gaps) ──────────────
                if hist.exists():
                    for line in hist.read_text().splitlines():
                        if not line.strip():
                            continue
                        try:
                            e = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        ts = e.get("ts", "")
                        if not ts or ts in source_id_to_interaction:
                            continue  # already imported
                        if not e.get("user_input"):
                            continue
                        cur.execute(
                            f"""INSERT INTO {tbl_int}
                                   (project_id, session_id, event_type, source_id, prompt, response, phase, metadata, created_at)
                               VALUES (%s,%s,'prompt',%s,%s,%s,%s,%s,%s::timestamptz)
                               ON CONFLICT DO NOTHING
                               RETURNING id""",
                            (project,
                             e.get("session_id") or e.get("session") or None,
                             ts,
                             (e.get("user_input") or "")[:4000],
                             (e.get("output") or "")[:4000],
                             e.get("phase"),
                             json.dumps({"provider": e.get("provider"), "source": e.get("source")}),
                             ts),
                        )
                        r = cur.fetchone()
                        if r:
                            source_id_to_interaction[ts] = str(r[0])
                            counts["interactions_from_history"] += 1

                # ── Step 4: event_tags_{p} → {tbl_itag} ────────────────────
                if _table_exists(cur, et_table) and source_id_to_interaction and old_id_to_wi:
                    cur.execute(
                        f"""SELECT et.event_id, e.source_id, et.entity_value_id, et.auto_tagged
                            FROM {et_table} et
                            JOIN {ev_table} e ON e.id = et.event_id""",
                    )
                    for (event_id, source_id, ev_val_id, auto_tagged) in cur.fetchall():
                        interaction_id = source_id_to_interaction.get(source_id or "")
                        work_item_id   = old_id_to_wi.get(ev_val_id)
                        if not interaction_id or not work_item_id:
                            continue
                        cur.execute(
                            f"""INSERT INTO {tbl_itag} (interaction_id, work_item_id, auto_tagged)
                               VALUES (%s::uuid, %s::uuid, %s) ON CONFLICT DO NOTHING""",
                            (interaction_id, work_item_id, auto_tagged),
                        )
                        counts["{tbl_itag}"] += cur.rowcount

                # ── Step 5: backfill work_item_id from metadata feature field ─────
                cur.execute(
                    f"""UPDATE {tbl_int} i
                          SET work_item_id = w.id
                         FROM {tbl_wi} w
                        WHERE i.project_id = w.project
                          AND i.metadata->>'feature' = w.name
                          AND i.work_item_id IS NULL
                          AND i.project_id = %s""",
                    (project,),
                )
                counts["work_item_links"] = cur.rowcount

        log.info(f"Migration for '{project}' complete: {counts}")
    except Exception as exc:
        log.error(f"Migration failed for '{project}': {exc}")
        counts["error"] = str(exc)

    return counts
