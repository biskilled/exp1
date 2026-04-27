"""
memory_files.py — Template-based LLM context file renderer.

Renders all per-project context files from DB tables with NO LLM calls.
Deterministic: same DB state → same output every time.

Provider mapping is driven by backend/memory/memory.yaml (engine config, not per-project).

Managed files (memory/):
  claude/CLAUDE.md        — full context  → code_dir/CLAUDE.md (Claude Code)
  cursor/rules.md         — compact       → code_dir/.cursorrules (Cursor)
  copilot/instructions.md — compact (=cursor/rules.md) → code_dir/.github/copilot-instructions.md
  api/system_prompt.md    — compact, shared by ALL API providers
  code.md                 — directory tree + hotspots + file coupling
  GEMINI.md               — full (=CLAUDE.md) → code_dir/GEMINI.md (Gemini CLI)
  AGENTS.md               — full (=CLAUDE.md) → code_dir/AGENTS.md  (Codex CLI)

Trigger conditions:
  project_facts upsert → write_root_files()
  work_item update     → write_root_files()
  /memory endpoint     → write_all_files()
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml as _yaml

from core.database import db
from core.config import settings
from core.prompt_loader import prompts as _prompts
from core import project_paths as pp

log = logging.getLogger(__name__)

# ── SQL ────────────────────────────────────────────────────────────────────────

_SQL_FACTS = """
    SELECT COALESCE(category, 'general'), fact_key, fact_value
    FROM mem_ai_project_facts
    WHERE project_id=%s AND valid_until IS NULL
      AND conflict_status IS DISTINCT FROM 'pending_review'
    ORDER BY category NULLS LAST, fact_key
"""

_SQL_ACTIVE_WORK_ITEMS = """
    SELECT wi_id, name, wi_type, user_status, due_date,
           LEFT(COALESCE(summary, ''), 100),
           LEFT(COALESCE(acceptance_criteria, ''), 150),
           LEFT(COALESCE(implementation_plan, ''), 200)
    FROM mem_work_items
    WHERE project_id = %s
      AND wi_type IN ('use_case', 'feature', 'bug', 'task')
      AND deleted_at IS NULL
      AND completed_at IS NULL
      AND approved_at IS NOT NULL
      AND user_status NOT IN ('done', 'blocked')
    ORDER BY
      CASE wi_type WHEN 'bug' THEN 0 WHEN 'use_case' THEN 1 WHEN 'feature' THEN 2 ELSE 3 END,
      score_importance DESC NULLS LAST,
      created_at DESC
    LIMIT 20
"""

_SQL_IN_PROGRESS_ITEMS = """
    SELECT wi_id, name, wi_type, due_date
    FROM mem_work_items
    WHERE project_id = %s
      AND user_status = 'in-progress'
      AND deleted_at IS NULL
      AND completed_at IS NULL
      AND approved_at IS NOT NULL
    ORDER BY score_importance DESC NULLS LAST, updated_at DESC
    LIMIT 10
"""

# user_status is TEXT after m079 migration: 'open'|'pending'|'in-progress'|'review'|'blocked'|'done'
# Pre-migration (smallint) values are mapped for backward compat.
_WI_STATUS_LABELS: dict = {
    0: "open", 1: "pending", 2: "in-progress", 3: "review", 4: "blocked", 5: "done",
    "open": "open", "pending": "pending", "in-progress": "in-progress",
    "review": "review", "blocked": "blocked", "done": "done",
}

_SQL_RECENTLY_CHANGED = """
    SELECT c.commit_hash_short, c.created_at::date AS commit_date,
           cc.file_path, cc.symbol_type, cc.class_name, cc.method_name,
           cc.file_change, cc.llm_summary
    FROM mem_mrr_commits c
    JOIN mem_mrr_commits_code cc ON cc.commit_hash = c.commit_hash
    WHERE c.project_id = %s
    ORDER BY c.created_at DESC
    LIMIT 60
"""

_SQL_HOTSPOTS = """
    SELECT file_path, hotspot_score, commit_count, current_lines, bug_commit_count, last_changed_at
    FROM mem_mrr_commits_file_stats
    WHERE project_id = %s AND hotspot_score >= %s
    ORDER BY hotspot_score DESC
    LIMIT 20
"""

# Single parameterized coupling query — used with different thresholds for display vs. work-item suggest
_SQL_COUPLING = """
    SELECT file_a, file_b, co_change_count
    FROM mem_mrr_commits_file_coupling
    WHERE project_id = %s AND co_change_count >= %s
    ORDER BY co_change_count DESC
    LIMIT 10
"""


# ── MemoryFiles ────────────────────────────────────────────────────────────────

class MemoryFiles:
    """
    Renders and writes all LLM context files from DB tables.
    No LLM calls — pure template rendering.
    """

    # ── Token helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _tokens(text: str) -> int:
        """Approximate token count (1 token ≈ 4 chars)."""
        return max(1, len(text) // 4)

    # ── Providers config ──────────────────────────────────────────────────────

    def _load_providers(self) -> dict:
        """Load memory.yaml — canonical map of CLI tools, API providers, and managed files.

        Reads from backend/memory/memory.yaml (engine code, not per-project workspace).
        """
        canon_path = Path(__file__).parent / "memory.yaml"
        try:
            if canon_path.exists():
                return _yaml.safe_load(canon_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            log.debug("_load_providers: %s", e)
        return {}

    # ── Config loading ────────────────────────────────────────────────────────

    def _load_memory_config(self, project: str) -> dict:
        """Load memory size config from project.yaml, with defaults."""
        defaults = {
            "claude_md_max_tokens": 8000,
            "cursorrules_max_tokens": 2000,
            "recent_work_max_entries": 30,
            "hotspot_threshold": 5,
            "coupling_threshold": 8,
            "hotspot_suggest_work_item": True,
        }
        try:
            proj_yaml = self._workspace() / project / "project.yaml"
            if proj_yaml.exists():
                data = _yaml.safe_load(proj_yaml.read_text(encoding="utf-8")) or {}
                mem = data.get("memory", {})
                return {**defaults, **mem}
        except Exception:
            pass
        return defaults

    # ── Path helpers ──────────────────────────────────────────────────────────

    def _workspace(self) -> Path:
        return Path(settings.workspace_dir)

    def _sys_dir(self, project: str) -> Path:
        """Backward-compat alias — returns memory_dir."""
        return pp.memory_dir(project)

    def _code_dir(self, project: str) -> Optional[Path]:
        # Try pipeline helper first (reads project.yaml + settings)
        try:
            from pipelines.pipeline_git import get_project_code_dir
            cd = get_project_code_dir(project)
            if cd:
                return Path(cd)
        except Exception:
            pass
        # Fallback: read project.yaml directly from workspace
        try:
            proj_yaml = self._workspace() / project / "project.yaml"
            if proj_yaml.exists():
                cfg = _yaml.safe_load(proj_yaml.read_text()) or {}
                cd = cfg.get("code_dir")
                if cd:
                    return Path(cd)
        except Exception:
            pass
        return None

    # ── Data loading ──────────────────────────────────────────────────────────

    def _load_context(self, project: str) -> dict:
        """Load all DB data needed for rendering."""
        mem_cfg = self._load_memory_config(project)
        ctx: dict = {
            "project":          project,
            "facts_by_cat":     {},      # category → [(key, value)]
            "active_tags":      [],      # list of dicts from mem_work_items (use_case/feature)
            "recently_changed": [],      # recently changed symbols from commits
            "project_summary":  "",      # first lines from PROJECT.md
            "code_structure":   [],      # top-level dirs in code_dir
            "hotspots":         [],      # high-score files from mem_mrr_commits_file_stats
            "coupling":         [],      # tightly-coupled file pairs
            "memory_config":    mem_cfg,
            "ts":               datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }

        # Load project_state.json — must run regardless of DB availability so
        # hook-triggered renders still get Stack & Key Decisions sections.
        state_data: dict = {}
        try:
            state_path = pp.project_state_path(project)
            if state_path.exists():
                state_data = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            pass
        ctx["state_data"] = state_data

        if not db.is_available():
            return ctx

        project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # Project facts grouped by category
                    cur.execute(_SQL_FACTS, (project_id,))
                    for cat, key, val in cur.fetchall():
                        ctx["facts_by_cat"].setdefault(cat, []).append((key, val))

                    # Active work items (use_case/feature — drives "Active Features" section)
                    cur.execute(_SQL_ACTIVE_WORK_ITEMS, (project_id,))
                    for wi_id, wi_name, wi_type, user_status, due_date, summary, ac, impl_plan in cur.fetchall():
                        status_label = (
                            _WI_STATUS_LABELS.get(user_status, "open")
                            if user_status is not None else "open"
                        )
                        ctx["active_tags"].append({
                            "name":                 wi_name,
                            "wi_id":                wi_id or "",
                            "wi_type":              wi_type or "",
                            "status":               status_label,
                            "description":          (summary or "").strip(),
                            "acceptance_criteria":  (ac or "").strip(),
                            "implementation_plan":  (impl_plan or "").strip(),
                            "due_date":             due_date.isoformat() if due_date else None,
                        })

                    # In-progress work items — from DB user_status field (accurate, not LLM-derived)
                    try:
                        cur.execute(_SQL_IN_PROGRESS_ITEMS, (project_id,))
                        ctx["in_progress_items"] = [
                            {
                                "wi_id": r[0] or "",
                                "name":  r[1] or "",
                                "type":  r[2] or "",
                                "due":   r[3].isoformat() if r[3] else None,
                            }
                            for r in cur.fetchall()
                        ]
                    except Exception as e:
                        log.debug(f"_load_context in_progress_items error: {e}")

                    # Recently changed symbols (deduplicated, most recent first)
                    try:
                        cur.execute(_SQL_RECENTLY_CHANGED, (project_id,))
                        seen: dict = {}
                        for hash_short, date, fp, stype, cls, meth, change, summary in cur.fetchall():
                            key = (fp, cls or "", meth or "")
                            if key not in seen:
                                if cls and meth:
                                    label = f"{cls}.{meth}"
                                elif cls:
                                    label = cls
                                elif meth:
                                    label = meth
                                else:
                                    label = fp
                                seen[key] = {
                                    "label":   label,
                                    "file":    fp,
                                    "change":  change or "modified",
                                    "hash":    hash_short or "",
                                    "summary": (summary or "")[:80],
                                }
                        ctx["recently_changed"] = list(seen.values())[:50]
                    except Exception as e:
                        log.debug(f"_load_context recently_changed error: {e}")

                    # Code hotspots + file coupling
                    try:
                        threshold = mem_cfg.get("hotspot_threshold", 5)
                        cur.execute(_SQL_HOTSPOTS, (project_id, threshold))
                        ctx["hotspots"] = [
                            {
                                "file":        row[0],
                                "score":       row[1],
                                "commits":     row[2],
                                "lines":       row[3] or 0,
                                "bug_commits": row[4] or 0,
                                "last_changed": row[5].date().isoformat() if row[5] else "",
                            }
                            for row in cur.fetchall()
                        ]
                        cur.execute(_SQL_COUPLING, (project_id, 3))
                        ctx["coupling"] = [
                            {"file_a": row[0], "file_b": row[1], "count": row[2]}
                            for row in cur.fetchall()
                        ]
                    except Exception as e:
                        log.debug(f"_load_context hotspots error: {e}")

        except Exception as e:
            log.warning(f"MemoryFiles._load_context error for '{project}': {e}")

        # Project summary from PROJECT.md — extract Vision + Core Goals sections
        try:
            proj_md_path = self._workspace() / project / "memory" / "PROJECT.md"
            if proj_md_path.exists():
                md_text = proj_md_path.read_text(encoding="utf-8")
                _wanted = {"Vision", "Core Goals"}
                _parts: list[str] = []
                for _section in md_text.split("\n## ")[1:]:
                    _heading = _section.split("\n")[0].strip()
                    if _heading in _wanted:
                        # Strip HTML comments (<!-- user-managed --> etc.)
                        _body = "\n".join(
                            l for l in _section.splitlines()[1:]
                            if l and not l.startswith("<!--")
                        )
                        if _body.strip():
                            _parts.append(f"## {_heading}\n{_body.strip()}")
                ctx["project_summary"] = "\n\n".join(_parts)[:1200]
                # Fallback: first paragraph if no sections found
                if not ctx["project_summary"]:
                    body = md_text.split("\n## ")[0]
                    summary_lines = [
                        l for l in body.splitlines()
                        if l and not l.startswith(("#", ">", "<!--", "_", "```", "|"))
                    ]
                    ctx["project_summary"] = " ".join(summary_lines[:3])[:300]
        except Exception:
            pass

        # Coding conventions + Deprecated section — read from PROJECT.md
        try:
            proj_md_path = self._workspace() / project / "memory" / "PROJECT.md"
            if proj_md_path.exists():
                _md = proj_md_path.read_text(encoding="utf-8")
                _conv_wanted = {"Conventions", "Coding Standards", "Coding Conventions", "Development Standards"}
                deprecated_phrases: list[str] = []
                for _section in _md.split("\n## ")[1:]:
                    _heading = _section.split("\n")[0].strip()
                    if _heading in _conv_wanted:
                        _body = "\n".join(l for l in _section.splitlines()[1:] if not l.startswith("<!--"))
                        ctx["conventions"] = _body.strip()[:800]
                    elif _heading == "Deprecated":
                        # Each non-empty line is a phrase; key_decisions containing it are suppressed
                        import re as _re_dep
                        for _line in _section.splitlines()[1:]:
                            _m = _re_dep.match(r'^-?\s*(.+)', _line.lstrip())
                            if _m:
                                _phrase = _m.group(1).strip()
                                if _phrase and not _phrase.startswith("<!--"):
                                    deprecated_phrases.append(_phrase.lower())
                ctx["deprecated_phrases"] = deprecated_phrases
        except Exception:
            pass

        # Fallback: populate facts_by_cat from project_state.json project_facts
        # when mem_ai_project_facts table is empty (common — table rarely auto-populated)
        if not ctx["facts_by_cat"]:
            pf = state_data.get("project_facts", {})
            for cat, kvs in pf.items():
                if isinstance(kvs, dict):
                    ctx["facts_by_cat"][cat] = list(kvs.items())

        # Code structure (top-level dirs) + store resolved code_dir in ctx
        try:
            code_dir = self._code_dir(project)
            if code_dir and code_dir.exists():
                ctx["code_dir"] = code_dir
                _SKIP = {
                    "__pycache__", "node_modules", "venv", ".git", "dist",
                    "build", ".venv", "old",
                }
                ctx["code_structure"] = sorted(
                    p.name for p in code_dir.iterdir()
                    if p.is_dir() and not p.name.startswith(".") and p.name not in _SKIP
                )[:20]
        except Exception as e:
            log.debug("_load_context code_dir error: %s", e)

        return ctx

    def get_active_feature_tags(self, project: str) -> list[str]:
        """Return names for active use_case/feature work items."""
        if not db.is_available():
            return []
        project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_ACTIVE_WORK_ITEMS, (project_id,))
                    # _SQL_ACTIVE_WORK_ITEMS returns (wi_id, name, wi_type, user_status, due_date)
                    return [r[1] for r in cur.fetchall()]
        except Exception:
            return []

    # ── Renderers ─────────────────────────────────────────────────────────────

    def render_root_claude_md(self, ctx: dict) -> str:
        """Render root CLAUDE.md — Claude CLI auto-loads this."""
        project = ctx["project"]
        ts = ctx["ts"]
        mem_cfg = ctx.get("memory_config", {})
        max_tokens = mem_cfg.get("claude_md_max_tokens", 8000)
        max_recent = mem_cfg.get("recent_work_max_entries", 30)

        # Context age — show when project_state.json was last synced
        state_data = ctx.get("state_data", {})
        state_last_run = state_data.get("last_memory_run") or state_data.get("last_updated", "")
        age_note = f" | Memory synced: {state_last_run[:10]}" if state_last_run else ""
        lines = [f"<!-- Last updated: {ts} -->", f"# {project}", f"_{ts}{age_note}_", ""]

        # Project summary (from PROJECT.md)
        if ctx.get("project_summary"):
            lines += [ctx["project_summary"], ""]

        # Code structure (top-level dirs)
        if ctx.get("code_structure"):
            lines += ["## Structure", ""]
            for d in ctx["code_structure"]:
                lines.append(f"- {d}/")
            lines.append("")

        # Stack & Architecture — from project_state.json (authoritative after /memory run)
        tech_stack = state_data.get("tech_stack", {})
        if tech_stack:
            lines += ["## Stack & Architecture", ""]
            for k, v in list(tech_stack.items())[:15]:
                lines.append(f"- **{k}**: {v}")
            lines.append("")

        # Key Architectural Decisions — from project_state.json
        # Entries matching any phrase in ctx["deprecated_phrases"] are suppressed.
        key_decisions = state_data.get("key_decisions", [])
        deprecated = [p.lower() for p in ctx.get("deprecated_phrases", [])]
        if deprecated:
            key_decisions = [d for d in key_decisions if not any(p in d.lower() for p in deprecated)]
        if key_decisions:
            lines += ["## Key Architectural Decisions", ""]
            for d in key_decisions[:15]:
                lines.append(f"- {d}")
            lines.append("")

        # In Progress — DB user_status='in-progress' (fallback to LLM-derived if DB empty)
        in_progress_db = ctx.get("in_progress_items", [])
        if in_progress_db:
            lines += ["## In Progress", ""]
            for item in in_progress_db:
                due = f" (due {item['due']})" if item.get("due") else ""
                wi_id_part = f"`{item['wi_id']}` " if item.get("wi_id") else ""
                lines.append(f"- {wi_id_part}{item['name']}{due}")
            lines.append("")
        elif state_data.get("in_progress"):
            lines += ["## In Progress", ""]
            for item in state_data["in_progress"][:6]:
                lines.append(f"- {item}")
            lines.append("")

        # Coding Conventions — from PROJECT.md ## Conventions section
        if ctx.get("conventions"):
            lines += ["## Coding Conventions", "", ctx["conventions"], ""]

        # Active Features / Use Cases
        if ctx["active_tags"]:
            lines += ["## Active Features", ""]
            for tag in ctx["active_tags"][:12]:
                due = f" (due {tag['due_date']})" if tag.get("due_date") else ""
                desc = f" — {tag['description']}" if tag.get("description") else ""
                wi_id_part = f"`{tag['wi_id']}` " if tag.get("wi_id") else ""
                lines.append(f"- {wi_id_part}`{tag['name']}` [{tag['status']}]{desc}{due}")
                if tag.get("acceptance_criteria") and tag.get("wi_type") == "use_case":
                    lines.append(f"  _AC: {tag['acceptance_criteria']}_")
                if tag.get("implementation_plan") and tag.get("status") == "in-progress":
                    lines.append(f"  _Plan: {tag['implementation_plan'][:180]}_")
            lines.append("")

        # Code Hotspots
        hotspots = ctx.get("hotspots") or []
        if hotspots:
            lines += ["## Code Hotspots", ""]
            for h in hotspots[:10]:
                bug_note = f", {h['bug_commits']} bug fixes" if h.get("bug_commits") else ""
                lines.append(
                    f"- `{h['file']}` — score {h['score']}"
                    f" ({h['commits']} commits{bug_note}, {h['lines']} lines)"
                )
            lines.append("")

        # Footer (reserved space; placed after recently changed below)
        footer = [
            "---",
            "_Auto-generated by aicli memory system. Run `/memory` to refresh._",
            f"_Last updated: {ts}_",
        ]

        # Recently Changed — token-budget aware (oldest entries roll off first)
        recent = ctx.get("recently_changed") or []
        if recent:
            header_lines = [f"## Recently Changed (last commits)", ""]
            current_text = "\n".join(lines + header_lines + footer)
            budget = max_tokens - self._tokens(current_text) - 20  # 20 token margin

            shown: list[str] = []
            for item in recent[:max_recent]:
                summary_part = f" — {item['summary']}" if item.get("summary") else ""
                entry = f"- `{item['label']}` — {item['change']} in {item['hash']}{summary_part}"
                if budget - self._tokens(entry) < 0:
                    break
                shown.append(entry)
                budget -= self._tokens(entry)

            lines += header_lines + shown
            rolled = len(recent) - len(shown)
            if rolled > 0:
                lines.append(
                    f"_({rolled} older {'entry' if rolled == 1 else 'entries'} rolled off"
                    " — run `git log` for full history)_"
                )
            lines.append("")
        else:
            lines += ["## Recently Changed", "", "(no commit history indexed yet)", ""]

        lines += footer
        return "\n".join(lines)

    def render_feature_claude_md(self, project: str, tag_name: str) -> str:
        """Render per-feature CLAUDE.md — auto-loaded when Claude enters features/{tag}/ dir.

        Reads summary from mem_work_items by name.
        """
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        summary = ""
        if db.is_available():
            try:
                project_id = db.get_or_create_project_id(project)
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "SELECT summary FROM mem_work_items "
                            "WHERE project_id=%s AND name=%s AND deleted_at IS NULL LIMIT 1",
                            (project_id, tag_name),
                        )
                        row = cur.fetchone()
                        if row:
                            summary = row[0] or ""
            except Exception as e:
                log.debug(f"render_feature_claude_md error for '{tag_name}': {e}")

        lines = [f"# Feature: {tag_name}", f"_{ts}_", ""]
        if summary:
            lines += ["## Summary", "", summary, ""]
        lines += ["---", "_Auto-generated by aicli. Run `/memory` to refresh._"]
        return "\n".join(lines)

    def render_cursorrules(self, ctx: dict) -> str:
        """Render .cursorrules — kept under 2000 tokens."""
        project = ctx["project"]
        lines = [f"<!-- Last updated: {ctx['ts']} -->", f"## Project: {project}", ""]

        state_data = ctx.get("state_data", {})

        tech_stack = state_data.get("tech_stack", {})
        if tech_stack:
            lines += ["## Stack", ""]
            for k, v in list(tech_stack.items())[:8]:
                lines.append(f"{k}: {v}")
            lines.append("")

        key_decisions = state_data.get("key_decisions", [])
        deprecated = [p.lower() for p in ctx.get("deprecated_phrases", [])]
        if deprecated:
            key_decisions = [d for d in key_decisions if not any(p in d.lower() for p in deprecated)]
        if key_decisions:
            lines += ["## Key Decisions", ""]
            for d in key_decisions[:8]:
                lines.append(f"- {d}")
            lines.append("")

        # Active features (concise)
        if ctx["active_tags"]:
            lines += ["## Active Features (do not break)", ""]
            for tag in ctx["active_tags"][:5]:
                lines.append(f"{tag['name']}: {tag['description'][:80]}")
            lines.append("")

        in_progress = state_data.get("in_progress", [])
        if in_progress:
            lines += ["## In Progress", ""]
            for item in in_progress[:4]:
                lines.append(f"- {item}")
            lines.append("")

        lines.append(f"_Last updated: {ctx['ts']}_")
        return "\n".join(lines)

    def render_system_compact(self, ctx: dict) -> str:
        """Compact system prompt — for GPT-4 and other small-window models (≤2000 tokens)."""
        project = ctx["project"]
        _preamble = (
            _prompts.content("memory_context_compact")
            or "You are a senior developer working on **{project}**.\n"
               "Respect all project facts below. Never contradict them unless explicitly asked.\n"
               "When working on a specific feature, ask for its snapshot before making decisions."
        ).format(project=project)
        lines = [f"<!-- Last updated: {ctx['ts']} -->"] + _preamble.split("\n") + [""]

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
        active = ctx["active_tags"][:3]
        if active:
            lines += ["## Active Features", ""]
            for tag in active:
                lines.append(f"- {tag['name']} [{tag['status']}]: {tag['description'][:80]}")
            lines.append("")

        return "\n".join(lines)

    def render_system_full(self, ctx: dict) -> str:
        """Full system prompt — for Claude, Deepseek, Gemini (large context window)."""
        project = ctx["project"]
        _preamble = (
            _prompts.content("memory_context_full")
            or "You are a senior developer working on **{project}**.\n"
               "Respect all project facts below. Never contradict them unless explicitly asked.\n"
               "When working on a specific feature, ask for its snapshot before making decisions."
        ).format(project=project)
        lines = [f"<!-- Last updated: {ctx['ts']} -->"] + _preamble.split("\n") + [""]

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
        if ctx["active_tags"]:
            lines += ["## Active Features", ""]
            for tag in ctx["active_tags"]:
                due = f" (due {tag['due_date']})" if tag.get("due_date") else ""
                lines.append(f"- `{tag['name']}` [{tag['status']}]: {tag['description'][:120]}{due}")
            lines.append("")

        return "\n".join(lines)

    def render_openai_system(self, ctx: dict) -> str:
        """System prompt for OpenAI API / Codex CLI (`--system-prompt`).

        Same depth as compact.md but uses OpenAI assistant framing.
        Keep under 2000 tokens.
        """
        project = ctx["project"]
        _preamble = (
            _prompts.content("memory_context_openai")
            or "You are an AI assistant helping develop the **{project}** project.\n"
               "Follow project conventions exactly. Do not introduce new dependencies without approval."
        ).format(project=project)
        lines = [f"<!-- Last updated: {ctx['ts']} -->"] + _preamble.split("\n") + [""]

        stack = (
            ctx["facts_by_cat"].get("stack", []) +
            ctx["facts_by_cat"].get("pattern", [])
        )[:8]
        if stack:
            lines += ["## Tech Stack", ""]
            for key, val in stack:
                lines.append(f"- {key}: {val}")
            lines.append("")

        conventions = ctx["facts_by_cat"].get("convention", [])
        if conventions:
            lines += ["## Conventions", ""]
            for key, val in conventions[:6]:
                lines.append(f"- {key}: {val}")
            lines.append("")

        if ctx["active_tags"]:
            lines += ["## Active Work", ""]
            for tag in ctx["active_tags"][:5]:
                due = f" (due {tag['due_date']})" if tag.get("due_date") else ""
                lines.append(f"- {tag['name']} [{tag['status']}]: {tag['description'][:80]}{due}")
            lines.append("")

        constraints = ctx["facts_by_cat"].get("constraint", [])
        if constraints:
            lines += ["## Never Do", ""]
            for _, val in constraints[:5]:
                lines.append(f"- {val}")
            lines.append("")

        lines += [
            f"_Generated by aicli. Run /memory to refresh. Project: {project}_",
        ]
        return "\n".join(lines)

    def render_gemini_context(self, ctx: dict) -> str:
        """Full Gemini context for Files API upload — all data, verbose."""
        project = ctx["project"]
        ts = ctx["ts"]
        lines = [
            f"<!-- Last updated: {ts} -->",
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

        # Active work items
        if ctx["active_tags"]:
            lines += ["## Active Features", ""]
            for tag in ctx["active_tags"]:
                due = f" (due {tag['due_date']})" if tag.get("due_date") else ""
                lines += [
                    f"### {tag['name']} [{tag['status']}]{due}",
                    "",
                ]

        return "\n".join(lines)

    # dirs/files to skip when building the directory tree
    _TREE_SKIP: frozenset[str] = frozenset({
        "__pycache__", "node_modules", ".git", "dist", "build",
        ".venv", "venv", "old", ".DS_Store", "*.pyc",
    })

    def _render_dir_tree(self, root: Path, max_depth: int = 3) -> list[str]:
        """Return lines of an ASCII directory tree, depth-limited."""
        out: list[str] = [root.name + "/"]

        def _walk(path: Path, prefix: str, depth: int) -> None:
            if depth > max_depth:
                return
            try:
                entries = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            except PermissionError:
                return
            entries = [
                e for e in entries
                if e.name not in self._TREE_SKIP and not e.name.startswith(".")
            ]
            for i, entry in enumerate(entries):
                is_last = i == len(entries) - 1
                connector = "└── " if is_last else "├── "
                label = entry.name + ("/" if entry.is_dir() else "")
                out.append(f"{prefix}{connector}{label}")
                if entry.is_dir():
                    child_prefix = prefix + ("    " if is_last else "│   ")
                    _walk(entry, child_prefix, depth + 1)

        _walk(root, "", 1)
        return out

    def _render_code_md(self, ctx: dict) -> str:
        """Render code/code.md — full code map for LLMs.

        Sections:
          1. Project Structure  — ASCII directory tree (depth 3)
          2. Active Work Items  — open/in-progress features and use-cases
          3. Recently Changed   — last 20 symbol-level changes from commits
          4. Code Hotspots      — files with highest commit frequency
          5. File Coupling      — tightly co-changed file pairs
        """
        project = ctx["project"]
        ts = ctx["ts"]
        lines: list[str] = [
            f"<!-- Last updated: {ts} -->",
            f"# Code Map: {project}",
            f"_Comprehensive code structure — single source for all LLMs. Refresh: `/memory`_",
            "",
        ]

        # ── 1. Project Structure ──────────────────────────────────────────────
        code_dir = ctx.get("code_dir") or self._code_dir(project)
        if code_dir and code_dir.exists():
            lines += ["## Project Structure", "", "```"]
            lines += self._render_dir_tree(code_dir, max_depth=3)
            lines += ["```", ""]

        # ── 2. Active Work Items ──────────────────────────────────────────────
        active_tags = ctx.get("active_tags") or []
        if active_tags:
            lines += ["## Active Work Items", ""]
            for t in active_tags:
                status = t.get("status") or "open"
                due = f"  _(due {t['due_date']})_" if t.get("due_date") else ""
                wi_type = t.get("wi_type") or t.get("type") or ""
                type_tag = f" `{wi_type}`" if wi_type else ""
                lines.append(f"- **[{status}]**{type_tag} {t['name']}{due}")
                if t.get("acceptance_criteria") and wi_type == "use_case":
                    lines.append(f"  _AC: {t['acceptance_criteria']}_")
                if t.get("implementation_plan") and status == "in-progress":
                    lines.append(f"  _Plan: {t['implementation_plan'][:200]}_")
            lines.append("")

        # ── 3. Coding Conventions ─────────────────────────────────────────────
        if ctx.get("conventions"):
            lines += ["## Coding Conventions", "", ctx["conventions"], ""]

        # ── 4. Recently Changed Symbols ───────────────────────────────────────
        recent = ctx.get("recently_changed") or []
        if recent:
            lines += [
                "## Recently Changed",
                "_Last 20 symbol-level changes (class / method / function)._",
                "",
                "| Symbol | Change | Commit | Summary |",
                "|--------|--------|--------|---------|",
            ]
            for r in recent[:20]:
                summary = (r.get("summary") or "").replace("|", "\\|")[:70]
                lines.append(
                    f"| `{r['label']}` | {r['change']} | `{r['hash']}` | {summary} |"
                )
            lines.append("")

        # ── 4. Code Hotspots ──────────────────────────────────────────────────
        hotspots = ctx.get("hotspots") or []
        if hotspots:
            lines += [
                "## Code Hotspots",
                "_Files with highest commit frequency — candidates for refactoring._",
                "",
                "| File | Score | Commits | Lines | Bug Fixes | Last Changed |",
                "|------|-------|---------|-------|-----------|--------------|",
            ]
            for h in hotspots:
                lines.append(
                    f"| `{h['file']}` | {h['score']} | {h['commits']}"
                    f" | {h['lines']} | {h['bug_commits']} | {h['last_changed']} |"
                )
            lines.append("")

        # ── 5. File Coupling ──────────────────────────────────────────────────
        coupling = ctx.get("coupling") or []
        if coupling:
            lines += [
                "## File Coupling",
                "_Files frequently committed together — likely tightly coupled._",
                "",
                "| File A | File B | Co-changes |",
                "|--------|--------|------------|",
            ]
            for c in coupling:
                lines.append(f"| `{c['file_a']}` | `{c['file_b']}` | {c['count']} |")
            lines.append("")

        lines += ["---", "_Generated by aicli. Run `/memory` to refresh._"]
        return "\n".join(lines)

    def _embed_code_md(self, project: str) -> bool:
        """Embed code.md into mem_ai_project_facts for semantic search via MCP.

        Expires the previous code_structure fact and inserts a fresh one.
        No-ops silently if DB is unavailable or embedding imports fail.
        """
        if not db.is_available():
            return False
        try:
            from agents.tools.tool_memory import _embed_sync, _vec_str
        except ImportError:
            return False

        code_md_path = pp.code_md_path(project)
        if not code_md_path.exists():
            return False
        content = code_md_path.read_text(encoding="utf-8")
        if not content.strip():
            return False

        embedding = _embed_sync(content[:8000])
        if not embedding:
            return False

        project_id = db.get_or_create_project_id(project)
        vec = _vec_str(embedding)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE mem_ai_project_facts SET valid_until = NOW() "
                        "WHERE project_id = %s AND fact_key = 'code_structure' AND valid_until IS NULL",
                        (project_id,),
                    )
                    cur.execute(
                        "INSERT INTO mem_ai_project_facts "
                        "(project_id, fact_key, fact_value, category, embedding) "
                        "VALUES (%s, 'code_structure', %s, 'code', %s::vector)",
                        (project_id, content[:8000], vec),
                    )
                conn.commit()
            log.debug("_embed_code_md: embedded code.md for '%s'", project)
            return True
        except Exception as e:
            log.debug("_embed_code_md error for '%s': %s", project, e)
            return False

    def _suggest_hotspot_work_items(
        self, project: str, hotspots: list[dict], mem_cfg: Optional[dict] = None
    ) -> int:
        """Open a refactor task for each hotspot file that has no existing open/active item.

        user_status is a smallint: 0=open, 2=in-progress, 5=done.
        Only creates items for files with no existing non-done entry.
        coupling_threshold comes from project.yaml memory.coupling_threshold (default 8).
        """
        if not db.is_available():
            return 0
        cfg = mem_cfg or {}
        project_id = db.get_or_create_project_id(project)
        created = 0
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # Batch check: which hotspot items already have an active WI?
                    hotspot_names = [f"Refactor {Path(h['file']).name} (hotspot)" for h in hotspots]
                    if hotspot_names:
                        cur.execute(
                            "SELECT name FROM mem_work_items "
                            "WHERE project_id=%s AND name = ANY(%s) "
                            "AND deleted_at IS NULL AND completed_at IS NULL "
                            "AND (user_status IS NULL OR user_status <> 'done')",
                            (project_id, hotspot_names),
                        )
                        existing_hotspots = {r[0] for r in cur.fetchall()}
                    else:
                        existing_hotspots = set()

                    for h in hotspots:
                        wi_name = f"Refactor {Path(h['file']).name} (hotspot)"
                        if wi_name in existing_hotspots:
                            continue
                        cur.execute(
                            "INSERT INTO mem_work_items "
                            "(project_id, name, wi_type, summary, user_status, score_importance) "
                            "VALUES (%s, %s, 'task', %s, 'open', 2)",
                            (
                                project_id,
                                wi_name,
                                f"File `{h['file']}` has hotspot_score={h['score']} "
                                f"({h['commits']} commits, {h['lines']} lines). "
                                "Consider splitting into smaller modules.",
                            ),
                        )
                        created += 1

                    # Auto-suggest decoupling for highly co-changed file pairs
                    coupling_threshold = cfg.get("coupling_threshold", 8)
                    cur.execute(_SQL_COUPLING, (project_id, coupling_threshold))
                    coupling_rows = cur.fetchall()

                    # Batch check coupling pairs
                    coupling_names = [
                        f"Decouple {Path(fa).name} ↔ {Path(fb).name}"
                        for fa, fb, _ in coupling_rows
                    ]
                    if coupling_names:
                        cur.execute(
                            "SELECT name FROM mem_work_items "
                            "WHERE project_id=%s AND name = ANY(%s) "
                            "AND deleted_at IS NULL AND completed_at IS NULL "
                            "AND (user_status IS NULL OR user_status <> 'done')",
                            (project_id, coupling_names),
                        )
                        existing_coupling = {r[0] for r in cur.fetchall()}
                    else:
                        existing_coupling = set()

                    for file_a, file_b, count in coupling_rows:
                        name_a, name_b = Path(file_a).name, Path(file_b).name
                        wi_name = f"Decouple {name_a} ↔ {name_b}"
                        if wi_name in existing_coupling:
                            continue
                        cur.execute(
                            "INSERT INTO mem_work_items "
                            "(project_id, name, wi_type, summary, user_status, score_importance) "
                            "VALUES (%s, %s, 'task', %s, 'open', 1)",
                            (
                                project_id,
                                wi_name,
                                f"`{file_a}` and `{file_b}` were committed together "
                                f"{count} times. Consider extracting shared logic or "
                                "clarifying their interface boundary.",
                            ),
                        )
                        created += 1
                conn.commit()
        except Exception as e:
            log.warning(f"_suggest_hotspot_work_items error: {e}")
        return created

    # ── Writers ───────────────────────────────────────────────────────────────

    def write_code_md(self, project: str) -> bool:
        """Regenerate code.md only — called after each commit to keep hotspots current.

        Cheaper than write_root_files() — reads fresh hotspot/coupling data from DB
        and rewrites just the one file. Returns True if written successfully.
        """
        try:
            ctx = self._load_context(project)
            dest = pp.code_md_path(project)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(self._render_code_md(ctx), encoding="utf-8")
            self._embed_code_md(project)
            return True
        except Exception as e:
            log.warning(f"write_code_md({project}): {e}")
            return False

    def write_root_files(self, project: str, suggest_hotspots: bool = False) -> list[str]:
        """Render and write all root-level context files.

        Returns list of written file paths (relative to workspace).
        """
        ctx = self._load_context(project)
        return self._write_root_files_with_ctx(project, ctx, suggest_hotspots)

    def _write_root_files_with_ctx(  # noqa: C901 (complexity acceptable here)
        self, project: str, ctx: dict, suggest_hotspots: bool = False
    ) -> list[str]:
        """Internal: render + write all root files from an already-loaded context dict."""
        code_dir = self._code_dir(project)
        written: list[str] = []

        # Ensure directories exist
        pp.ensure_project_dirs(project)

        def _write(path: Path, content: str) -> None:
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                written.append(str(path))
            except Exception as e:
                log.warning(f"write_root_files: failed to write {path}: {e}")

        # Load provider mapping
        providers = self._load_providers()
        cli_tools = {t["id"]: t for t in providers.get("cli_tools", [])}

        # ── Primary memory files ──────────────────────────────────────────────
        claude_content = self.render_root_claude_md(ctx)
        cursor_content = self.render_cursorrules(ctx)
        api_content    = self.render_system_compact(ctx)

        _write(pp.claude_md_path(project),              claude_content)
        _write(pp.cursor_rules_path(project),           cursor_content)
        _write(pp.copilot_instructions_path(project),   cursor_content)
        _write(pp.api_system_prompt_path(project),      api_content)

        # Mirror files for Gemini CLI and Codex CLI (same content as CLAUDE.md)
        _write(pp.memory_dir(project) / "GEMINI.md", claude_content)
        _write(pp.memory_dir(project) / "AGENTS.md", claude_content)

        # Code intelligence file
        _write(pp.code_md_path(project), self._render_code_md(ctx))

        # ── Copy to code_dir (driven by providers config) ─────────────────────
        if code_dir and code_dir.exists():
            # Build content map: tier → content
            content_map = {"claude_code": claude_content, "cursor": cursor_content}
            for tool in providers.get("cli_tools", []):
                copy_to = tool.get("copy_to_code_dir")
                if not copy_to:
                    continue
                # Resolve content: own render or copy from source
                src_id = tool.get("source") or tool["id"]
                content = content_map.get(src_id)
                if content is None:
                    continue
                dest = code_dir / copy_to
                _write(dest, content)

            # Fallback: always write CLAUDE.md and .cursorrules if providers.yaml missing
            if not cli_tools:
                _write(code_dir / "CLAUDE.md", claude_content)
                _write(code_dir / ".cursorrules", cursor_content)

        # Clean up old pipeline run logs and history archives
        try:
            # Use already-loaded memory config from ctx — avoids re-reading project.yaml
            _log_cfg = mem_cfg.get("logs", {}) if isinstance(mem_cfg, dict) else {}
            _pipe_days = int(_log_cfg.get("pipeline_retention_days", 14))
            _hist_days = int(_log_cfg.get("history_retention_days", 30))
            _deleted = pp.cleanup_project_logs(project, pipeline_days=_pipe_days, history_days=_hist_days)
            if _deleted:
                log.info("write_root_files: cleaned %d stale log file(s) for '%s'", _deleted, project)
        except Exception as _ce:
            log.debug("write_root_files: log cleanup error: %s", _ce)

        # Auto-suggest refactor/decouple tasks from hotspot + coupling data
        mem_cfg = ctx.get("memory_config", {})
        if suggest_hotspots and mem_cfg.get("hotspot_suggest_work_item", True):
            created = self._suggest_hotspot_work_items(project, ctx.get("hotspots", []), mem_cfg)
            if created:
                log.info(f"MemoryFiles: created {created} hotspot/coupling task(s) for '{project}'")

        # Embed code.md for semantic search via MCP search_facts
        self._embed_code_md(project)

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

        # Write to cli/claude/features/ for archive
        sys_feature_path = pp.claude_dir(project) / "features" / tag_name / "CLAUDE.md"
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
        """Write root files + all active feature files. Called by /memory POST."""
        ctx = self._load_context(project)
        # Re-use the already-loaded active_tags from ctx — avoids a second DB round-trip
        written = self._write_root_files_with_ctx(project, ctx, suggest_hotspots=True)
        for tag in ctx.get("active_tags", []):
            if tag.get("name"):
                written.extend(self.write_feature_files(project, tag["name"]))
        return written

    def _write_root_files_with_ctx(
        self, project: str, ctx: dict, suggest_hotspots: bool = False
    ) -> list[str]:
        """Internal: render and write all root-level context files from a pre-loaded ctx."""
