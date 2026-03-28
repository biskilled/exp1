"""
tool_memory.py — Agent tools for reading project memory and history.

Provides direct DB/filesystem access (no HTTP round-trip) for:
  - search_memory: cosine similarity over pr_embeddings + text search in pr_events
  - get_recent_history: latest prompts from pr_prompts
  - get_project_facts: reads project_state.json durable facts

These tools are assigned to research-oriented roles (PM, Architect, Reviewer)
so they can reason over past decisions without leaving the agentic loop.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# ── Tool definitions (Claude tool_use JSON schema format) ─────────────────────

MEMORY_TOOL_DEFS: list[dict] = [
    {
        "name": "search_memory",
        "description": (
            "Search the project knowledge base using text similarity. "
            "Returns relevant past interactions, decisions, and code chunks."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query":   {"type": "string", "description": "Search query"},
                "project": {"type": "string", "description": "Project name (default: active project)"},
                "limit":   {"type": "integer", "description": "Max results (default 5)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_recent_history",
        "description": "Retrieve recent interaction history for the project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project name"},
                "limit":   {"type": "integer", "description": "Max entries (default 10)"},
                "feature": {"type": "string", "description": "Filter by feature tag (optional)"},
            },
        },
    },
    {
        "name": "get_project_facts",
        "description": "Get durable architectural facts for the project from project_state.json.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project name"},
            },
        },
    },
]

# ── Handlers ──────────────────────────────────────────────────────────────────

def _get_active_project() -> str:
    """Best-effort: read from session_state.json or fall back to env."""
    import os
    from pathlib import Path
    project = os.environ.get("ACTIVE_PROJECT", "")
    if not project:
        state_path = Path.home() / ".aicli" / "session_state.json"
        if state_path.exists():
            try:
                project = json.loads(state_path.read_text()).get("project", "")
            except Exception:
                pass
    return project or "aicli"


def _handle_search_memory(args: dict) -> str:
    query   = args.get("query", "")
    project = args.get("project") or _get_active_project()
    limit   = int(args.get("limit", 5))

    results: list[str] = []

    try:
        from core.database import db
        if db.is_available():
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # Text search in pr_events content
                    cur.execute(
                        """SELECT source, content, created_at
                           FROM pr_events
                           WHERE client_id=1 AND project=%s
                             AND content ILIKE %s
                           ORDER BY created_at DESC
                           LIMIT %s""",
                        (project, f"%{query}%", limit),
                    )
                    rows = cur.fetchall()
                    for row in rows:
                        ts = row[2].strftime("%Y-%m-%d") if row[2] else "?"
                        results.append(f"[{ts}] {row[0]}: {(row[1] or '')[:300]}")
    except Exception as e:
        log.debug(f"search_memory DB error: {e}")

    # Fallback: search history.jsonl
    if not results:
        try:
            import os
            cfg_path = Path.home() / ".aicli" / "config.json"
            workspace = "workspace"
            if cfg_path.exists():
                workspace = json.loads(cfg_path.read_text()).get("workspace_dir", workspace)
            history_path = Path(workspace) / project / "_system" / "history.jsonl"
            if history_path.exists():
                lines = history_path.read_text().splitlines()
                query_lower = query.lower()
                for line in reversed(lines[-500:]):
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
            with db.conn() as conn:
                with conn.cursor() as cur:
                    if feature:
                        cur.execute(
                            """SELECT i.role, i.content, i.created_at
                               FROM pr_prompts i
                               JOIN pr_prompt_tags it ON it.interaction_id = i.id
                               JOIN mng_entity_values ev ON ev.id = it.entity_value_id
                               WHERE i.client_id=1 AND i.project=%s AND ev.name ILIKE %s
                               ORDER BY i.created_at DESC LIMIT %s""",
                            (project, f"%{feature}%", limit),
                        )
                    else:
                        cur.execute(
                            """SELECT role, content, created_at
                               FROM pr_prompts
                               WHERE client_id=1 AND project=%s
                               ORDER BY created_at DESC LIMIT %s""",
                            (project, limit),
                        )
                    rows = cur.fetchall()
                    for row in rows:
                        ts = row[2].strftime("%Y-%m-%d %H:%M") if row[2] else "?"
                        results.append(f"[{ts}] {row[0]}: {(row[1] or '')[:400]}")
    except Exception as e:
        log.debug(f"get_recent_history DB error: {e}")

    # Fallback: history.jsonl
    if not results:
        try:
            import os
            cfg_path = Path.home() / ".aicli" / "config.json"
            workspace = "workspace"
            if cfg_path.exists():
                workspace = json.loads(cfg_path.read_text()).get("workspace_dir", workspace)
            history_path = Path(workspace) / project / "_system" / "history.jsonl"
            if history_path.exists():
                lines = history_path.read_text().splitlines()
                for line in reversed(lines[-(limit * 2):]):
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

    if not results:
        return "No recent history found."
    return "\n\n".join(results)


def _handle_get_project_facts(args: dict) -> str:
    project = args.get("project") or _get_active_project()

    # Try DB first
    try:
        from core.database import db
        if db.is_available():
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT key, value FROM pr_project_facts
                           WHERE client_id=1 AND project=%s
                           ORDER BY key""",
                        (project,),
                    )
                    rows = cur.fetchall()
                    if rows:
                        lines = [f"{r[0]}: {r[1]}" for r in rows]
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
            facts = state.get("facts", {})
            if facts:
                lines = [f"{k}: {v}" for k, v in facts.items()]
                return "Project Facts:\n" + "\n".join(lines)
    except Exception as e:
        log.debug(f"get_project_facts JSON fallback: {e}")

    return "No project facts found."


# ── Handler map ───────────────────────────────────────────────────────────────

MEMORY_HANDLERS: dict[str, callable] = {
    "search_memory":       _handle_search_memory,
    "get_recent_history":  _handle_get_recent_history,
    "get_project_facts":   _handle_get_project_facts,
}
