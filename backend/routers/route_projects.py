"""
Projects router — list/create/switch projects from templates.
f"""

import asyncio
import json
import logging
import re
import shutil
import time
import yaml
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from core.config import settings
from core.database import db

# ── SQL ──────────────────────────────────────────────────────────────────────

_SQL_GET_ENTITY_SUMMARY = (
    """SELECT tc.name AS category, tc.icon,
              t.id::text, t.name,
              COALESCE(t.description, '') AS description,
              t.status, t.due_date, t.parent_id::text,
              0 AS event_count,
              0 AS commit_count
       FROM mng_tags_categories tc
       JOIN planner_tags t ON t.category_id = tc.id AND t.project_id=%s
       WHERE t.status != 'archived'
       ORDER BY tc.name, t.status"""
)




_SQL_GET_EXISTING_ENTITY_VALUES = (
    """SELECT id::text, name FROM planner_tags
       WHERE project_id=%s AND status='active'
       ORDER BY name LIMIT 50"""
)


_SQL_COUNT_INTERACTIONS_TOTAL = (
    "SELECT COUNT(*) FROM mem_mrr_prompts WHERE project_id=%s"
)

_SQL_COUNT_INTERACTIONS_SINCE = (
    "SELECT COUNT(*) FROM mem_mrr_prompts WHERE project_id=%s AND created_at > %s::timestamptz"
)

_SQL_GET_UNPROCESSED_ITEMS = (
    """SELECT id::text FROM mem_mrr_items
       WHERE project_id=%s
       ORDER BY created_at DESC LIMIT 20"""
)

_SQL_GET_UNPROCESSED_MESSAGES = (
    """SELECT id::text FROM mem_mrr_messages
       WHERE project_id=%s
       ORDER BY created_at DESC LIMIT 20"""
)

_SQL_GET_ACTIVE_PLANNER_TAGS = (
    """SELECT name FROM planner_tags
       WHERE project_id=%s AND status IN ('open', 'active')
       ORDER BY updated_at DESC LIMIT 10"""
)

# ─────────────────────────────────────────────────────────────────────────────

router = APIRouter()
log = logging.getLogger(__name__)

# Absolute path to the aicli root dir (backend/routers/projects.py → 3 levels up)
_AICLI_DIR = Path(__file__).parent.parent.parent

# 60-second in-process cache for memory-status (avoids scanning history.jsonl on every tab open)
_MEMORY_STATUS_CACHE: dict[str, tuple[float, dict]] = {}   # project → (timestamp, result)
_MEMORY_STATUS_TTL = 60.0  # seconds

# ── History rotation ──────────────────────────────────────────────────────────

def _rotate_history(sys_dir: Path, max_rows: int = 500) -> dict:
    """Rotate history.jsonl when it exceeds max_rows.

    Keeps the most recent max_rows entries in history.jsonl.
    Archives older entries to history_YYMMDDHHMM.jsonl (named from the first
    entry's timestamp so the filename reflects the period it covers).

    Returns a dict with rotation metadata (rotated, archived_to, rows_kept, rows_archived).
    Called during /memory so the DB has already imported older entries via _do_sync_events.
    """
    hist = sys_dir / "history.jsonl"
    if not hist.exists():
        return {"rotated": False}
    lines = [ln for ln in hist.read_text().splitlines() if ln.strip()]
    if len(lines) <= max_rows:
        return {"rotated": False, "total_rows": len(lines)}

    archive_lines = lines[:-max_rows]
    keep_lines    = lines[-max_rows:]

    # Name the archive after the first (oldest) entry's timestamp
    suffix = datetime.utcnow().strftime("%y%m%d%H%M")
    try:
        first = json.loads(archive_lines[0])
        ts_raw = first.get("ts", "")
        if ts_raw:
            dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            suffix = dt.strftime("%y%m%d%H%M")
    except Exception:
        pass

    archive_path = sys_dir / f"history_{suffix}.jsonl"
    # Avoid overwriting if file already exists (e.g. two rotations same minute)
    counter = 0
    while archive_path.exists():
        counter += 1
        archive_path = sys_dir / f"history_{suffix}_{counter}.jsonl"

    archive_path.write_text("\n".join(archive_lines) + "\n")
    hist.write_text("\n".join(keep_lines) + "\n")

    log.info(f"Rotated history.jsonl: {len(archive_lines)} rows → {archive_path.name}, "
             f"{len(keep_lines)} rows kept")
    return {
        "rotated":        True,
        "archived_to":    archive_path.name,
        "rows_archived":  len(archive_lines),
        "rows_kept":      len(keep_lines),
    }


# ── Noise filtering ───────────────────────────────────────────────────────────

_NOISE_PATTERNS = ["<task-notification>", "<tool-use-id>", "<task-id>", "<parameter>"]

def _is_noisy(entry: dict) -> bool:
    """Return True only when the entry IS a noise message (starts with XML tag).

    Uses startswith so user messages that discuss these tags are never filtered.
    """
    txt = (entry.get("user_input") or "").strip()
    return any(txt.startswith(p) for p in _NOISE_PATTERNS)


def _workspace() -> Path:
    return Path(settings.workspace_dir)


def _find_claude_md(sys_dir: Path) -> Path:
    """Return path to CLAUDE.md — new per-LLM location first, then legacy fallback."""
    new = sys_dir / "claude" / "CLAUDE.md"
    if new.exists():
        return new
    return sys_dir / "CLAUDE.md"  # legacy


def _ensure_per_llm_dirs(sys_dir: Path) -> None:
    """Create the per-LLM subdirectories and migrate legacy CLAUDE.md if needed."""
    for subdir in ("claude", "cursor", "aicli", "hooks"):
        (sys_dir / subdir).mkdir(parents=True, exist_ok=True)
    # Migrate legacy _system/CLAUDE.md → _system/claude/CLAUDE.md
    legacy = sys_dir / "CLAUDE.md"
    new = sys_dir / "claude" / "CLAUDE.md"
    if legacy.exists() and not new.exists():
        shutil.copy2(str(legacy), str(new))
    # Create empty stubs if missing
    for stub in [sys_dir / "claude" / "MEMORY.md", sys_dir / "cursor" / "rules.md", sys_dir / "aicli" / "context.md"]:
        if not stub.exists():
            stub.write_text("")


@router.get("/")
async def list_projects():
    """List all project workspaces. Reads from mng_projects when DB is available, falls back to filesystem."""
    ws = _workspace()

    # DB-primary: read from mng_projects
    if db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT name, description, code_dir, default_provider,
                               is_active, created_at, workspace_path
                        FROM mng_projects WHERE client_id=1 AND name != '_global'
                        ORDER BY name
                    """)
                    db_projects = cur.fetchall()
            projects = []
            for row in db_projects:
                name, description, code_dir, default_provider, is_active, created_at, workspace_path = row
                projects.append({
                    "name": name,
                    "description": description or "",
                    "code_dir": code_dir or "",
                    "default_provider": default_provider or "claude",
                    "is_active": is_active,
                    "active": name == settings.active_project,
                })
            return {"projects": projects, "active": settings.active_project}
        except Exception as _e:
            log.warning("list_projects: DB query failed, falling back to filesystem: %s", _e)

    # Filesystem fallback
    if not ws.exists():
        return {"projects": []}

    projects = []
    for d in sorted(ws.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        proj_yaml = d / "project.yaml"
        info: dict = {"name": d.name, "active": d.name == settings.active_project}
        if proj_yaml.exists():
            try:
                data = yaml.safe_load(proj_yaml.read_text()) or {}
                info["description"] = data.get("description", "")
                info["default_provider"] = data.get("default_provider", "claude")
            except Exception:
                pass
        projects.append(info)

    return {"projects": projects, "active": settings.active_project}


@router.get("/templates")
async def list_templates():
    """List available project templates (from _templates/starters/)."""
    templates_dir = _workspace() / "_templates" / "starters"
    if not templates_dir.exists():
        return {"templates": []}

    templates = []
    for d in sorted(templates_dir.iterdir()):
        if d.is_dir():
            proj_yaml = d / "project.yaml"
            info: dict = {"name": d.name}
            if proj_yaml.exists():
                try:
                    data = yaml.safe_load(proj_yaml.read_text()) or {}
                    info["description"] = data.get("description", "")
                except Exception:
                    pass
            templates.append(info)
    return {"templates": templates}


class NewProject(BaseModel):
    name: str
    template: str = "default"
    code_dir: str = ""
    description: str = ""
    default_provider: str = "claude"
    # IDE / tool integrations
    claude_cli_support: bool = False   # hooks + .mcp.json for Claude CLI / Claude Code
    cursor_support: bool = False       # .cursor/rules + .cursor/mcp.json
    # API-based providers (context injected via aicli CLI; saves to project.yaml)
    openai_support: bool = False
    deepseek_support: bool = False
    gemini_support: bool = False
    grok_support: bool = False
    git_config: dict = {}


@router.post("/")
async def create_project(body: NewProject):
    """Create a new project from a template."""
    ws = _workspace()
    template_dir = ws / "_templates" / "starters" / body.template
    dest_dir = ws / body.name

    if not template_dir.exists():
        raise HTTPException(status_code=404, detail=f"Template not found: {body.template}")
    if dest_dir.exists():
        raise HTTPException(status_code=409, detail=f"Project already exists: {body.name}")

    # Copy the starter template content directly
    shutil.copytree(template_dir, dest_dir)

    # Replace template vars
    today = datetime.utcnow().strftime("%Y-%m-%d")
    for path in dest_dir.rglob("*.yaml"):
        try:
            content = path.read_text()
            content = content.replace("{{PROJECT_NAME}}", body.name)
            content = content.replace("{{DATE}}", today)
            if body.code_dir:
                content = content.replace("../../{{PROJECT_NAME}}", body.code_dir)
            path.write_text(content)
        except Exception:
            pass

    for path in dest_dir.rglob("*.md"):
        try:
            content = path.read_text()
            content = content.replace("{{PROJECT_NAME}}", body.name)
            content = content.replace("{{DATE}}", today)
            path.write_text(content)
        except Exception:
            pass

    # Create documents folder
    docs_dir = dest_dir / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "README.md").write_text(
        f"# {body.name} — Documents\n\nProject documents go here. "
        "Workflow outputs are saved automatically when runs are linked to a work item.\n"
    )

    # Create per-LLM _system/ directories and stubs
    sys_dir = dest_dir / "_system"
    _ensure_per_llm_dirs(sys_dir)

    # Merge extra fields into project.yaml
    extra: dict = {}
    if body.description:
        extra["description"] = body.description
    if body.default_provider:
        extra["default_provider"] = body.default_provider
    if body.code_dir:
        extra["code_dir"] = body.code_dir
    if body.claude_cli_support:
        extra["claude_cli_support"] = True
    if body.cursor_support:
        extra["cursor_support"] = True
    # Record enabled API providers
    enabled_providers = [p for p, flag in [
        ("openai", body.openai_support), ("deepseek", body.deepseek_support),
        ("gemini", body.gemini_support), ("grok", body.grok_support),
    ] if flag]
    if enabled_providers:
        extra["enabled_api_providers"] = enabled_providers
    if extra:
        proj_yaml = dest_dir / "project.yaml"
        existing: dict = {}
        if proj_yaml.exists():
            try:
                existing = yaml.safe_load(proj_yaml.read_text()) or {}
            except Exception:
                pass
        existing.update(extra)
        proj_yaml.write_text(yaml.dump(existing, default_flow_style=False, allow_unicode=True))

    # IDE support setup
    setup_results: dict = {}
    if body.code_dir:
        code_path = Path(body.code_dir)
        claude_src = ws / "_templates" / "cli" / "claude"
        mcp_tpl_path = ws / "_templates" / "cli" / "mcp.template.json"

        def _render_tpl(tpl_file: Path) -> str:
            return (tpl_file.read_text()
                    .replace("{{WORKSPACE_DIR}}", str(ws))
                    .replace("{{PROJECT_NAME}}", body.name)
                    .replace("{{AICLI_DIR}}", str(_AICLI_DIR)))

        if body.claude_cli_support and claude_src.exists():
            # Install hooks into _system/hooks/
            hooks_dest = sys_dir / "hooks"
            hooks_dest.mkdir(parents=True, exist_ok=True)
            hooks_dir = claude_src / "hooks"
            for sh in hooks_dir.glob("*.sh"):
                shutil.copy2(str(sh), str(hooks_dest / sh.name))
            # Render settings.template.json → {code_dir}/.claude/settings.local.json
            tpl_file = claude_src / "settings.template.json"
            if tpl_file.exists():
                settings_dir = code_path / ".claude"
                settings_dir.mkdir(parents=True, exist_ok=True)
                (settings_dir / "settings.local.json").write_text(_render_tpl(tpl_file))
            # Render mcp.template.json → {code_dir}/.mcp.json  (Claude Code + Claude CLI)
            if mcp_tpl_path.exists():
                (code_path / ".mcp.json").write_text(_render_tpl(mcp_tpl_path))
            setup_results["claude_cli"] = str(hooks_dest)
            setup_results["claude_mcp"] = str(code_path / ".mcp.json")

        if body.cursor_support:
            cursor_rules_dir = code_path / ".cursor" / "rules"
            cursor_rules_dir.mkdir(parents=True, exist_ok=True)
            # Initial rules stub (refreshed on every /memory call)
            proj_md = dest_dir / "PROJECT.md"
            proj_summary = proj_md.read_text()[:400] if proj_md.exists() else ""
            rules_content = f"# AI Rules — {body.name}\n> Managed by aicli. Re-run `/memory` to refresh.\n\n## Project\n{proj_summary}\n"
            (cursor_rules_dir / "aicli.mdrules").write_text(rules_content)
            # Render shared mcp.template.json → {code_dir}/.cursor/mcp.json
            if mcp_tpl_path.exists():
                cursor_mcp_dir = code_path / ".cursor"
                cursor_mcp_dir.mkdir(parents=True, exist_ok=True)
                (cursor_mcp_dir / "mcp.json").write_text(_render_tpl(mcp_tpl_path))
            setup_results["cursor"] = str(cursor_rules_dir)
            setup_results["cursor_mcp"] = str(code_path / ".cursor" / "mcp.json")

    # Tables are pre-created at startup; no per-project schema call needed.

    return {
        "created": body.name,
        "template": body.template,
        "path": str(dest_dir),
        "setup": setup_results,
    }


@router.post("/switch/{project_name}")
async def switch_project(project_name: str):
    """Switch the active project (updates in-memory settings)."""
    proj_dir = _workspace() / project_name
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    settings.active_project = project_name
    return {"active_project": project_name}


@router.get("/{project_name}/config")
async def get_project_config(project_name: str):
    """Get project.yaml contents as JSON."""
    proj_yaml = _workspace() / project_name / "project.yaml"
    if not proj_yaml.exists():
        raise HTTPException(status_code=404, detail=f"No project.yaml for: {project_name}")
    try:
        data = yaml.safe_load(proj_yaml.read_text()) or {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return data


@router.put("/{project_name}/config")
async def update_project_config(project_name: str, body: dict = Body(...)):
    """Merge fields into project.yaml. Accepts a plain JSON object."""
    proj_dir = _workspace() / project_name
    proj_yaml = proj_dir / "project.yaml"
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    existing: dict = {}
    if proj_yaml.exists():
        try:
            existing = yaml.safe_load(proj_yaml.read_text()) or {}
        except Exception:
            pass

    existing.update(body)
    proj_yaml.write_text(yaml.dump(existing, default_flow_style=False, allow_unicode=True))
    return {"updated": project_name, "config": existing}


class CommandRequest(BaseModel):
    command: str
    cwd: str = ""


@router.post("/{project_name}/run-command")
async def run_command(project_name: str, body: CommandRequest):
    """Run a shell command in the project's code directory."""
    proj_dir = _workspace() / project_name
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    # Resolve working dir — prefer explicit cwd, then code_dir from yaml, then project dir
    cwd = body.cwd
    if not cwd:
        try:
            data = yaml.safe_load((proj_dir / "project.yaml").read_text()) or {}
            cwd = data.get("code_dir", "")
        except Exception:
            pass
    if not cwd or not Path(cwd).exists():
        cwd = str(proj_dir)

    try:
        proc = await asyncio.create_subprocess_shell(
            body.command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
        output = stdout.decode(errors="replace")
        return {
            "command": body.command,
            "cwd": cwd,
            "exit_code": proc.returncode,
            "output": output,
        }
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Command timed out (60s limit)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_name}/context")
async def get_project_context(project_name: str, save: bool = False):
    """Generate a CONTEXT.md from PROJECT.md + project_state.json + recent history.
    Pass ?save=true to write CONTEXT.md to the project directory.
    """
    proj_dir = _workspace() / project_name
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    # 1. project.yaml — config
    cfg: dict = {}
    if (proj_dir / "project.yaml").exists():
        try:
            cfg = yaml.safe_load((proj_dir / "project.yaml").read_text()) or {}
        except Exception:
            pass

    # 2. PROJECT.md — full living doc
    project_md = ""
    if (proj_dir / "PROJECT.md").exists():
        project_md = (proj_dir / "PROJECT.md").read_text()

    sys_dir = proj_dir / "_system"

    # 3. project_state.json — structured metadata (in _system/)
    state_data: dict = {}
    for p in [sys_dir / "project_state.json", proj_dir / "project_state.json"]:
        if p.exists():
            try:
                state_data = json.loads(p.read_text())
                break
            except Exception:
                pass

    # 4. Recent history — last 15 exchanges (in _system/), excluding noisy entries
    recent: list[dict] = []
    for hist_file in [sys_dir / "history.jsonl", proj_dir / "history" / "history.jsonl"]:
        if hist_file.exists():
            with open(hist_file) as f:
                lines = [l.strip() for l in f if l.strip()]
            for line in lines[-60:]:
                try:
                    e = json.loads(line)
                    if e.get("user_input") and not _is_noisy(e):
                        recent.append(e)
                except Exception:
                    pass
            recent = recent[-15:]
            break

    # 5. Runtime state (in _system/)
    runtime: dict = {}
    for p in [sys_dir / "dev_runtime_state.json", proj_dir / "dev_runtime_state.json"]:
        if p.exists():
            try:
                runtime = json.loads(p.read_text())
                break
            except Exception:
                pass

    # Build CONTEXT.md
    lines_out: list[str] = []
    lines_out.append(f"# Project Context: {project_name}")
    lines_out.append(f"\n> Auto-generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC — do not edit manually.\n")

    # Quick stats
    lines_out.append("## Quick Stats\n")
    if cfg:
        lines_out.append(f"- **Provider**: {cfg.get('default_provider', 'claude')}")
        if cfg.get("github_repo"):
            lines_out.append(f"- **GitHub**: {cfg['github_repo']}")
        if cfg.get("code_dir"):
            lines_out.append(f"- **Code dir**: `{cfg['code_dir']}`")
    if runtime:
        lines_out.append(f"- **Sessions**: {runtime.get('session_count', 0)}")
        lines_out.append(f"- **Last active**: {runtime.get('last_updated', '—')}")
        lines_out.append(f"- **Last provider**: {runtime.get('last_provider', '—')}")
    if state_data.get("version"):
        lines_out.append(f"- **Version**: {state_data['version']}")

    # Tech stack (from project_state.json)
    if state_data.get("tech_stack"):
        lines_out.append("\n## Tech Stack\n")
        for k, v in state_data["tech_stack"].items():
            lines_out.append(f"- **{k}**: {v}")

    # In-progress items
    if state_data.get("in_progress"):
        lines_out.append("\n## In Progress\n")
        for item in state_data["in_progress"]:
            lines_out.append(f"- {item}")

    # Key decisions
    if state_data.get("key_decisions"):
        lines_out.append("\n## Key Decisions\n")
        for d in state_data["key_decisions"]:
            lines_out.append(f"- {d}")

    # PROJECT.md (abridged — first 80 lines for context)
    if project_md:
        lines_out.append("\n---\n\n## Project Documentation (PROJECT.md)\n")
        md_lines = project_md.splitlines()[:80]
        lines_out.append("\n".join(md_lines))
        if len(project_md.splitlines()) > 80:
            lines_out.append(f"\n\n*...{len(project_md.splitlines()) - 80} more lines in PROJECT.md*")

    # Recent history
    if recent:
        lines_out.append("\n---\n\n## Recent Development History\n")
        for e in reversed(recent):
            ts = e.get("ts", "")[:16].replace("T", " ")
            src = e.get("source", "")
            prov = e.get("provider", "")
            user_in = (e.get("user_input") or "")[:120].replace("\n", " ")
            out = (e.get("output") or "")[:200].replace("\n", " ")
            lines_out.append(f"**[{ts}]** `{src}/{prov}`  ")
            lines_out.append(f"→ {user_in}")
            if out:
                lines_out.append(f"← _{out}_")
            lines_out.append("")

    context_md = "\n".join(lines_out)

    # Build CLAUDE.md — lean version for CLI (role + key decisions + abridged project summary)
    claude_lines: list[str] = []

    # Role section: embed from prompts/roles/ if a default role exists, else generic
    role_file = proj_dir / "prompts" / "roles" / "architect.md"
    if not role_file.exists():
        # Try any role file
        roles = list((proj_dir / "prompts" / "roles").glob("*.md")) if (proj_dir / "prompts" / "roles").exists() else []
        role_file = roles[0] if roles else None

    if role_file and role_file.exists():
        claude_lines.append(role_file.read_text().strip())
    else:
        claude_lines.append(f"# Role: Developer — {project_name}\n\nYou are working on **{project_name}**.")

    # Key decisions
    if state_data.get("key_decisions"):
        claude_lines.append("\n## Key Architectural Decisions\n")
        for d in state_data["key_decisions"]:
            claude_lines.append(f"- {d}")

    # Abridged PROJECT.md (first 60 lines)
    if project_md:
        claude_lines.append("\n---\n\n## Project Documentation\n")
        claude_lines.append("\n".join(project_md.splitlines()[:60]))
        if len(project_md.splitlines()) > 60:
            claude_lines.append(f"\n\n*See PROJECT.md for full documentation ({len(project_md.splitlines())} lines total)*")

    # Recent prompts (last 5 — gives CLI users context of recent work)
    if recent:
        claude_lines.append("\n## Recent Work (last 5 prompts)\n")
        for e in recent[-5:]:
            ts = e.get("ts", "")[:10]
            user_in = (e.get("user_input") or "")[:100].replace("\n", " ")
            src = e.get("source", "")
            claude_lines.append(f"- [{ts}] `{src}`: {user_in}")

    claude_lines.append(f"\n---\n*Full context: see `_system/CONTEXT.md` — refresh with `GET /projects/{project_name}/context?save=true`*")
    claude_md = "\n".join(claude_lines)

    if save:
        sys_dir.mkdir(parents=True, exist_ok=True)
        # Migrate to per-LLM structure if needed
        _ensure_per_llm_dirs(sys_dir)
        (sys_dir / "CONTEXT.md").write_text(context_md)
        # Write to new location; also keep legacy for backward compat
        (sys_dir / "claude" / "CLAUDE.md").write_text(claude_md)
        (sys_dir / "CLAUDE.md").write_text(claude_md)

        # Copy CLAUDE.md to code_dir root so Claude Code CLI finds it
        code_dir = cfg.get("code_dir", "")
        if code_dir:
            code_path = Path(code_dir)
            if not code_path.is_absolute():
                code_path = proj_dir / code_path
            code_path = code_path.resolve()
            if code_path.exists() and code_path.is_dir():
                try:
                    (code_path / "CLAUDE.md").write_text(claude_md)
                except Exception:
                    pass  # Don't fail if code_dir is read-only

    return {"context": context_md, "claude_md": claude_md, "saved": save}


@router.get("/{project_name}/summary")
async def get_project_summary(project_name: str):
    """Get PROJECT.md content from project root."""
    proj_dir = _workspace() / project_name
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")
    proj_md = proj_dir / "PROJECT.md"
    if not proj_md.exists():
        raise HTTPException(status_code=404, detail="PROJECT.md not found")
    return {"content": proj_md.read_text(), "path": "PROJECT.md"}


@router.put("/{project_name}/summary")
async def update_project_summary(project_name: str, body: dict = Body(...)):
    """Write PROJECT.md at project root."""
    proj_dir = _workspace() / project_name
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")
    content = body.get("content", "")
    (proj_dir / "PROJECT.md").write_text(content)
    return {"saved": True}


# ── Memory generation helpers ─────────────────────────────────────────────────

def _save_project_state(sys_dir: Path, state_data: dict) -> None:
    """Persist updated project_state.json to _system/ directory."""
    try:
        state_path = sys_dir / "project_state.json"
        state_path.write_text(json.dumps(state_data, indent=2, ensure_ascii=False))
    except Exception:
        pass


def _update_project_md_section(proj_dir: Path, section_title: str, new_body: str) -> None:
    """Update or append a '## {section_title}' section in PROJECT.md without touching other content."""
    try:
        proj_md_path = proj_dir / "PROJECT.md"
        if not proj_md_path.exists():
            return
        content = proj_md_path.read_text()
        marker = f"## {section_title}"
        if marker in content:
            before, rest = content.split(marker, 1)
            next_h2 = re.search(r"\n## ", rest)
            after = rest[next_h2.start():] if next_h2 else ""
            content = before + marker + "\n\n" + new_body.rstrip() + "\n" + after
        else:
            content = content.rstrip() + "\n\n" + marker + "\n\n" + new_body.rstrip() + "\n"
        proj_md_path.write_text(content)
    except Exception:
        pass


async def _synthesize_with_llm(
    project_name: str,
    history: list[dict],
    state_data: dict,
    project_md: str,
    entity_text: str = "",
    prior_synthesis: dict | None = None,
) -> dict | None:
    """Use Claude Haiku to intelligently synthesize project history into structured memory.

    Accepts prior_synthesis (cached from last run) to support incremental mode:
    when only a few new entries exist, Haiku merges them into the prior synthesis
    instead of re-processing the full history — reducing token cost ~8× on repeat runs.

    Returns a dict with: key_decisions, in_progress, tech_stack, memory_digest, project_summary.
    Returns None silently if the API key is missing or any error occurs.
    """
    try:
        import anthropic
        from data.dl_api_keys import get_key

        key = get_key("claude")
        if not key:
            return None

        # Build history text (oldest first, entries passed in by caller — already filtered)
        history_lines: list[str] = []
        for e in history:
            ts = (e.get("ts") or "")[:16].replace("T", " ")
            src = e.get("source", "?")
            q = (e.get("user_input") or "").strip()[:300].replace("\n", " ")
            a = (e.get("output") or "").strip()[:400].replace("\n", " ")
            history_lines.append(f"[{ts} | {src}]")
            history_lines.append(f"Q: {q}")
            if a:
                history_lines.append(f"A: {a}")
            history_lines.append("")
        history_text = "\n".join(history_lines)

        current_state = json.dumps({
            "tech_stack": state_data.get("tech_stack", {}),
            "key_decisions": state_data.get("key_decisions", []),
            "in_progress": state_data.get("in_progress", []),
        }, indent=2)
        proj_intro = (project_md.split("\n## ")[0].strip()[:600] if project_md else "")

        entity_block = f"Active project entities (features/bugs/tasks):\n{entity_text}\n\n" if entity_text else ""

        # Include prior synthesis so Haiku merges rather than discards stable context
        prior_block = ""
        if prior_synthesis:
            prior_json = json.dumps({
                k: prior_synthesis.get(k)
                for k in ("key_decisions", "in_progress", "tech_stack", "project_summary")
                if prior_synthesis.get(k)
            }, indent=2)[:800]
            prior_block = f"Prior synthesis (merge, do not discard stable decisions):\n{prior_json}\n\n"

        prompt = (
            f'You are analyzing development history for project "{project_name}".\n\n'
            f"Current structured state:\n{current_state}\n\n"
            f"{prior_block}"
            f"Project intro (from PROJECT.md):\n{proj_intro}\n\n"
            f"{entity_block}"
            f"Development history ({len(history)} entries, oldest→newest):\n{history_text}\n\n"
            "Return ONLY valid JSON (no markdown fences) with exactly these fields:\n"
            "{\n"
            '  "key_decisions": ["up to 15 stable architectural/technical decisions any LLM must know"],\n'
            '  "in_progress": ["up to 6 items most recently worked on, based on last 5 sessions"],\n'
            '  "tech_stack": {"component": "technology or version"},\n'
            '  "memory_digest": "Markdown: synthesize the 10 most important recent work items. '
            'Format each as: **[date]** `source` — description of what was done/decided.",\n'
            '  "project_summary": "2-3 sentence description of what this project is and its current state."\n'
            "}\n\n"
            "Rules:\n"
            "- key_decisions: permanent facts (tech choices, auth approach, architecture patterns)\n"
            "- in_progress: what was MOST RECENTLY worked on (infer from last 5 sessions)\n"
            "- tech_stack: merge existing + any new tech mentioned in history\n"
            "- memory_digest: synthesize meaningfully, don't just copy. Focus on decisions + features.\n"
            "- Return ONLY valid JSON, no explanation outside the JSON."
        )

        client = anthropic.AsyncAnthropic(api_key=key)
        response = await client.messages.create(
            model=settings.haiku_model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        content = (response.content[0].text if response.content else "").strip()
        # Strip markdown code fences if the model wrapped its output
        if "```" in content:
            for part in content.split("```"):
                stripped = part.strip()
                if stripped.startswith("json"):
                    stripped = stripped[4:].strip()
                if stripped.startswith("{"):
                    content = stripped
                    break

        parsed: dict = json.loads(content)
        required = {"key_decisions", "in_progress", "tech_stack", "memory_digest", "project_summary"}
        if not required.issubset(parsed.keys()):
            return None
        return parsed

    except Exception:
        return None  # Caller falls back to mechanical approach


async def _suggest_tags(
    project: str, entries: list[dict], existing_values: list[dict]
) -> list[dict]:
    """Ask Haiku to suggest 2-3 relevant entity tags for recent prompts.

    Returns a list of dicts: [{name, category, is_new}].
    Silent on error — returns [] when API key missing or call fails.
    """
    _log = logging.getLogger(__name__)
    try:
        from data.dl_api_keys import get_key
        import anthropic

        key = get_key("claude") or get_key("anthropic")
        if not key:
            _log.warning("[suggest_tags] No Anthropic API key found under 'claude' or 'anthropic'")
            return []

        recent_text = "\n".join(
            (e.get("user_input") or "")[:200].replace("\n", " ")
            for e in entries[-10:]
            if e.get("user_input")
        )
        if not recent_text.strip():
            _log.info("[suggest_tags] No user_input entries in recent history — skipping")
            return []

        existing_names = [v["name"] for v in existing_values[:30] if v.get("name")]
        prompt = (
            f"Recent developer prompts:\n{recent_text}\n\n"
            f"Existing tags: {', '.join(existing_names) if existing_names else '(none yet)'}\n\n"
            "Suggest 2-3 relevant tags for these prompts. Prefer existing tags where applicable; "
            "propose new ones only if clearly needed.\n"
            'Respond ONLY as valid JSON array: [{"name":"tag","category":"feature|bug|task","is_new":true}]'
        )
        _log.info("[suggest_tags] Calling Haiku for project=%s, entries=%d", project, len(entries))
        client = anthropic.AsyncAnthropic(api_key=key)
        response = await client.messages.create(
            model=settings.haiku_model,
            max_tokens=150,
            system="You are a JSON API. Respond with a valid JSON array only. No explanation, no preamble, no markdown.",
            messages=[{"role": "user", "content": prompt}],
        )
        text = (response.content[0].text if response.content else "").strip()
        _log.info("[suggest_tags] Haiku raw response: %s", text)
        # Extract JSON array from response — greedy match to capture full array with multiple objects
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            suggestions = json.loads(match.group())
            result = [s for s in suggestions if isinstance(s, dict) and s.get("name")][:3]
            _log.info("[suggest_tags] Parsed %d suggestions: %s", len(result), result)
            return result
        _log.warning("[suggest_tags] No JSON array found in response: %s", text)
        return []
    except Exception as e:
        _log.error("[suggest_tags] Failed: %s: %s", type(e).__name__, e)
        return []




async def _sync_workspace_projects() -> list[str]:
    """Upsert mng_projects rows from all workspace project.yaml files."""
    from pathlib import Path as _Path
    synced = []
    workspace = _Path(settings.workspace_dir)
    if not workspace.exists():
        return synced
    for proj_dir in workspace.iterdir():
        if not proj_dir.is_dir() or proj_dir.name.startswith('_'):
            continue
        yaml_path = proj_dir / "project.yaml"
        cfg: dict = {}
        if yaml_path.exists():
            try:
                import yaml as _yaml
                cfg = _yaml.safe_load(yaml_path.read_text()) or {}
            except Exception:
                pass
        cfg['workspace_path'] = str(proj_dir)
        db.get_or_create_project_id(proj_dir.name, config=cfg)
        synced.append(proj_dir.name)
    return synced


@router.post("/sync")
async def sync_workspace_projects():
    """Sync all workspace projects to mng_projects table."""
    synced = await _sync_workspace_projects()
    return {"synced": synced, "count": len(synced)}

@router.post("/{project_name}/memory")
async def generate_memory(project_name: str):
    """Generate per-LLM memory files and copy to code_dir.

    Generates files for every AI tool in use:
      _system/claude/MEMORY.md         — distilled Q&A history + decisions (Claude CLI reads at session start)
      _system/claude/CLAUDE.md         — refreshed project context + MEMORY.md reference
      _system/cursor/rules.md          — Cursor AI rules file
      _system/aicli/context.md         — compact block injected by aicli CLI into ALL providers
      _system/aicli/copilot.md         — GitHub Copilot instructions

    Copies to <code_dir>:
      <code_dir>/CLAUDE.md             → Claude CLI auto-loads
      <code_dir>/MEMORY.md             → referenced in CLAUDE.md so Claude reads it
      <code_dir>/.cursor/rules/aicli.mdrules  → Cursor AI
      <code_dir>/.github/copilot-instructions.md → GitHub Copilot
    """
    proj_dir = _workspace() / project_name
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    sys_dir = proj_dir / "_system"
    _ensure_per_llm_dirs(sys_dir)

    # Load config
    cfg: dict = {}
    proj_yaml_path = proj_dir / "project.yaml"
    if proj_yaml_path.exists():
        try:
            cfg = yaml.safe_load(proj_yaml_path.read_text()) or {}
        except Exception:
            pass

    # Rotate history.jsonl if it exceeds the configured limit
    history_max_rows: int = int(cfg.get("history_max_rows", 500))
    rotation = _rotate_history(sys_dir, max_rows=history_max_rows)

    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Load recent history from mem_mrr_prompts (DB-primary; JSONL no longer used)
    recent: list[dict] = []
    if db.is_available():
        try:
            _proj_id_mem = db.get_or_create_project_id(project_name)
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT source_id, session_id, tags->>'source' AS source,
                                  prompt, response, created_at
                           FROM mem_mrr_prompts
                           WHERE project_id=%s
                             AND prompt IS NOT NULL AND prompt != ''
                           ORDER BY created_at DESC LIMIT 120""",
                        (_proj_id_mem,),
                    )
                    rows = cur.fetchall()
            for source_id, session_id, source, prompt, response, created_at in reversed(rows):
                if prompt.strip().startswith(("<task-notification>", "<tool-use-id>", "<task-id>", "<parameter>")):
                    continue
                recent.append({
                    "ts":         source_id or (created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if created_at else ""),
                    "source":     source or "ui",
                    "session_id": session_id,
                    "user_input": prompt,
                    "output":     response or "",
                })
        except Exception as e:
            log.warning("generate_memory: DB history read failed: %s", e)
    recent = recent[-40:]

    # Load project_state.json (also reads last_memory_run for incremental processing)
    state_data: dict = {}
    state_path: Path | None = None
    for p in [sys_dir / "project_state.json", proj_dir / "project_state.json"]:
        if p.exists():
            try:
                state_data = json.loads(p.read_text())
                state_path = p
                break
            except Exception:
                pass
    if state_path is None:
        state_path = sys_dir / "project_state.json"

    # last_memory_run: ISO ts of the previous /memory call — used for incremental ingest
    last_memory_run: str | None = state_data.get("last_memory_run")

    # Load PROJECT.md
    project_md = ""
    if (proj_dir / "PROJECT.md").exists():
        project_md = (proj_dir / "PROJECT.md").read_text()

    generated: list[str] = []

    # ── Load entity summary (features/bugs/tasks) for synthesis + MEMORY.md ──
    entity_groups: list[dict] = []
    entity_text_for_llm = ""
    if db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_ENTITY_SUMMARY, (_proj_id_mem,))
                    entity_rows = cur.fetchall()
            # Build per-category groups
            _cats: dict[str, list] = {}
            for (cat, icon, vid, vname, vdesc, vstatus, vdue, vparent, ec, cc) in entity_rows:
                _cats.setdefault(cat, []).append((icon, vname, vdesc, vstatus, vdue, vparent, ec, cc))
            entity_groups = [{"category": k, "values": v} for k, v in _cats.items()]
            # Compact text for LLM prompt
            lines_for_llm: list[str] = []
            for g in entity_groups:
                for (icon, vname, vdesc, vstatus, vdue, vparent, ec, cc) in g["values"]:
                    due = f" due:{vdue.isoformat() if vdue else ''}" if vdue else ""
                    desc = f" — {vdesc[:80]}" if vdesc else ""
                    lines_for_llm.append(
                        f"[{g['category']}] {vname} ({vstatus}){due}{desc} | {ec} events, {cc} commits"
                    )
            entity_text_for_llm = "\n".join(lines_for_llm[:40])
        except Exception as _e:
            log.warning("entity summary for /memory failed: %s", _e)

    # ── LLM synthesis (optional — degrades to mechanical approach if API unavailable) ──
    # Incremental: only send new entries to Haiku when ≥3 exist since last run.
    combined_entity_text = entity_text_for_llm
    prior_synthesis: dict = state_data.get("_synthesis_cache", {})
    new_entries = [e for e in recent if (e.get("ts") or "") > (last_memory_run or "")]
    if len(new_entries) >= 3:
        entries_for_llm = new_entries
    else:
        entries_for_llm = recent  # fallback

    synthesis = await _synthesize_with_llm(
        project_name, entries_for_llm, state_data, project_md, combined_entity_text,
        prior_synthesis=prior_synthesis if new_entries else None,
    )
    if synthesis:
        # Merge LLM-extracted structured data into state_data (LLM wins on new fields)
        if synthesis.get("tech_stack"):
            state_data.setdefault("tech_stack", {}).update(synthesis["tech_stack"])
        if synthesis.get("key_decisions"):
            # Deduplicate: LLM wins on new entries; preserve prior unique decisions
            existing = set(state_data.get("key_decisions", []))
            new_kd = synthesis["key_decisions"]
            state_data["key_decisions"] = new_kd + [d for d in existing if d not in set(new_kd)]
            state_data["key_decisions"] = state_data["key_decisions"][:15]
        if synthesis.get("in_progress"):
            state_data["in_progress"] = synthesis["in_progress"][:6]
        # Save synthesis as cache for next incremental run
        state_data["_synthesis_cache"] = {
            k: synthesis.get(k)
            for k in ("key_decisions", "in_progress", "tech_stack", "project_summary", "memory_digest")
        }
        # Persist updated project_state.json so get_project_context() reads fresh data below
        _save_project_state(sys_dir, state_data)
        # Refresh PROJECT.md "Recent Work" section with LLM-extracted items
        if synthesis.get("in_progress"):
            recent_body = "\n".join(f"- {item}" for item in synthesis["in_progress"]) + "\n"
            _update_project_md_section(proj_dir, "Recent Work", recent_body)

    # ── 1. MEMORY.md — distilled history for Claude CLI ───────────────────────
    # Claude CLI reads CLAUDE.md at startup; CLAUDE.md references MEMORY.md.
    memory_lines = [
        f"# Project Memory — {project_name}",
        f"_Generated: {ts} by aicli /memory_\n",
        "> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.\n",
    ]

    if synthesis and synthesis.get("project_summary"):
        memory_lines.append("## Project Summary\n")
        memory_lines.append(synthesis["project_summary"])
        memory_lines.append("")

    if state_data.get("tech_stack"):
        memory_lines.append("## Tech Stack\n")
        for k, v in state_data["tech_stack"].items():
            memory_lines.append(f"- **{k}**: {v}")
        memory_lines.append("")

    if state_data.get("key_decisions"):
        memory_lines.append("## Key Decisions\n")
        for d in state_data["key_decisions"]:
            memory_lines.append(f"- {d}")
        memory_lines.append("")

    if state_data.get("in_progress"):
        memory_lines.append("## In Progress\n")
        for item in state_data["in_progress"]:
            memory_lines.append(f"- {item}")
        memory_lines.append("")

    # ── Active Features from entity layer (uses pre-loaded entity_groups) ──────
    if entity_groups:
        memory_lines.append("## Active Features / Bugs / Tasks\n")
        for g in entity_groups:
            cat = g["category"]
            vals = g["values"]
            if not vals:
                continue
            memory_lines.append(f"### {cat.capitalize()}\n")
            for (icon, vname, vdesc, vstatus, vdue, vparent, ec, cc) in vals:
                label = f"- **{vname}**"
                if vstatus != "active":
                    label += f" `[{vstatus}]`"
                if vdue:
                    label += f" | due: {vdue.isoformat() if hasattr(vdue, 'isoformat') else vdue}"
                if vdesc:
                    label += f" — {vdesc[:100]}"
                meta = []
                if ec:
                    meta.append(f"{ec} events")
                if cc:
                    meta.append(f"{cc} commits")
                if meta:
                    label += f" `({', '.join(meta)})`"
                memory_lines.append(label)
            memory_lines.append("")

    if synthesis and synthesis.get("memory_digest"):
        # LLM synthesis across all context (supplements memory_items or standalone)
        memory_lines.append("## AI Synthesis\n")
        memory_lines.append(synthesis["memory_digest"])
    else:
        # Fallback: mechanical Q&A truncation (no API key or synthesis failed)
        memory_lines.append("## Recent Work (last 10 exchanges)\n")
        shown = 0
        for e in reversed(recent):
            if shown >= 10:
                break
            date = (e.get("ts") or "")[:16].replace("T", " ")
            src = e.get("source", "")
            prov = e.get("provider", "")
            q = (e.get("user_input") or "").strip()[:200].replace("\n", " ")
            a = (e.get("output") or "").strip()[:300].replace("\n", " ")
            memory_lines.append(f"**[{date}]** `{src}/{prov}`")
            memory_lines.append(f"Q: {q}")
            if a:
                memory_lines.append(f"A: {a}")
            memory_lines.append("")
            shown += 1

    memory_md = "\n".join(memory_lines)
    (sys_dir / "claude" / "MEMORY.md").write_text(memory_md)
    generated.append("_system/claude/MEMORY.md")

    # ── 2. CLAUDE.md — refreshed context with MEMORY.md reference ─────────────
    try:
        ctx_result = await get_project_context(project_name, save=True)
        claude_md_content = ctx_result.get("claude_md", "")
        # Append MEMORY.md reference so Claude CLI reads it
        if claude_md_content and "MEMORY.md" not in claude_md_content:
            digest_note = (
                "LLM-synthesized project digest" if synthesis
                else "last 10 development exchanges"
            )
            claude_md_content += (
                "\n\n---\n\n## Session Memory\n\n"
                f"Read `MEMORY.md` in this directory for recent work history, "
                f"key decisions, and in-progress items. It was generated by aicli `/memory` "
                f"({digest_note}).\n"
            )
            # Re-write with the reference included
            (sys_dir / "claude" / "CLAUDE.md").write_text(claude_md_content)
            (sys_dir / "CLAUDE.md").write_text(claude_md_content)
        generated.append("_system/claude/CLAUDE.md")
    except Exception:
        claude_md_content = ""

    # ── 3. cursor/rules.md — Cursor AI coding rules ───────────────────────────
    # Cursor reads .cursor/rules/*.mdrules — keep focused on coding conventions.
    cursor_lines = [
        f"# {project_name} — AI Coding Rules",
        f"> Managed by aicli. Run `/memory` to refresh. Generated: {ts}\n",
    ]
    # Project description (first paragraph of PROJECT.md)
    if project_md:
        first_section = project_md.split("\n## ")[0].strip()
        cursor_lines.append(first_section[:500])
        cursor_lines.append("")

    if state_data.get("tech_stack"):
        cursor_lines.append("## Tech Stack\n")
        for k, v in state_data["tech_stack"].items():
            cursor_lines.append(f"- **{k}**: {v}")
        cursor_lines.append("")

    if state_data.get("key_decisions"):
        cursor_lines.append("## Key Decisions\n")
        for d in state_data["key_decisions"]:
            cursor_lines.append(f"- {d}")
        cursor_lines.append("")

    # Recent context for Cursor
    if recent:
        cursor_lines.append("## Recent Context (last 5 changes)\n")
        for e in recent[-5:]:
            date = (e.get("ts") or "")[:10]
            q = (e.get("user_input") or "").strip()[:120].replace("\n", " ")
            cursor_lines.append(f"- [{date}] {q}")

    cursor_md = "\n".join(cursor_lines)
    (sys_dir / "cursor" / "rules.md").write_text(cursor_md)
    generated.append("_system/cursor/rules.md")

    # .ai/rules.md — Windsurf / Cursor AI rules (newer .ai/ directory format)
    # Stored under _system/aicli/ai_rules.md; copied to code_dir/.ai/rules.md below
    ai_rules_md = cursor_md  # same content as cursor rules

    # ── 4. aicli/context.md — injected into ALL providers by aicli CLI ────────
    # This is what OpenAI, DeepSeek, Grok, Gemini, etc. receive before every prompt.
    # Keep it under ~600 chars — compact but informative.
    aicli_lines = [
        f"[PROJECT CONTEXT: {project_name}]",
    ]
    if synthesis and synthesis.get("project_summary"):
        aicli_lines.append(synthesis["project_summary"])
    elif cfg.get("description"):
        aicli_lines.append(cfg["description"])

    if state_data.get("tech_stack"):
        stack_str = ", ".join(f"{k}={v}" for k, v in list(state_data["tech_stack"].items())[:5])
        aicli_lines.append(f"Stack: {stack_str}")

    if state_data.get("in_progress"):
        aicli_lines.append(f"In progress: {', '.join(state_data['in_progress'][:3])}")

    if state_data.get("key_decisions"):
        aicli_lines.append("Decisions: " + "; ".join(state_data["key_decisions"][:3]))

    if entity_groups:
        # Compact entity summary — top active items per category
        entity_parts: list[str] = []
        for g in entity_groups:
            top = [(vname, ec) for (_, vname, _, vstatus, _, _, ec, _) in g["values"]
                   if vstatus == "active"][:3]
            if top:
                items = ", ".join(f"{n} ({e}ev)" for n, e in top)
                entity_parts.append(f"[{g['category']}] {items}")
        if entity_parts:
            aicli_lines.append("Entities: " + " | ".join(entity_parts))

    if recent:
        last = recent[-1]
        aicli_lines.append(
            f"Last work ({(last.get('ts') or '')[:10]}): "
            f"{(last.get('user_input') or '').strip()[:150].replace(chr(10), ' ')}"
        )
    aicli_context = "\n".join(aicli_lines)
    (sys_dir / "aicli" / "context.md").write_text(aicli_context)
    generated.append("_system/aicli/context.md")

    # ── 5. GitHub Copilot instructions ────────────────────────────────────────
    copilot_lines = [
        f"# {project_name} — GitHub Copilot Instructions",
        f"> Generated by aicli {ts}\n",
    ]
    if project_md:
        copilot_lines.append(project_md.split("\n## ")[0].strip()[:400])
        copilot_lines.append("")
    if state_data.get("tech_stack"):
        copilot_lines.append("## Tech Stack\n")
        for k, v in state_data["tech_stack"].items():
            copilot_lines.append(f"- {k}: {v}")
        copilot_lines.append("")
    if state_data.get("key_decisions"):
        copilot_lines.append("## Architectural Decisions\n")
        for d in state_data["key_decisions"]:
            copilot_lines.append(f"- {d}")
    copilot_md = "\n".join(copilot_lines)
    (sys_dir / "aicli" / "copilot.md").write_text(copilot_md)
    generated.append("_system/aicli/copilot.md")

    # ── 6. Copy to code_dir ───────────────────────────────────────────────────
    copied_to: list[str] = []
    skipped_copy = True
    code_dir_str = cfg.get("code_dir", "")
    if code_dir_str:
        code_path = Path(code_dir_str)
        if not code_path.is_absolute():
            code_path = proj_dir / code_path
        code_path = code_path.resolve()
        if code_path.exists() and code_path.is_dir():
            skipped_copy = False
            for src_content, dest_rel, make_parents in [
                (claude_md_content, "CLAUDE.md", False),
                (memory_md, "MEMORY.md", False),
                (cursor_md, ".cursor/rules/aicli.mdrules", True),
                (copilot_md, ".github/copilot-instructions.md", True),
                (ai_rules_md, ".ai/rules.md", True),
            ]:
                if not src_content:
                    continue
                dest = code_path / dest_rel
                try:
                    if make_parents:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(src_content)
                    copied_to.append(dest_rel)
                except Exception:
                    pass

    # ── Update last_memory_run BEFORE background tasks start ─────────────────
    run_ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    state_data["last_memory_run"] = run_ts
    try:
        state_path.write_text(json.dumps(state_data, indent=2))
    except Exception:
        pass
    # Bust memory-status cache so next load reflects the fresh run
    _MEMORY_STATUS_CACHE.pop(project_name, None)

    # ── Tag suggestions — ask Haiku based on recent history ──────────────────
    # Works with or without PostgreSQL: existing_values is best-effort from DB,
    # falls back to [] so Haiku still suggests tags even when DB is unavailable.
    suggested_tags: list[dict] = []
    suggestions_note = ""
    if not recent:
        suggestions_note = "no recent history found in history.jsonl"
    else:
        try:
            existing_values: list[dict] = []
            if db.is_available():
                try:
                    with db.conn() as conn:
                        with conn.cursor() as cur:
                            _pid_ev = db.get_or_create_project_id(project_name)
                            cur.execute(_SQL_GET_EXISTING_ENTITY_VALUES, (_pid_ev,))
                            existing_values = [{"id": r[0], "name": r[1]} for r in cur.fetchall()]
                except Exception:
                    pass
            suggested_tags = await _suggest_tags(project_name, recent, existing_values)
            if not suggested_tags:
                suggestions_note = "Haiku returned no suggestions (check backend logs for detail)"
        except Exception as e:
            suggestions_note = f"error: {e}"

    return {
        "generated": generated,
        "copied_to": copied_to,
        "skipped_copy": skipped_copy,
        "synthesized": synthesis is not None,
        "incremental_since": last_memory_run,
        "suggestions_note": suggestions_note,
        "run_ts": run_ts,
        "suggested_tags": suggested_tags,
        "history_rotation": rotation,
    }


@router.get("/{project_name}/memory-status")
async def memory_status(project_name: str, bust: bool = False):
    """Return memory health: how many new prompts since last /memory run.

    Reads project_state.json for last_memory_run, counts new history.jsonl entries,
    compares against configurable threshold (project.yaml memory_threshold, default 20).
    Used by the UI amber banner and summary Memory Health card.
    Result is cached for 60 s per project to avoid rescanning on every page load.
    Pass ?bust=true to force a fresh scan (e.g. after running /memory).
    """
    # Serve from cache if fresh enough
    cached = _MEMORY_STATUS_CACHE.get(project_name)
    if cached and not bust:
        ts, result = cached
        if time.monotonic() - ts < _MEMORY_STATUS_TTL:
            return result

    proj_dir = _workspace() / project_name
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    sys_dir = proj_dir / "_system"

    # Load project_state.json for last_memory_run
    state_data: dict = {}
    for sp in [sys_dir / "project_state.json", proj_dir / "project_state.json"]:
        if sp.exists():
            try:
                state_data = json.loads(sp.read_text())
                break
            except Exception:
                pass
    last_memory_run: str | None = state_data.get("last_memory_run")

    # Load threshold from project.yaml
    threshold = 20
    proj_yaml = proj_dir / "project.yaml"
    if proj_yaml.exists():
        try:
            cfg = yaml.safe_load(proj_yaml.read_text()) or {}
            threshold = int(cfg.get("memory_threshold", 20))
        except Exception:
            pass

    # Count prompts in history.jsonl since last_memory_run
    total_prompts = 0
    prompts_since = 0
    hist_file = sys_dir / "history.jsonl"
    if hist_file.exists():
        for line in hist_file.read_text().splitlines():
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            if not e.get("user_input"):
                continue
            total_prompts += 1
            ts = e.get("ts") or ""
            if last_memory_run is None or ts > last_memory_run:
                prompts_since += 1

    # Days since last run
    days_since: int | None = None
    if last_memory_run:
        try:
            last_dt = datetime.fromisoformat(last_memory_run.replace("Z", "+00:00"))
            days_since = (datetime.utcnow().replace(tzinfo=last_dt.tzinfo) - last_dt).days
        except Exception:
            pass

    # Also count from mem_mrr_prompts table (new storage)
    interactions_total = 0
    interactions_since = 0
    if db.is_available():
        try:
            _pid_ms = db.get_or_create_project_id(project_name)
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_COUNT_INTERACTIONS_TOTAL, (_pid_ms,))
                    interactions_total = (cur.fetchone() or (0,))[0]
                    if last_memory_run:
                        cur.execute(_SQL_COUNT_INTERACTIONS_SINCE, (_pid_ms, last_memory_run))
                        interactions_since = (cur.fetchone() or (0,))[0]
                    else:
                        interactions_since = interactions_total
        except Exception:
            pass

    # Use whichever count is higher (both sources may have data)
    total_prompts  = max(total_prompts, interactions_total)
    prompts_since  = max(prompts_since, interactions_since)

    result = {
        "last_memory_run": last_memory_run,
        "prompts_since_last_memory": prompts_since,
        "total_prompts": total_prompts,
        "needs_memory": prompts_since >= threshold,
        "threshold": threshold,
        "days_since_last_memory": days_since,
        "project": project_name,
    }
    _MEMORY_STATUS_CACHE[project_name] = (time.monotonic(), result)
    return result


@router.get("/{project_name}")
async def get_project(project_name: str):
    """Get project details."""
    proj_dir = _workspace() / project_name
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")

    proj_yaml = proj_dir / "project.yaml"
    data: dict = {"name": project_name}
    if proj_yaml.exists():
        try:
            data.update(yaml.safe_load(proj_yaml.read_text()) or {})
        except Exception:
            pass

    proj_md = proj_dir / "PROJECT.md"
    if proj_md.exists():
        data["project_md"] = proj_md.read_text()

    # Check per-LLM location first, then legacy flat location
    sys_dir = proj_dir / "_system"
    claude_md_path = _find_claude_md(sys_dir)
    if claude_md_path.exists():
        data["claude_md"] = claude_md_path.read_text()
    elif (proj_dir / "CLAUDE.md").exists():
        data["claude_md"] = (proj_dir / "CLAUDE.md").read_text()

    context_md = sys_dir / "CONTEXT.md"
    if context_md.exists():
        data["context_md"] = context_md.read_text()
    elif (proj_dir / "CONTEXT.md").exists():
        data["context_md"] = (proj_dir / "CONTEXT.md").read_text()

    # Include state snapshot files if present
    for state_file in ("project_state.json", "dev_runtime_state.json"):
        for base in [sys_dir, proj_dir]:
            path = base / state_file
            if path.exists():
                try:
                    data[state_file.replace(".json", "").replace("-", "_")] = json.loads(path.read_text())
                    break
                except Exception:
                    pass

    return data

class ProjectMemberAdd(BaseModel):
    user_id: str
    role: str = "member"  # 'owner'|'editor'|'viewer'


@router.get("/{project}/members")
def list_project_members(project: str):
    if not db.is_available():
        return {"members": []}
    project_id = db.get_project_id(project)
    if project_id is None:
        raise HTTPException(404, f"Project '{project}' not found")
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT u.id, u.email, up.role, up.joined_at
                   FROM mng_user_projects up
                   JOIN mng_users u ON u.id = up.user_id
                   WHERE up.project_id=%s ORDER BY up.joined_at""",
                (project_id,)
            )
            rows = cur.fetchall()
    return {"members": [{"user_id": r[0], "email": r[1], "role": r[2], "joined_at": str(r[3])} for r in rows]}


@router.post("/{project}/members")
def add_project_member(project: str, body: ProjectMemberAdd):
    if not db.is_available():
        raise HTTPException(503, "Database unavailable")
    project_id = db.get_project_id(project)
    if project_id is None:
        raise HTTPException(404, f"Project '{project}' not found")
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO mng_user_projects (user_id, project_id, role)
                   VALUES (%s, %s, %s) ON CONFLICT (user_id, project_id) DO UPDATE SET role=EXCLUDED.role""",
                (body.user_id, project_id, body.role)
            )
    return {"ok": True}


@router.put("/{project}/members/{user_id}")
def update_project_member(project: str, user_id: str, body: ProjectMemberAdd):
    if not db.is_available():
        raise HTTPException(503, "Database unavailable")
    project_id = db.get_project_id(project)
    if project_id is None:
        raise HTTPException(404, f"Project '{project}' not found")
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE mng_user_projects SET role=%s WHERE user_id=%s AND project_id=%s",
                (body.role, user_id, project_id)
            )
    return {"ok": True}


@router.delete("/{project}/members/{user_id}")
def remove_project_member(project: str, user_id: str):
    if not db.is_available():
        raise HTTPException(503, "Database unavailable")
    project_id = db.get_project_id(project)
    if project_id is None:
        raise HTTPException(404, f"Project '{project}' not found")
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM mng_user_projects WHERE user_id=%s AND project_id=%s",
                (user_id, project_id)
            )
    return {"ok": True}
