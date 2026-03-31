"""
memory_files.py — Template-based LLM context file renderer.

Renders all per-project context files from DB tables with NO LLM calls.
Deterministic: same DB state → same output every time.

Managed files (root):
  {sys_dir}/claude/CLAUDE.md              — Claude CLI context (main)
  {sys_dir}/cursor/rules.md               — Cursor rules
  {sys_dir}/llm_prompts/compact.md        — Compact system prompt (GPT-4 / small window, ≤2000 tokens)
  {sys_dir}/llm_prompts/full.md           — Full system prompt (Claude / Deepseek / Gemini)
  {sys_dir}/llm_prompts/gemini_context.md — Gemini Files API upload context
  {code_dir}/CLAUDE.md                    — copy to code root (auto-loaded by Claude CLI)
  {code_dir}/.cursorrules                 — copy to code root (Cursor)
  {code_dir}/.claude/memory/top_events.md — top-N events injected at session start

Per-feature:
  {code_dir}/features/{tag}/CLAUDE.md     — feature context (auto-loaded when in that dir)

Trigger conditions:
  project_facts upsert     → write_root_files()
  work_items upsert        → write_root_files() + write_feature_files(tag)
  session_summaries insert → write_root_files()
  tag_relations insert     → write_root_files() + write_feature_files(affected tags)
  feature_snapshots upsert → write_feature_files(tag)
  /memory endpoint         → write_all_files()
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from core.database import db
from core.config import settings

log = logging.getLogger(__name__)

# ── SQL ────────────────────────────────────────────────────────────────────────

_SQL_FACTS = """
    SELECT COALESCE(category, 'general'), fact_key, fact_value
    FROM mem_ai_project_facts
    WHERE client_id=1 AND project=%s AND valid_until IS NULL
      AND conflict_status IS DISTINCT FROM 'pending_review'
    ORDER BY category NULLS LAST, fact_key
"""

_SQL_ACTIVE_WORK_ITEMS = """
    SELECT wi.name, wi.description, wi.lifecycle_status, wi.category_name,
           wi.seq_num, t.name AS tag_name
    FROM mem_ai_work_items wi
    LEFT JOIN planner_tags t ON t.id = wi.tag_id
    WHERE wi.client_id=1 AND wi.project=%s AND wi.status != 'done'
    ORDER BY CASE wi.lifecycle_status
               WHEN 'development' THEN 1 WHEN 'testing' THEN 2
               WHEN 'review' THEN 3      WHEN 'design'  THEN 4
               WHEN 'idea'   THEN 5      ELSE 6
             END,
             wi.created_at DESC
"""

_SQL_LATEST_SESSION = """
    SELECT summary, open_threads, next_steps, created_at, session_id
    FROM mem_ai_events
    WHERE client_id=1 AND project=%s AND event_type='session_summary'
    ORDER BY created_at DESC
    LIMIT 1
"""

_SQL_BLOCKERS = """
    WITH pt AS (SELECT id, name FROM planner_tags WHERE client_id=1 AND project=%s)
    SELECT f.name, r.relation, t.name, r.note
    FROM mem_ai_tags_relations r
    JOIN pt f ON f.id = r.from_tag_id
    JOIN pt t ON t.id = r.to_tag_id
    WHERE r.relation IN ('blocks', 'depends_on')
    ORDER BY r.relation, f.name
"""

_SQL_ALL_RELATIONS = """
    WITH pt AS (SELECT id, name FROM planner_tags WHERE client_id=1 AND project=%s)
    SELECT f.name, r.relation, t.name, r.note
    FROM mem_ai_tags_relations r
    JOIN pt f ON f.id = r.from_tag_id
    JOIN pt t ON t.id = r.to_tag_id
    ORDER BY r.relation, f.name
"""

_SQL_FEATURE_SNAPSHOTS = """
    SELECT fs.requirements, fs.action_items, fs.design, fs.code_summary,
           fs.work_item_status, t.name AS tag_name
    FROM mem_ai_features fs
    JOIN planner_tags t ON t.id = fs.tag_id
    WHERE fs.client_id=1 AND fs.project=%s
    ORDER BY fs.updated_at DESC
"""

_SQL_BLOCKED_TAGS = """
    SELECT t.name, COALESCE(tm.description, '')
    FROM planner_tags t
    LEFT JOIN planner_tags_meta tm ON tm.tag_id = t.id
    WHERE t.client_id=1 AND t.project=%s AND t.status='blocked'
    ORDER BY t.name
"""

_SQL_TOP_EVENTS = """
    SELECT content, event_type, importance, created_at,
           importance * EXP(-0.01 * EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400.0) AS relevance
    FROM mem_ai_events
    WHERE client_id=1 AND project=%s
    ORDER BY relevance DESC
    LIMIT %s
"""

_SQL_ACTIVE_TAGS = """
    SELECT DISTINCT t.name
    FROM mem_ai_features fs
    JOIN planner_tags t ON t.id = fs.tag_id
    JOIN mem_ai_work_items wi ON wi.tag_id = t.id
    WHERE fs.client_id=1 AND fs.project=%s
      AND wi.status != 'done'
    ORDER BY t.name
"""

_SQL_FEATURE_SNAPSHOT_BY_TAG = """
    SELECT fs.requirements, fs.action_items, fs.design, fs.code_summary, fs.work_item_status
    FROM mem_ai_features fs
    JOIN planner_tags t ON t.id = fs.tag_id
    WHERE fs.client_id=1 AND fs.project=%s AND t.name=%s
    LIMIT 1
"""

_SQL_FEATURE_RELATIONS = """
    SELECT f.name AS from_name, r.relation, t.name AS to_name, r.note
    FROM mem_ai_tags_relations r
    JOIN planner_tags f ON f.id = r.from_tag_id
    JOIN planner_tags t ON t.id = r.to_tag_id
    WHERE (r.from_tag_id = (SELECT id FROM planner_tags WHERE client_id=1 AND project=%s AND name=%s LIMIT 1)
        OR r.to_tag_id  = (SELECT id FROM planner_tags WHERE client_id=1 AND project=%s AND name=%s LIMIT 1))
    ORDER BY r.relation
"""


# ── MemoryFiles ────────────────────────────────────────────────────────────────

class MemoryFiles:
    """
    Renders and writes all LLM context files from DB tables.
    No LLM calls — pure template rendering.
    """

    # ── Path helpers ──────────────────────────────────────────────────────────

    def _workspace(self) -> Path:
        return Path(settings.workspace_dir)

    def _sys_dir(self, project: str) -> Path:
        return self._workspace() / project / "_system"

    def _code_dir(self, project: str) -> Optional[Path]:
        try:
            from gitops.git import get_project_code_dir
            cd = get_project_code_dir(project)
            return Path(cd) if cd else None
        except Exception:
            return None

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_context(self, project: str) -> dict:
        """Load all DB data needed for rendering."""
        ctx: dict = {
            "project":          project,
            "facts_by_cat":     {},      # category → [(key, value)]
            "active_work":      [],      # list of dicts
            "latest_session":   None,    # dict or None
            "blockers":         [],      # (from_name, relation, to_name, note)
            "all_relations":    [],
            "features":         {},      # tag_name → snapshot dict
            "blocked_tags":     [],      # (name, description)
            "ts":               datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }
        if not db.is_available():
            return ctx

        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # Project facts grouped by category
                    cur.execute(_SQL_FACTS, (project,))
                    for cat, key, val in cur.fetchall():
                        ctx["facts_by_cat"].setdefault(cat, []).append((key, val))

                    # Active work items
                    cur.execute(_SQL_ACTIVE_WORK_ITEMS, (project,))
                    for name, desc, lifecycle, cat_name, seq_num, tag_name in cur.fetchall():
                        ctx["active_work"].append({
                            "name": name, "desc": (desc or "")[:120],
                            "lifecycle": lifecycle, "category": cat_name,
                            "seq_num": seq_num, "tag_name": tag_name or name,
                        })

                    # Latest session summary
                    cur.execute(_SQL_LATEST_SESSION, (project,))
                    row = cur.fetchone()
                    if row:
                        ctx["latest_session"] = {
                            "summary":      row[0] or "",
                            "open_threads": row[1] or "",
                            "next_steps":   row[2] or "",
                            "created_at":   row[3].strftime("%Y-%m-%d %H:%M") if row[3] else "",
                            "session_id":   row[4] or "",
                        }

                    # Blockers and dependencies
                    cur.execute(_SQL_BLOCKERS, (project,))
                    ctx["blockers"] = [
                        {"from": r[0], "relation": r[1], "to": r[2], "note": r[3] or ""}
                        for r in cur.fetchall()
                    ]

                    # All relations
                    cur.execute(_SQL_ALL_RELATIONS, (project,))
                    ctx["all_relations"] = [
                        {"from": r[0], "relation": r[1], "to": r[2], "note": r[3] or ""}
                        for r in cur.fetchall()
                    ]

                    # Feature snapshots
                    cur.execute(_SQL_FEATURE_SNAPSHOTS, (project,))
                    for reqs, action, design, code_sum, wi_status, tag_name in cur.fetchall():
                        ctx["features"][tag_name] = {
                            "requirements":    reqs or "",
                            "action_items":    action or "",
                            "design":          design or {},
                            "code_summary":    code_sum or {},
                            "work_item_status": wi_status or "",
                        }

                    # Blocked tags
                    cur.execute(_SQL_BLOCKED_TAGS, (project,))
                    ctx["blocked_tags"] = [(r[0], r[1]) for r in cur.fetchall()]

        except Exception as e:
            log.warning(f"MemoryFiles._load_context error for '{project}': {e}")

        return ctx

    def get_top_events(self, project: str, limit: int = 5) -> list[dict]:
        """Return top-N events by time-decayed relevance score."""
        if not db.is_available():
            return []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_TOP_EVENTS, (project, limit))
                    return [
                        {
                            "content":     r[0],
                            "event_type": r[1],
                            "importance":  r[2],
                            "created_at":  r[3].isoformat() if r[3] else "",
                            "relevance":   float(r[4]) if r[4] else 0.0,
                        }
                        for r in cur.fetchall()
                    ]
        except Exception as e:
            log.debug(f"get_top_events error: {e}")
            return []

    def get_active_feature_tags(self, project: str) -> list[str]:
        """Return tag names for active features that have snapshots."""
        if not db.is_available():
            return []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_ACTIVE_TAGS, (project,))
                    return [r[0] for r in cur.fetchall()]
        except Exception:
            return []

    # ── Renderers ─────────────────────────────────────────────────────────────

    def render_root_claude_md(self, ctx: dict) -> str:
        """Render root CLAUDE.md — Claude CLI auto-loads this."""
        project = ctx["project"]
        lines = [f"# Project: {project}", ""]

        # Stack & Architecture
        stack_cats = ("stack", "pattern")
        stack_facts = []
        for cat in stack_cats:
            stack_facts.extend(ctx["facts_by_cat"].get(cat, []))
        if stack_facts:
            lines += ["## Stack & Architecture", ""]
            for key, val in stack_facts:
                lines.append(f"- **{key}**: {val}")
            lines.append("")

        # Active Work
        if ctx["active_work"]:
            lines += ["## Active Work", ""]
            for wi in ctx["active_work"][:12]:
                ref = f"#{wi['seq_num']} " if wi.get("seq_num") else ""
                tag = wi["tag_name"]
                summary = wi["desc"] or wi["name"]
                lifecycle = wi["lifecycle"]
                lines.append(f"- `{ref}{tag}` [{lifecycle}] — {summary}")
            lines.append("")

        # Current Blockers
        blockers = [r for r in ctx["blockers"] if r["relation"] == "blocks"]
        deps     = [r for r in ctx["blockers"] if r["relation"] == "depends_on"]
        if blockers:
            lines += ["## Current Blockers", ""]
            for r in blockers:
                note = f" _{r['note']}_" if r["note"] else ""
                lines.append(f"- `{r['from']}` blocks `{r['to']}`{note}")
            lines.append("")
        if deps:
            lines += ["## Dependencies", ""]
            for r in deps:
                note = f" _{r['note']}_" if r["note"] else ""
                lines.append(f"- `{r['from']}` depends on `{r['to']}`{note}")
            lines.append("")

        # Last Session
        sess = ctx.get("latest_session")
        if sess and sess.get("summary"):
            lines += [f"## Last Session _{sess['created_at']}_", ""]
            for bullet in sess["summary"].strip().splitlines():
                if bullet.strip():
                    lines.append(bullet if bullet.startswith("-") else f"- {bullet.strip()}")
            lines.append("")
            if sess.get("open_threads"):
                lines += ["### Open Threads", ""]
                for t in sess["open_threads"].strip().splitlines():
                    if t.strip():
                        lines.append(t if t.startswith("-") else f"- {t.strip()}")
                lines.append("")
            if sess.get("next_steps"):
                lines += ["### Next Steps", ""]
                for ns in sess["next_steps"].strip().splitlines():
                    if ns.strip():
                        lines.append(ns if ns.startswith("-") else f"- {ns.strip()}")
                lines.append("")

        # Conventions
        conv_facts = ctx["facts_by_cat"].get("convention", [])
        if conv_facts:
            lines += ["## Conventions", ""]
            for key, val in conv_facts:
                lines.append(f"- **{key}**: {val}")
            lines.append("")

        # Constraints
        const_facts = ctx["facts_by_cat"].get("constraint", [])
        if const_facts:
            lines += ["## Constraints", ""]
            for key, val in const_facts:
                lines.append(f"- **{key}**: {val}")
            lines.append("")

        # Client Requirements
        client_facts = ctx["facts_by_cat"].get("client", [])
        if client_facts:
            lines += ["## Client Requirements", ""]
            for key, val in client_facts:
                lines.append(f"- **{key}**: {val}")
            lines.append("")

        # Do Not Touch
        if ctx["blocked_tags"]:
            lines += ["## Do Not Touch", ""]
            for name, desc in ctx["blocked_tags"]:
                reason = f" — {desc}" if desc else ""
                lines.append(f"- `{name}`{reason}")
            lines.append("")

        # Memory reference footer
        lines += [
            "---",
            "_Auto-generated by aicli memory system. Run `/memory` to refresh._",
            f"_Last updated: {ctx['ts']}_",
        ]

        return "\n".join(lines)

    def render_feature_claude_md(self, project: str, tag_name: str) -> str:
        """Render per-feature CLAUDE.md — auto-loaded when Claude enters features/{tag}/ dir."""
        if not db.is_available():
            return f"# Feature: {tag_name}\n_No database available._\n"

        snap = {}
        relations = []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_FEATURE_SNAPSHOT_BY_TAG, (project, tag_name))
                    row = cur.fetchone()
                    if row:
                        snap = {
                            "requirements":    row[0] or "",
                            "action_items":    row[1] or "",
                            "design":          row[2] or {},
                            "code_summary":    row[3] or {},
                            "work_item_status": row[4] or "",
                        }
                    cur.execute(_SQL_FEATURE_RELATIONS, (project, tag_name, project, tag_name))
                    relations = [
                        {"from": r[0], "relation": r[1], "to": r[2], "note": r[3] or ""}
                        for r in cur.fetchall()
                    ]
        except Exception as e:
            log.debug(f"render_feature_claude_md error for '{tag_name}': {e}")

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        status = snap.get("work_item_status") or "unknown"
        lines = [f"# Feature: {tag_name}", f"_Status: {status} | {ts}_", ""]

        if snap.get("requirements"):
            lines += ["## Requirements", "", snap["requirements"], ""]
        if snap.get("action_items"):
            lines += ["## Action Items", "", snap["action_items"], ""]

        design = snap.get("design") or {}
        if isinstance(design, dict) and design.get("high_level"):
            lines += ["## Design", "", design["high_level"], ""]
            if design.get("patterns_used"):
                pts = design["patterns_used"]
                if isinstance(pts, list):
                    lines += ["**Patterns**: " + ", ".join(str(p) for p in pts), ""]

        code = snap.get("code_summary") or {}
        if isinstance(code, dict) and code.get("files"):
            lines += ["## Files", ""]
            for f in code["files"][:15]:
                lines.append(f"- `{f}`")
            lines.append("")

        if relations:
            lines += ["## Relationships", ""]
            for r in relations:
                note = f" _{r['note']}_" if r["note"] else ""
                lines.append(f"- `{r['from']}` **{r['relation']}** `{r['to']}`{note}")
            lines.append("")

        lines += ["---", "_Auto-generated by aicli. Run `/memory` to refresh._"]
        return "\n".join(lines)

    def render_cursorrules(self, ctx: dict) -> str:
        """Render .cursorrules — kept under 2000 tokens."""
        project = ctx["project"]
        lines = [f"## Project: {project}", ""]

        stack = ctx["facts_by_cat"].get("stack", [])
        if stack:
            lines += ["## Stack", ""]
            for key, val in stack[:8]:
                lines.append(f"{key}: {val}")
            lines.append("")

        patterns = ctx["facts_by_cat"].get("pattern", [])
        if patterns:
            lines += ["## Patterns in Use", ""]
            for key, val in patterns[:6]:
                lines.append(f"{key}: {val}")
            lines.append("")

        conventions = ctx["facts_by_cat"].get("convention", [])
        if conventions:
            lines += ["## Coding Conventions", ""]
            for key, val in conventions[:8]:
                lines.append(f"{key}: {val}")
            lines.append("")

        # Active features (in_progress only, concise)
        in_progress = [w for w in ctx["active_work"] if w["lifecycle"] in ("development", "testing", "review")]
        if in_progress:
            lines += ["## Active Features (do not break)", ""]
            for wi in in_progress[:5]:
                lines.append(f"{wi['tag_name']}: {(wi['desc'] or wi['name'])[:80]}")
            lines.append("")

        constraints = ctx["facts_by_cat"].get("constraint", [])
        if constraints:
            lines += ["## Never Do", ""]
            for _, val in constraints[:5]:
                lines.append(f"- {val}")
            lines.append("")

        return "\n".join(lines)

    def render_system_compact(self, ctx: dict) -> str:
        """Compact system prompt — for GPT-4 and other small-window models (≤2000 tokens)."""
        project = ctx["project"]
        lines = [
            f"You are a senior developer working on **{project}**.",
            "Respect all project facts below. Never contradict them unless explicitly asked.",
            "When working on a specific feature, ask for its snapshot before making decisions.",
            "",
        ]

        # Stack (max 5)
        stack = (
            ctx["facts_by_cat"].get("stack", []) +
            ctx["facts_by_cat"].get("pattern", [])
        )[:5]
        if stack:
            lines += ["## Stack", ""]
            for key, val in stack:
                lines.append(f"- {key}: {val}")
            lines.append("")

        # Active features (max 3)
        active = ctx["active_work"][:3]
        if active:
            lines += ["## Active Features", ""]
            for wi in active:
                lines.append(f"- {wi['tag_name']} [{wi['lifecycle']}]: {(wi['desc'] or wi['name'])[:80]}")
            lines.append("")

        # Last session (2 sentences)
        sess = ctx.get("latest_session")
        if sess and sess.get("summary"):
            bullets = [b.strip().lstrip("- ") for b in sess["summary"].strip().splitlines() if b.strip()]
            compact = ". ".join(bullets[:2]) + ("." if bullets else "")
            lines += ["## Last Session", compact, ""]

        return "\n".join(lines)

    def render_system_full(self, ctx: dict) -> str:
        """Full system prompt — for Claude, Deepseek, Gemini (large context window)."""
        project = ctx["project"]
        lines = [
            f"You are a senior developer working on **{project}**.",
            "Respect all project facts below. Never contradict them unless explicitly asked.",
            "When working on a specific feature, ask for its snapshot before making decisions.",
            "",
        ]

        # All fact categories
        cat_labels = {
            "stack":      "## Stack",
            "pattern":    "## Architecture Patterns",
            "convention": "## Conventions",
            "constraint": "## Never Do",
            "client":     "## Client Requirements",
            "general":    "## Project Notes",
        }
        for cat, label in cat_labels.items():
            facts = ctx["facts_by_cat"].get(cat, [])
            if facts:
                lines += [label, ""]
                for key, val in facts:
                    lines.append(f"- **{key}**: {val}")
                lines.append("")

        # Active features
        if ctx["active_work"]:
            lines += ["## Active Features", ""]
            for wi in ctx["active_work"]:
                ref = f"#{wi['seq_num']} " if wi.get("seq_num") else ""
                lines.append(
                    f"- `{ref}{wi['tag_name']}` [{wi['lifecycle']}]: "
                    f"{(wi['desc'] or wi['name'])[:120]}"
                )
            lines.append("")

        # Blockers
        blockers = [r for r in ctx["blockers"] if r["relation"] == "blocks"]
        if blockers:
            lines += ["## Current Blockers", ""]
            for r in blockers:
                note = f" ({r['note']})" if r["note"] else ""
                lines.append(f"- `{r['from']}` blocks `{r['to']}`{note}")
            lines.append("")

        # Last session
        sess = ctx.get("latest_session")
        if sess and sess.get("summary"):
            lines += [f"## Last Session ({sess['created_at']})", ""]
            for bullet in sess["summary"].strip().splitlines():
                if bullet.strip():
                    lines.append(bullet if bullet.startswith("-") else f"- {bullet.strip()}")
            if sess.get("open_threads"):
                lines += ["", "Open threads:", sess["open_threads"]]
            if sess.get("next_steps"):
                lines += ["", "Next steps:", sess["next_steps"]]
            lines.append("")

        return "\n".join(lines)

    def render_gemini_context(self, ctx: dict) -> str:
        """Full Gemini context for Files API upload — all data, verbose."""
        project = ctx["project"]
        ts = ctx["ts"]
        lines = [
            f"# Project Context: {project}",
            f"# Generated: {ts}",
            "",
        ]

        # All project facts grouped by category
        if ctx["facts_by_cat"]:
            lines += ["## Project Facts", ""]
            for cat, facts in sorted(ctx["facts_by_cat"].items()):
                lines += [f"### {cat.title()}", ""]
                for key, val in facts:
                    lines.append(f"- {key}: {val}")
                lines.append("")

        # All active work items (full summary)
        if ctx["active_work"]:
            lines += ["## Active Work Items", ""]
            for wi in ctx["active_work"]:
                ref = f"#{wi['seq_num']} " if wi.get("seq_num") else ""
                lines += [
                    f"### {ref}{wi['tag_name']}",
                    f"Status: {wi['lifecycle']} | Category: {wi['category']}",
                    wi["desc"] or wi["name"],
                    "",
                ]

        # Latest session (full)
        sess = ctx.get("latest_session")
        if sess and sess.get("summary"):
            lines += [f"## Recent Session ({sess['created_at']})", ""]
            lines.append(sess["summary"])
            if sess.get("open_threads"):
                lines += ["", "**Open Threads:**", sess["open_threads"]]
            if sess.get("next_steps"):
                lines += ["", "**Next Steps:**", sess["next_steps"]]
            lines.append("")

        # Feature snapshots (active features only)
        active_tags = {wi["tag_name"] for wi in ctx["active_work"]}
        active_snaps = {k: v for k, v in ctx["features"].items() if k in active_tags}
        if active_snaps:
            lines += ["## Feature Snapshots (Active)", ""]
            for tag_name, snap in active_snaps.items():
                lines += [f"### {tag_name}", ""]
                if snap.get("requirements"):
                    lines += ["**Requirements:**", snap["requirements"], ""]
                if snap.get("action_items"):
                    lines += ["**Action Items:**", snap["action_items"], ""]
                design = snap.get("design") or {}
                if isinstance(design, dict) and design.get("high_level"):
                    lines += ["**Design:**", design["high_level"], ""]
                code = snap.get("code_summary") or {}
                if isinstance(code, dict) and code.get("files"):
                    files_str = ", ".join(f"`{f}`" for f in code["files"][:10])
                    lines += [f"**Files:** {files_str}", ""]

        # All relationships
        if ctx["all_relations"]:
            lines += ["## Relationships", ""]
            for r in ctx["all_relations"]:
                note = f" ({r['note']})" if r["note"] else ""
                lines.append(f"- `{r['from']}` → **{r['relation']}** → `{r['to']}`{note}")
            lines.append("")

        return "\n".join(lines)

    def render_top_events_md(self, project: str, limit: int = 5) -> str:
        """Render top-N events as .claude/memory/top_events.md for session injection."""
        events = self.get_top_events(project, limit)
        if not events:
            return ""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            "# Recent Memory Events",
            f"_Top {len(events)} most relevant events — auto-updated at session start ({ts})_",
            "",
        ]
        for i, ev in enumerate(events, 1):
            stype = ev["event_type"]
            rel = f"{ev['relevance']:.1f}"
            content = ev["content"][:200].replace("\n", " ")
            lines.append(f"{i}. **[{stype} | relevance={rel}]** {content}")
        lines.append("")
        return "\n".join(lines)

    # ── Writers ───────────────────────────────────────────────────────────────

    def write_root_files(self, project: str) -> list[str]:
        """
        Render and write all root-level context files.
        Returns list of written file paths (relative to workspace).
        """
        ctx = self._load_context(project)
        sys_dir = self._sys_dir(project)
        code_dir = self._code_dir(project)
        written: list[str] = []

        # Ensure directories exist
        (sys_dir / "claude").mkdir(parents=True, exist_ok=True)
        (sys_dir / "cursor").mkdir(parents=True, exist_ok=True)
        (sys_dir / "llm_prompts").mkdir(parents=True, exist_ok=True)

        def _write(path: Path, content: str) -> None:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                written.append(str(path))
            except Exception as e:
                log.warning(f"write_root_files: failed to write {path}: {e}")

        # Root CLAUDE.md
        claude_content = self.render_root_claude_md(ctx)
        _write(sys_dir / "claude" / "CLAUDE.md", claude_content)
        _write(sys_dir / "CLAUDE.md", claude_content)  # backward compat

        # Cursor rules
        _write(sys_dir / "cursor" / "rules.md", self.render_cursorrules(ctx))

        # LLM system prompts
        _write(sys_dir / "llm_prompts" / "compact.md",       self.render_system_compact(ctx))
        _write(sys_dir / "llm_prompts" / "full.md",          self.render_system_full(ctx))
        _write(sys_dir / "llm_prompts" / "gemini_context.md", self.render_gemini_context(ctx))

        # Copy to code_dir
        if code_dir and code_dir.exists():
            _write(code_dir / "CLAUDE.md", claude_content)
            _write(code_dir / ".cursorrules", self.render_cursorrules(ctx))

            # Top events for .claude/memory/
            top_events_content = self.render_top_events_md(project)
            if top_events_content:
                _write(
                    code_dir / ".claude" / "memory" / "top_events.md",
                    top_events_content,
                )

        return written

    def write_feature_files(self, project: str, tag_name: str) -> list[str]:
        """
        Render and write the feature-level CLAUDE.md for a specific tag.
        Written to {code_dir}/features/{tag_name}/CLAUDE.md.
        """
        code_dir = self._code_dir(project)
        written: list[str] = []

        content = self.render_feature_claude_md(project, tag_name)
        if not content:
            return written

        # Write to _system for archive
        sys_dir = self._sys_dir(project)
        sys_feature_path = sys_dir / "claude" / "features" / tag_name / "CLAUDE.md"
        try:
            sys_feature_path.parent.mkdir(parents=True, exist_ok=True)
            sys_feature_path.write_text(content, encoding="utf-8")
            written.append(str(sys_feature_path))
        except Exception as e:
            log.warning(f"write_feature_files: sys_dir write failed: {e}")

        # Write to code_dir for Claude CLI auto-load
        if code_dir and code_dir.exists():
            code_feature_path = code_dir / "features" / tag_name / "CLAUDE.md"
            try:
                code_feature_path.parent.mkdir(parents=True, exist_ok=True)
                code_feature_path.write_text(content, encoding="utf-8")
                written.append(str(code_feature_path))
            except Exception as e:
                log.warning(f"write_feature_files: code_dir write failed: {e}")

        return written

    def write_all_files(self, project: str) -> list[str]:
        """Write root files + all active feature files."""
        written = self.write_root_files(project)
        for tag_name in self.get_active_feature_tags(project):
            written.extend(self.write_feature_files(project, tag_name))
        return written
