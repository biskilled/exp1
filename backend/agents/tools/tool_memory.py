"""
tool_memory.py — Agent tools for reading project memory, history, and tag context.

Provides direct DB access (no HTTP round-trip) for pipeline ReAct agents:
  - search_memory     : text search over mem_mrr_prompts (prompt/response content)
  - get_recent_history: latest prompts from mem_mrr_prompts (with optional tag filter)
  - get_project_facts : current facts from mem_ai_project_facts
  - get_tag_context   : full context for a tag — snapshot, relations
  - search_features   : search planner_tags by tag name or semantic query

Assigned to research-oriented roles (PM, Architect, Reviewer) so they can reason
over past decisions without leaving the agentic loop.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# ── Embedding helper (sync — for use in sync tool handlers) ───────────────────

def _embed_sync(text: str) -> list[float] | None:
    """Synchronous embedding via OpenAI text-embedding-3-small. Returns None on failure."""
    try:
        from data.dl_api_keys import get_key
        import openai
        key = get_key("openai") or get_key("openai_key")
        if not key:
            return None
        client = openai.OpenAI(api_key=key)
        resp = client.embeddings.create(model="text-embedding-3-small", input=text[:8000])
        return resp.data[0].embedding
    except Exception as e:
        log.debug(f"_embed_sync error: {e}")
        return None


def _vec_str(vec: list[float]) -> str:
    return f"[{','.join(str(x) for x in vec)}]"


def _get_active_project() -> str:
    """Best-effort: read from session_state.json or fall back to env."""
    import os
    project = os.environ.get("ACTIVE_PROJECT", "")
    if not project:
        state_path = Path.home() / ".aicli" / "session_state.json"
        if state_path.exists():
            try:
                project = json.loads(state_path.read_text()).get("project", "")
            except Exception:
                pass
    return project or "aicli"


# ── Tool definitions ───────────────────────────────────────────────────────────

MEMORY_TOOL_DEFS: list[dict] = [
    {
        "name": "search_memory",
        "description": (
            "Text search over the project's raw prompt/response history (mem_mrr_prompts). "
            "Returns matching entries from past AI sessions. "
            "Optionally filter by feature tag name to scope results to a specific tag."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query":   {"type": "string",  "description": "Natural language search query"},
                "project": {"type": "string",  "description": "Project name (default: active)"},
                "limit":   {"type": "integer", "description": "Max results (default 6)"},
                "feature": {"type": "string",  "description": "Filter by planner_tag name (optional)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_recent_history",
        "description": (
            "Retrieve recent raw prompt/response pairs from mem_mrr_prompts. "
            "Use 'feature' to scope results to a specific tag."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string",  "description": "Project name"},
                "limit":   {"type": "integer", "description": "Max entries (default 10)"},
                "feature": {"type": "string",  "description": "Filter by feature tag name (optional)"},
            },
        },
    },
    {
        "name": "get_project_facts",
        "description": (
            "Get all current durable architectural facts from mem_ai_project_facts "
            "(valid_until IS NULL). Returns key-value pairs like 'auth_method: JWT + bcrypt'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project name"},
            },
        },
    },
    {
        "name": "get_tag_context",
        "description": (
            "Return comprehensive context for a specific feature/bug/task tag. "
            "Includes: tag description + requirements, recent prompts tagged to this feature, "
            "feature snapshot (requirements, action_items, design, code_summary), "
            "and tag relations (depends_on, blocks, etc.). "
            "Call this FIRST when starting work on any feature or bug — the PM agent "
            "uses this to orient on full history before creating acceptance criteria."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tag_name": {"type": "string",  "description": "Tag name, e.g. 'auth-refactor', 'retry-dashboard'"},
                "project":  {"type": "string",  "description": "Project name"},
                "limit":    {"type": "integer", "description": "Max AI events to return (default 8)"},
            },
            "required": ["tag_name"],
        },
    },
    {
        "name": "search_features",
        "description": (
            "Search planner_tags (feature snapshots) by tag name or semantic query. "
            "Returns requirements, action_items, design overview, and affected files for matching features."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query":   {"type": "string",  "description": "Tag name or semantic query"},
                "project": {"type": "string",  "description": "Project name"},
                "limit":   {"type": "integer", "description": "Max results (default 5)"},
            },
            "required": ["query"],
        },
    },
]

# ── Handlers ───────────────────────────────────────────────────────────────────

def _handle_search_memory(args: dict) -> str:
    query   = args.get("query", "")
    project = args.get("project") or _get_active_project()
    limit   = int(args.get("limit", 6))
    feature = args.get("feature")

    results: list[str] = []

    try:
        from core.database import db
        if db.is_available():
            project_id = db.get_or_create_project_id(project)
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # ── Text search over raw prompt/response history ──────
                    if feature:
                        cur.execute(
                            """SELECT p.prompt, p.response, p.created_at
                               FROM mem_mrr_prompts p
                               WHERE p.project_id=%s
                                 AND (p.prompt ILIKE %s OR p.response ILIKE %s)
                                 AND p.tags @> %s::jsonb
                               ORDER BY p.created_at DESC LIMIT %s""",
                            (project_id, f"%{query}%", f"%{query}%",
                             json.dumps({"feature": feature}), limit),
                        )
                    else:
                        cur.execute(
                            """SELECT prompt, response, created_at
                               FROM mem_mrr_prompts
                               WHERE project_id=%s
                                 AND (prompt ILIKE %s OR response ILIKE %s)
                               ORDER BY created_at DESC LIMIT %s""",
                            (project_id, f"%{query}%", f"%{query}%", limit),
                        )
                    for row in cur.fetchall():
                        ts = row[2].strftime("%Y-%m-%d") if row[2] else "?"
                        q_snippet = (row[0] or "")[:200]
                        r_snippet = (row[1] or "")[:200]
                        results.append(f"[{ts}] Q: {q_snippet}\n  A: {r_snippet}")
    except Exception as e:
        log.debug(f"search_memory DB error: {e}")

    # JSONL fallback (DB unavailable)
    if not results:
        try:
            cfg_path = Path.home() / ".aicli" / "config.json"
            workspace = "workspace"
            if cfg_path.exists():
                workspace = json.loads(cfg_path.read_text()).get("workspace_dir", workspace)
            history_path = Path(workspace) / project / "_system" / "history.jsonl"
            if history_path.exists():
                query_lower = query.lower()
                for line in reversed(history_path.read_text().splitlines()[-500:]):
                    try:
                        entry = json.loads(line)
                        content = (entry.get("content") or entry.get("message") or "")
                        if query_lower in content.lower():
                            ts = (entry.get("timestamp") or "?")[:10]
                            results.append(f"[{ts}] {entry.get('role','?')}: {content[:300]}")
                            if len(results) >= limit:
                                break
                    except Exception:
                        continue
        except Exception as e:
            log.debug(f"search_memory JSONL fallback error: {e}")

    if not results:
        return f"No results found for: {query}"
    return "\n\n".join(results)


def _handle_get_recent_history(args: dict) -> str:
    project = args.get("project") or _get_active_project()
    limit   = int(args.get("limit", 10))
    feature = args.get("feature")

    results: list[str] = []

    try:
        from core.database import db
        if db.is_available():
            project_id = db.get_or_create_project_id(project)
            with db.conn() as conn:
                with conn.cursor() as cur:
                    if feature:
                        cur.execute(
                            """SELECT p.prompt, p.response, p.created_at
                               FROM mem_mrr_prompts p
                               WHERE p.project_id=%s
                                 AND %s = ANY(p.tags)
                               ORDER BY p.created_at DESC LIMIT %s""",
                            (project_id, f"feature:{feature}", limit),
                        )
                    else:
                        cur.execute(
                            """SELECT prompt, response, created_at
                               FROM mem_mrr_prompts
                               WHERE project_id=%s
                               ORDER BY created_at DESC LIMIT %s""",
                            (project_id, limit),
                        )
                    for row in cur.fetchall():
                        ts = row[2].strftime("%Y-%m-%d %H:%M") if row[2] else "?"
                        results.append(f"[{ts}] Q: {(row[0] or '')[:300]}")
    except Exception as e:
        log.debug(f"get_recent_history DB error: {e}")

    # JSONL fallback
    if not results:
        try:
            cfg_path = Path.home() / ".aicli" / "config.json"
            workspace = "workspace"
            if cfg_path.exists():
                workspace = json.loads(cfg_path.read_text()).get("workspace_dir", workspace)
            history_path = Path(workspace) / project / "_system" / "history.jsonl"
            if history_path.exists():
                for line in reversed(history_path.read_text().splitlines()[-(limit * 2):]):
                    try:
                        entry = json.loads(line)
                        content = (entry.get("content") or entry.get("message") or "")[:400]
                        ts = (entry.get("timestamp") or "?")[:16]
                        results.append(f"[{ts}] {entry.get('role','?')}: {content}")
                        if len(results) >= limit:
                            break
                    except Exception:
                        continue
        except Exception as e:
            log.debug(f"get_recent_history JSONL fallback: {e}")

    return "\n\n".join(results) if results else "No recent history found."


def _handle_get_project_facts(args: dict) -> str:
    project = args.get("project") or _get_active_project()

    try:
        from core.database import db
        if db.is_available():
            project_id = db.get_or_create_project_id(project)
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT fact_key, fact_value, category FROM mem_ai_project_facts
                           WHERE project_id=%s AND valid_until IS NULL
                           ORDER BY category NULLS LAST, fact_key""",
                        (project_id,),
                    )
                    rows = cur.fetchall()
                    if rows:
                        lines = []
                        cur_cat = None
                        for k, v, cat in rows:
                            if cat and cat != cur_cat:
                                lines.append(f"\n[{cat}]")
                                cur_cat = cat
                            lines.append(f"  {k}: {v}")
                        return "Project Facts:\n" + "\n".join(lines)
    except Exception as e:
        log.debug(f"get_project_facts DB error: {e}")

    # Fallback: project_state.json
    try:
        cfg_path = Path.home() / ".aicli" / "config.json"
        workspace = "workspace"
        if cfg_path.exists():
            workspace = json.loads(cfg_path.read_text()).get("workspace_dir", workspace)
        state_path = Path(workspace) / project / "_system" / "project_state.json"
        if state_path.exists():
            state = json.loads(state_path.read_text())
            facts = state.get("key_decisions", state.get("facts", {}))
            if isinstance(facts, list):
                return "Project Key Decisions:\n" + "\n".join(f"- {f}" for f in facts)
            if isinstance(facts, dict) and facts:
                return "Project Facts:\n" + "\n".join(f"{k}: {v}" for k, v in facts.items())
    except Exception as e:
        log.debug(f"get_project_facts JSON fallback: {e}")

    return "No project facts found."


def _handle_get_tag_context(args: dict) -> str:
    tag_name = args.get("tag_name", "").strip()
    project  = args.get("project") or _get_active_project()
    limit    = int(args.get("limit", 8))

    if not tag_name:
        return "Error: tag_name is required."

    try:
        from core.database import db
        if not db.is_available():
            return "Database not available."

        project_id = db.get_or_create_project_id(project)
        with db.conn() as conn:
            with conn.cursor() as cur:
                # ── Tag + meta ────────────────────────────────────────────
                cur.execute(
                    """SELECT t.id, t.name, t.status, t.status,
                              c.name AS category,
                              t.description, t.requirements, t.due_date, t.priority
                       FROM planner_tags t
                       LEFT JOIN mng_tags_categories c ON c.id = t.category_id
                       WHERE t.project_id=%s AND t.name=%s
                       LIMIT 1""",
                    (project_id, tag_name),
                )
                tag_row = cur.fetchone()
                if not tag_row:
                    return f"Tag '{tag_name}' not found in project '{project}'."
                tag_id = str(tag_row[0])

                lines = [
                    f"=== Tag: {tag_row[1]} ===",
                    f"Category: {tag_row[4] or 'unset'}  |  Status: {tag_row[2]}",
                ]
                if tag_row[5]:
                    lines.append(f"Description: {tag_row[5]}")
                if tag_row[6]:
                    lines.append(f"Requirements: {tag_row[6][:500]}")
                if tag_row[7]:
                    lines.append(f"Due: {tag_row[7]}  Priority: {tag_row[8] or 3}")

                # ── Feature snapshot (inline on planner_tags) ─────────────
                cur.execute(
                    """SELECT requirements, action_items, design, code_summary, updated_at
                       FROM planner_tags
                       WHERE project_id=%s AND id=%s::uuid
                       LIMIT 1""",
                    (project_id, tag_id),
                )
                snap = cur.fetchone()
                if snap:
                    lines.append("\n--- Feature Snapshot ---")
                    if snap[0]:
                        lines.append(f"Requirements: {snap[0][:600]}")
                    if snap[1]:
                        lines.append(f"Action Items: {snap[1][:400]}")
                    if snap[2]:
                        design = snap[2] if isinstance(snap[2], dict) else {}
                        hl = design.get("high_level", "")
                        if hl:
                            lines.append(f"Design: {hl[:300]}")
                    if snap[3]:
                        cs = snap[3] if isinstance(snap[3], dict) else {}
                        files = cs.get("files", [])
                        if files:
                            lines.append(f"Key files: {', '.join(files[:8])}")

                # ── Recent prompts for this tag ───────────────────────────
                cur.execute(
                    """SELECT p.prompt, p.response, p.created_at
                       FROM mem_mrr_prompts p
                       WHERE p.project_id=%s
                         AND p.tags @> %s::jsonb
                       ORDER BY p.created_at DESC
                       LIMIT %s""",
                    (project_id, json.dumps({"feature": tag_name}), limit),
                )
                prompts = cur.fetchall()
                if prompts:
                    lines.append(f"\n--- Recent Prompts (last {len(prompts)}) ---")
                    for pr in prompts:
                        ts = pr[2].strftime("%Y-%m-%d") if pr[2] else "?"
                        q_snippet = (pr[0] or "")[:200]
                        lines.append(f"[{ts}] Q: {q_snippet}")

                # ── Relations ─────────────────────────────────────────────
                cur.execute(
                    """SELECT r.relation, r.note,
                              tf.name AS from_name, tt.name AS to_name
                       FROM mng_ai_tags_relations r
                       JOIN planner_tags tf ON tf.id = r.from_tag_id
                       JOIN planner_tags tt ON tt.id = r.to_tag_id
                       WHERE r.from_tag_id=%s::uuid OR r.to_tag_id=%s::uuid""",
                    (tag_id, tag_id),
                )
                rels = cur.fetchall()
                if rels:
                    lines.append("\n--- Relations ---")
                    for rel in rels:
                        note = f" ({rel[1]})" if rel[1] else ""
                        lines.append(f"  {rel[2]} --[{rel[0]}]--> {rel[3]}{note}")

        return "\n".join(lines)

    except Exception as e:
        log.debug(f"get_tag_context error: {e}")
        return f"Error fetching context for '{tag_name}': {e}"


def _handle_search_features(args: dict) -> str:
    query   = args.get("query", "").strip()
    project = args.get("project") or _get_active_project()
    limit   = int(args.get("limit", 5))

    if not query:
        return "Error: query is required."

    results: list[str] = []

    try:
        from core.database import db
        if not db.is_available():
            return "Database not available."

        project_id = db.get_or_create_project_id(project)
        with db.conn() as conn:
            with conn.cursor() as cur:
                # Text search on name + description (embedding column dropped in m027)
                cur.execute(
                    """SELECT t.name, t.requirements, t.action_items, t.description,
                              t.updated_at, t.status
                       FROM planner_tags t
                       WHERE t.project_id=%s
                         AND (t.name ILIKE %s OR t.description ILIKE %s
                              OR t.requirements ILIKE %s)
                       ORDER BY t.updated_at DESC LIMIT %s""",
                    (project_id, f"%{query}%", f"%{query}%", f"%{query}%", limit),
                )
                rows = cur.fetchall()
                for row in rows:
                    ts   = row[4].strftime("%Y-%m-%d") if row[4] else "?"
                    reqs = (row[1] or "")[:300]
                    acts = (row[2] or "")[:200]
                    desc = (row[3] or "")[:120]
                    status = row[5] or "open"
                    block = [
                        f"[Feature: {row[0]}] [{status}] updated {ts}",
                    ]
                    if desc:
                        block.append(f"  Description: {desc}")
                    if reqs:
                        block.append(f"  Requirements: {reqs}")
                    if acts:
                        block.append(f"  Action Items: {acts}")
                    results.append("\n".join(block))
    except Exception as e:
        log.debug(f"search_features error: {e}")
        return f"Error searching features: {e}"

    if not results:
        return f"No feature snapshots found matching: {query}"
    return "\n\n".join(results)


# ── Handler map ────────────────────────────────────────────────────────────────

MEMORY_HANDLERS: dict[str, callable] = {
    "search_memory":      _handle_search_memory,
    "get_recent_history": _handle_get_recent_history,
    "get_project_facts":  _handle_get_project_facts,
    "get_tag_context":    _handle_get_tag_context,
    "search_features":    _handle_search_features,
}
