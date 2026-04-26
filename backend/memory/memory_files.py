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

from core.database import db
from core.config import settings
from core.prompt_loader import prompts as _prompts

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
    SELECT wi_id, name, wi_type, user_status, due_date
    FROM mem_work_items
    WHERE project_id = %s
      AND wi_type IN ('use_case', 'feature')
      AND deleted_at IS NULL
      AND completed_at IS NULL
    ORDER BY score_importance DESC NULLS LAST, created_at DESC
    LIMIT 20
"""

_SQL_RECENTLY_CHANGED = """
    SELECT c.commit_hash_short, c.created_at::date AS commit_date,
           cc.file_path, cc.symbol_type, cc.class_name, cc.method_name,
           cc.file_change, cc.llm_summary
    FROM mem_mrr_commits c
    JOIN mem_mrr_commits_code cc ON cc.commit_hash = c.commit_hash
    WHERE c.project_id = %s
    ORDER BY c.created_at DESC
    LIMIT 200
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
            "active_tags":      [],      # list of dicts from mem_work_items (use_case/feature)
            "recently_changed": [],      # recently changed symbols from commits
            "project_summary":  "",      # first lines from PROJECT.md
            "code_structure":   [],      # top-level dirs in code_dir
            "ts":               datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        }
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
                    for wi_id, wi_name, wi_type, user_status, due_date in cur.fetchall():
                        ctx["active_tags"].append({
                            "name":        wi_name,
                            "status":      user_status or wi_type or "open",
                            "description": "",
                            "due_date":    due_date.isoformat() if due_date else None,
                        })

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

        except Exception as e:
            log.warning(f"MemoryFiles._load_context error for '{project}': {e}")

        # Project summary from PROJECT.md
        try:
            proj_md_path = self._workspace() / project / "PROJECT.md"
            if proj_md_path.exists():
                md_text = proj_md_path.read_text(encoding="utf-8")
                body = md_text.split("\n## ")[0]
                summary_lines = [
                    l for l in body.splitlines()
                    if l and not l.startswith(("#", ">", "<!--", "_", "```", "|"))
                ]
                ctx["project_summary"] = " ".join(summary_lines[:3])[:300]
        except Exception:
            pass

        # Code structure (top-level dirs)
        try:
            code_dir = self._code_dir(project)
            if code_dir and code_dir.exists():
                _SKIP = {
                    "__pycache__", "node_modules", "venv", ".git", "dist",
                    "build", ".venv", "old",
                }
                ctx["code_structure"] = sorted(
                    p.name for p in code_dir.iterdir()
                    if p.is_dir() and not p.name.startswith(".") and p.name not in _SKIP
                )[:20]
        except Exception:
            pass

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
        lines = [f"# {project}", ""]

        # Project summary (from PROJECT.md)
        if ctx.get("project_summary"):
            lines += [ctx["project_summary"], ""]

        # Code structure (top-level dirs)
        if ctx.get("code_structure"):
            lines += ["## Structure", ""]
            for d in ctx["code_structure"]:
                lines.append(f"- {d}/")
            lines.append("")

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

        # Active Features / Use Cases
        if ctx["active_tags"]:
            lines += ["## Active Features", ""]
            for tag in ctx["active_tags"][:12]:
                due = f" (due {tag['due_date']})" if tag.get("due_date") else ""
                desc = f" — {tag['description']}" if tag.get("description") else ""
                lines.append(f"- `{tag['name']}` [{tag['status']}]{desc}{due}")
            lines.append("")

        # Recently Changed
        recent = ctx.get("recently_changed") or []
        if recent:
            lines += [f"## Recently Changed (last commits)", ""]
            shown = recent[:30]
            for item in shown:
                summary_part = f" — {item['summary']}" if item.get("summary") else ""
                lines.append(
                    f"- `{item['label']}` — {item['change']} in {item['hash']}{summary_part}"
                )
            if len(recent) > 30:
                lines.append(f"(+ {len(recent) - 30} more — see git log)")
            lines.append("")
        else:
            lines += ["## Recently Changed", "", "(no commit history indexed yet)", ""]

        # Conventions
        conv_facts = ctx["facts_by_cat"].get("convention", [])
        if conv_facts:
            lines += ["## Conventions & Decisions", ""]
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

        # Memory reference footer
        lines += [
            "---",
            "_Auto-generated by aicli memory system. Run `/memory` to refresh._",
            f"_Last updated: {ctx['ts']}_",
        ]

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

        # Active features (concise)
        if ctx["active_tags"]:
            lines += ["## Active Features (do not break)", ""]
            for tag in ctx["active_tags"][:5]:
                lines.append(f"{tag['name']}: {tag['description'][:80]}")
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
        _preamble = (
            _prompts.content("memory_context_compact")
            or "You are a senior developer working on **{project}**.\n"
               "Respect all project facts below. Never contradict them unless explicitly asked.\n"
               "When working on a specific feature, ask for its snapshot before making decisions."
        ).format(project=project)
        lines = _preamble.split("\n") + [""]

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
        lines = _preamble.split("\n") + [""]

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
        lines = _preamble.split("\n") + [""]

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
        (sys_dir / "openai").mkdir(parents=True, exist_ok=True)

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
        _write(sys_dir / "llm_prompts" / "compact.md",        self.render_system_compact(ctx))
        _write(sys_dir / "llm_prompts" / "full.md",           self.render_system_full(ctx))
        _write(sys_dir / "llm_prompts" / "gemini_context.md", self.render_gemini_context(ctx))
        _write(sys_dir / "llm_prompts" / "openai.md",         self.render_openai_system(ctx))
        _write(sys_dir / "openai" / "system_prompt.md",       self.render_openai_system(ctx))

        # Copy to code_dir
        if code_dir and code_dir.exists():
            _write(code_dir / "CLAUDE.md", claude_content)
            _write(code_dir / ".cursorrules", self.render_cursorrules(ctx))

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
