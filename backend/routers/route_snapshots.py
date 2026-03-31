"""
route_snapshots.py — 4-layer feature snapshot generation endpoint.

Generates structured knowledge artifacts from memory events:
  1. Load all mem_ai_events for a tag
  2. Call Sonnet with memory_feature_snapshot prompt from mng_system_roles
  3. Parse JSON → upsert mem_ai_features
  4. Extract project_facts → upsert mem_ai_project_facts
  5. Embed requirements+action_items → mem_ai_features.embedding
  6. Mark contributing mem_ai_events.processed_at = NOW()

Endpoints:
    POST /projects/{project}/snapshot/{tag_name}
    GET  /projects/{project}/snapshot/{tag_name}
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Optional

from fastapi import APIRouter, HTTPException

from core.config import settings
from core.database import db

log = logging.getLogger(__name__)

router = APIRouter()

# ── SQL ──────────────────────────────────────────────────────────────────────

_SQL_GET_TAG_ID = """
    SELECT id FROM planner_tags
    WHERE client_id = 1 AND project = %s AND name = %s
    LIMIT 1
"""

_SQL_GET_MEMORY_EVENTS = """
    SELECT me.id, me.source_type, me.source_id, me.session_id, me.content, me.importance
    FROM mem_ai_events me
    JOIN mem_ai_tags mt ON mt.event_id = me.id
    WHERE mt.tag_id = %s::uuid
      AND me.client_id = 1 AND me.project = %s
    ORDER BY me.created_at
"""

_SQL_GET_SYSTEM_ROLE = """
    SELECT content FROM mng_system_roles
    WHERE client_id = 1 AND name = %s AND is_active = TRUE
    LIMIT 1
"""

_SQL_UPSERT_SNAPSHOT = """
    INSERT INTO mem_ai_features
        (client_id, project, tag_id, work_item_type, requirements, action_items,
         design, code_summary, prompt_ids, commit_hashes, file_paths, design_refs,
         embedding, is_reusable, created_at, updated_at)
    VALUES (1, %s, %s::uuid, %s, %s, %s, %s::jsonb, %s::jsonb,
            %s, %s, %s, %s,
            %s, %s, NOW(), NOW())
    ON CONFLICT (client_id, project, tag_id)
    DO UPDATE SET
        requirements  = EXCLUDED.requirements,
        action_items  = EXCLUDED.action_items,
        design        = EXCLUDED.design,
        code_summary  = EXCLUDED.code_summary,
        prompt_ids    = EXCLUDED.prompt_ids,
        commit_hashes = EXCLUDED.commit_hashes,
        file_paths    = EXCLUDED.file_paths,
        design_refs   = EXCLUDED.design_refs,
        embedding     = EXCLUDED.embedding,
        is_reusable   = EXCLUDED.is_reusable,
        updated_at    = NOW()
    RETURNING id
"""

_SQL_MARK_EVENTS_PROCESSED = """
    UPDATE mem_ai_events SET processed_at = NOW()
    WHERE id = ANY(%s::uuid[]) AND processed_at IS NULL
"""

_SQL_GET_SNAPSHOT = """
    SELECT fs.id, fs.tag_id, fs.work_item_type, fs.requirements, fs.action_items,
           fs.design, fs.code_summary, fs.prompt_ids, fs.commit_hashes,
           fs.file_paths, fs.is_reusable, fs.created_at, fs.updated_at,
           t.name AS tag_name
    FROM mem_ai_features fs
    JOIN planner_tags t ON t.id = fs.tag_id
    WHERE fs.client_id = 1 AND fs.project = %s AND t.name = %s
    LIMIT 1
"""

_SQL_UPSERT_FACT = """
    INSERT INTO mem_ai_project_facts (client_id, project, fact_key, fact_value, valid_from)
    VALUES (1, %s, %s, %s, NOW())
    ON CONFLICT (client_id, project, fact_key) WHERE valid_until IS NULL
    DO UPDATE SET fact_value = EXCLUDED.fact_value
"""

_DEFAULT_SNAPSHOT_PROMPT = (
    "Produce a 4-layer feature snapshot as JSON with these keys: "
    "requirements (string), action_items (string), "
    "design (object: {high_level, low_level, patterns_used}), "
    "code_summary (object: {files, key_classes, key_methods, dependencies_added, dependencies_removed}). "
    "Base your answer only on the provided evidence. Return ONLY valid JSON."
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_db():
    if not db.is_available():
        raise HTTPException(status_code=503, detail="Database not available")


async def _call_sonnet(system_prompt: str, user_message: str) -> str:
    try:
        from data.dl_api_keys import get_key
        api_key = get_key("claude") or get_key("anthropic")
        if not api_key:
            raise ValueError("No Claude API key configured")
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key)
        resp = await client.messages.create(
            model=settings.claude_model,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return resp.content[0].text if resp.content else ""
    except Exception as e:
        log.warning(f"_call_sonnet error: {e}")
        return ""


async def _embed_text(text: str) -> Optional[list]:
    try:
        from memory.mem_embeddings import get_embedding
        return await get_embedding(text)
    except Exception:
        return None


def _parse_snapshot_json(text: str) -> dict:
    clean = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")
    m = re.search(r"\{[\s\S]*\}", clean)
    if not m:
        return {}
    try:
        return json.loads(m.group())
    except Exception:
        return {}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/projects/{project}/snapshot/{tag_name}")
async def generate_snapshot(project: str, tag_name: str):
    """Generate a 4-layer feature snapshot for a tag from its memory events."""
    _require_db()

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_TAG_ID, (project, tag_name))
            tag_row = cur.fetchone()
    if not tag_row:
        raise HTTPException(status_code=404, detail=f"Tag '{tag_name}' not found in project '{project}'")
    tag_id = str(tag_row[0])

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_MEMORY_EVENTS, (tag_id, project))
            events = cur.fetchall()

    if not events:
        raise HTTPException(
            status_code=422,
            detail=f"No memory events found for tag '{tag_name}'. Run a few sessions first.",
        )

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_SYSTEM_ROLE, ("memory_feature_snapshot",))
            role_row = cur.fetchone()
    system_prompt = role_row[0] if role_row else _DEFAULT_SNAPSHOT_PROMPT

    by_type: dict[str, list[str]] = {}
    event_ids: list[str] = []
    for ev_id, src_type, src_id, session_id, content, importance in events:
        event_ids.append(str(ev_id))
        by_type.setdefault(src_type, []).append(f"[importance={importance}] {content}")

    sections = []
    for stype, items in by_type.items():
        sections.append(f"## {stype.replace('_', ' ').title()}\n" + "\n".join(f"- {i}" for i in items))
    user_message = (
        f"Feature: **{tag_name}**\nProject: {project}\n\n"
        + "\n\n".join(sections)
    )

    raw = await _call_sonnet(system_prompt, user_message)
    if not raw:
        raise HTTPException(status_code=502, detail="LLM returned empty response")

    parsed = _parse_snapshot_json(raw)
    if not parsed:
        raise HTTPException(status_code=502, detail=f"Could not parse LLM JSON: {raw[:200]}")

    # Extract AI-detected relations before consuming the rest of the dict
    ai_relations: list[dict] = parsed.pop("relations", []) or []

    embed_text = " ".join(filter(None, [
        parsed.get("requirements", ""),
        parsed.get("action_items", ""),
    ]))
    embedding = await _embed_text(embed_text) if embed_text.strip() else None

    design = parsed.get("design", {})
    code_summary = parsed.get("code_summary", {})
    file_paths = list(code_summary.get("files", []) if isinstance(code_summary, dict) else [])

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _SQL_UPSERT_SNAPSHOT,
                (
                    project, tag_id, "feature",
                    parsed.get("requirements", ""),
                    parsed.get("action_items", ""),
                    json.dumps(design),
                    json.dumps(code_summary),
                    None,           # prompt_ids
                    None,           # commit_hashes
                    file_paths or None,
                    None,           # design_refs
                    embedding,
                    False,
                ),
            )
            snap_row = cur.fetchone()
            snap_id = str(snap_row[0]) if snap_row else None

            if event_ids:
                cur.execute(_SQL_MARK_EVENTS_PROCESSED, (event_ids,))

    facts_extracted = 0
    if isinstance(design, dict) and design.get("patterns_used"):
        patterns = design["patterns_used"]
        patterns_str = ", ".join(str(p) for p in patterns) if isinstance(patterns, list) else str(patterns)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        _SQL_UPSERT_FACT,
                        (project, f"feature.{tag_name}.patterns", patterns_str),
                    )
            facts_extracted += 1
        except Exception as e:
            log.debug(f"fact upsert error: {e}")

    # Upsert AI-detected relations (source='ai_snapshot')
    relations_upserted = 0
    if ai_relations:
        try:
            from memory.memory_tagging import MemoryTagging
            relations_upserted = MemoryTagging().upsert_relations_from_list(
                project, ai_relations, source="ai_snapshot"
            )
        except Exception as e:
            log.debug(f"relation upsert error: {e}")

    log.info(f"Snapshot generated for '{tag_name}' in '{project}': "
             f"{len(event_ids)} events, {facts_extracted} facts, "
             f"{relations_upserted} relations")

    # Regenerate feature CLAUDE.md in background after snapshot
    async def _regen():
        try:
            from memory.memory_files import MemoryFiles
            mf = MemoryFiles()
            await asyncio.get_event_loop().run_in_executor(
                None, mf.write_feature_files, project, tag_name
            )
        except Exception as e:
            log.debug(f"snapshot regen error: {e}")
    asyncio.create_task(_regen())

    return {
        "snapshot_id":        snap_id,
        "tag_name":           tag_name,
        "project":            project,
        "requirements":       parsed.get("requirements", ""),
        "action_items":       parsed.get("action_items", ""),
        "design":             design,
        "code_summary":       code_summary,
        "events_processed":   len(event_ids),
        "facts_extracted":    facts_extracted,
        "relations_upserted": relations_upserted,
        "relations":          ai_relations,
    }


@router.get("/projects/{project}/snapshot/{tag_name}")
async def get_snapshot(project: str, tag_name: str):
    """Retrieve an existing feature snapshot."""
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_SNAPSHOT, (project, tag_name))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"No snapshot found for '{tag_name}'")
    return {
        "id":             str(row[0]),
        "tag_id":         str(row[1]),
        "tag_name":       row[13],
        "work_item_type": row[2],
        "requirements":   row[3],
        "action_items":   row[4],
        "design":         row[5],
        "code_summary":   row[6],
        "prompt_ids":     [str(x) for x in (row[7] or [])],
        "commit_hashes":  row[8] or [],
        "file_paths":     row[9] or [],
        "is_reusable":    row[10],
        "created_at":     row[11].isoformat() if row[11] else None,
        "updated_at":     row[12].isoformat() if row[12] else None,
    }
