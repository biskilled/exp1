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
from data.database import db

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
    """List all project workspaces."""
    ws = _workspace()
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
    """List available project templates."""
    templates_dir = _workspace() / "_templates"
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
    template: str = "blank"
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
    template_dir = ws / "_templates" / body.template
    dest_dir = ws / body.name

    if not template_dir.exists():
        raise HTTPException(status_code=404, detail=f"Template not found: {body.template}")
    if dest_dir.exists():
        raise HTTPException(status_code=409, detail=f"Project already exists: {body.name}")

    # Copy only the template content (not hooks/)
    def _ignore_hooks(src, names):
        return ["hooks"] if Path(src).name == "_templates" else []

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
        hooks_src = ws / "_templates" / "hooks"

        def _render_tpl(tpl_file: Path) -> str:
            return (tpl_file.read_text()
                    .replace("{{WORKSPACE_DIR}}", str(ws))
                    .replace("{{PROJECT_NAME}}", body.name)
                    .replace("{{AICLI_DIR}}", str(_AICLI_DIR)))

        if body.claude_cli_support and hooks_src.exists():
            # Install hooks into _system/hooks/
            hooks_dest = sys_dir / "hooks"
            hooks_dest.mkdir(parents=True, exist_ok=True)
            for sh in hooks_src.glob("*.sh"):
                shutil.copy2(str(sh), str(hooks_dest / sh.name))
            # Render settings.template.json → {code_dir}/.claude/settings.local.json
            tpl_file = hooks_src / "settings.template.json"
            if tpl_file.exists():
                settings_dir = code_path / ".claude"
                settings_dir.mkdir(parents=True, exist_ok=True)
                (settings_dir / "settings.local.json").write_text(_render_tpl(tpl_file))
            # Render mcp.template.json → {code_dir}/.mcp.json  (Claude Code + Claude CLI)
            mcp_tpl = hooks_src / "mcp.template.json"
            if mcp_tpl.exists():
                (code_path / ".mcp.json").write_text(_render_tpl(mcp_tpl))
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
            # Render mcp.template.json → {code_dir}/.cursor/mcp.json  (Cursor MCP)
            mcp_tpl = hooks_src / "mcp.template.json"
            if mcp_tpl.exists():
                cursor_mcp_dir = code_path / ".cursor"
                cursor_mcp_dir.mkdir(parents=True, exist_ok=True)
                (cursor_mcp_dir / "mcp.json").write_text(_render_tpl(mcp_tpl))
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
    # Embed updated PROJECT.md for semantic search (fire-and-forget)
    try:
        from memory.mem_embeddings import embed_and_store as _embed
        asyncio.create_task(_embed(project_name, "project_md", "PROJECT.md", content))
    except Exception:
        pass
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
        from core.api_keys import get_key

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
        from core.api_keys import get_key
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


# ── Memory distillation pipeline ─────────────────────────────────────────────

async def _summarize_session_memory(project: str) -> int:
    """Layer 1: Summarize unsummarized sessions into pr_memory_items (Trycycle pattern).

    Queries interactions for sessions with >= 3 prompts not yet summarized.
    Each session gets two Haiku calls: summarize + rate/improve. Result stored
    in memory_items(scope='session').
    Returns count of new memory_items created.
    """
    if not db.is_available():
        return 0
    try:
        from core.api_keys import get_key
        import anthropic

        key = get_key("claude") or get_key("anthropic")
        if not key:
            return 0

        # Find sessions with >= 3 interactions not yet in memory_items
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT i.session_id, COUNT(*) AS cnt,
                              ARRAY_AGG(i.id ORDER BY i.created_at) AS ids,
                              STRING_AGG(
                                  '[' || LEFT(i.created_at::text, 16) || '] Q: '
                                  || LEFT(COALESCE(i.prompt,''),300)
                                  || CASE WHEN i.response != '' THEN E'\n A: ' || LEFT(i.response,200) ELSE '' END,
                                  E'\n\n' ORDER BY i.created_at
                              ) AS history_text
                       FROM pr_interactions i
                       WHERE i.client_id=1 AND i.project=%s
                         AND i.event_type='prompt'
                         AND i.session_id IS NOT NULL
                         AND NOT EXISTS (
                             SELECT 1 FROM pr_memory_items m
                             WHERE m.client_id=1 AND m.project=i.project
                               AND m.scope='session'
                               AND m.scope_ref=i.session_id
                         )
                       GROUP BY i.session_id
                       HAVING COUNT(*) >= 3
                       LIMIT 10""",
                    (project,),
                )
                sessions = cur.fetchall()

        if not sessions:
            return 0

        client = anthropic.AsyncAnthropic(api_key=key)
        created = 0

        for (session_id, cnt, interaction_ids, history_text) in sessions:
            try:
                # Haiku call 1: summarize
                r1 = await client.messages.create(
                    model=settings.haiku_model,
                    max_tokens=800,
                    messages=[{"role": "user", "content":
                        f"Summarize this development session — focus on decisions and code changes "
                        f"(3-8 bullet points max, be specific):\n\n{history_text[:3000]}"}],
                )
                summary1 = (r1.content[0].text if r1.content else "").strip()
                if not summary1:
                    continue

                # Haiku call 2: Trycycle review (fresh context)
                r2 = await client.messages.create(
                    model=settings.haiku_model,
                    max_tokens=600,
                    messages=[{"role": "user", "content":
                        f"Rate this session summary 1-10 for completeness and accuracy. "
                        f"Return ONLY valid JSON: {{\"score\": N, \"critique\": \"...\", \"improved_summary\": \"...\"}}.\n\n"
                        f"Original session:\n{history_text[:2000]}\n\nSummary to rate:\n{summary1}"}],
                )
                r2_text = (r2.content[0].text if r2.content else "").strip()
                score, critique, final_summary = 8, "", summary1
                try:
                    if "```" in r2_text:
                        for part in r2_text.split("```"):
                            s = part.strip().lstrip("json").strip()
                            if s.startswith("{"):
                                r2_text = s
                                break
                    parsed = json.loads(r2_text)
                    score    = int(parsed.get("score", 8))
                    critique = parsed.get("critique", "")
                    if score < 7 and parsed.get("improved_summary"):
                        final_summary = parsed["improved_summary"]
                except Exception:
                    pass

                # Store in memory_items
                # interaction_ids from ARRAY_AGG may come back as a PG array string
                # like '{uuid1,uuid2}' — normalise to a proper uuid[] literal
                if isinstance(interaction_ids, str):
                    _raw = interaction_ids.strip('{}')
                    _ids = [x.strip() for x in _raw.split(',') if x.strip()]
                else:
                    _ids = [str(i) for i in (interaction_ids or [])]
                source_ids_pg = '{' + ','.join(_ids) + '}'

                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """INSERT INTO pr_memory_items
                                   (client_id, project, scope, scope_ref, content, source_ids,
                                    reviewer_score, reviewer_critique)
                               VALUES (1, %s,'session',%s,%s,%s::uuid[],%s,%s)
                               ON CONFLICT DO NOTHING
                               RETURNING id""",
                            (project, session_id, final_summary,
                             source_ids_pg, score, critique or None),
                        )
                        row = cur.fetchone()
                        if row:
                            created += 1
                            # Embed into pgvector for semantic search
                            try:
                                from memory.mem_embeddings import embed_and_store
                                asyncio.create_task(embed_and_store(
                                    project, "memory_item", str(row[0]), final_summary,
                                    doc_type="session_summary",
                                ))
                            except Exception:
                                pass
            except Exception as e:
                log.debug(f"_summarize_session_memory: session {session_id} failed: {e}")

        return created
    except Exception as e:
        log.debug(f"_summarize_session_memory failed: {e}")
        return 0


async def _summarize_feature_memory(project: str, work_item_id: str) -> str | None:
    """Layer 2: Summarize a completed feature/bug/task into a memory_item.

    Called when a work_item lifecycle_status → 'done'.
    Collects session summaries whose source_ids overlap with this work_item's interactions,
    then uses Haiku + Trycycle to create a feature-level memory.
    Returns the new memory_item UUID or None.
    """
    if not db.is_available():
        return None
    try:
        from core.api_keys import get_key
        import anthropic

        key = get_key("claude") or get_key("anthropic")
        if not key:
            return None

        with db.conn() as conn:
            with conn.cursor() as cur:
                # Get work item details
                cur.execute(
                    "SELECT name, description FROM pr_work_items WHERE id=%s::uuid AND client_id=1 AND project=%s",
                    (work_item_id, project),
                )
                wi_row = cur.fetchone()
                if not wi_row:
                    return None
                wi_name, wi_desc = wi_row

                # Find memory_items whose source_ids overlap with this work_item's interactions
                cur.execute(
                    """SELECT m.content
                       FROM pr_memory_items m
                       WHERE m.client_id=1 AND m.project=%s AND m.scope='session'
                         AND EXISTS (
                             SELECT 1 FROM pr_interaction_tags it
                             WHERE it.work_item_id=%s::uuid
                               AND it.interaction_id = ANY(m.source_ids)
                         )
                       ORDER BY m.created_at
                       LIMIT 10""",
                    (project, work_item_id),
                )
                session_summaries = [r[0] for r in cur.fetchall()]

        if not session_summaries:
            return None

        context = "\n\n---\n\n".join(session_summaries)
        client = anthropic.AsyncAnthropic(api_key=key)

        # Haiku call 1: feature summary
        r1 = await client.messages.create(
            model=settings.haiku_model,
            max_tokens=600,
            messages=[{"role": "user", "content":
                f"Summarize the complete development history for feature '{wi_name}': {wi_desc}.\n\n"
                f"Session summaries:\n{context[:2500]}\n\n"
                f"Write a concise feature postmortem (decisions, implementation approach, outcome)."}],
        )
        summary1 = (r1.content[0].text if r1.content else "").strip()
        if not summary1:
            return None

        # Haiku call 2: Trycycle
        r2 = await client.messages.create(
            model=settings.haiku_model,
            max_tokens=500,
            messages=[{"role": "user", "content":
                f"Rate this feature summary 1-10. Return ONLY JSON: "
                f"{{\"score\": N, \"critique\": \"...\", \"improved_summary\": \"...\"}}.\n\nSummary:\n{summary1}"}],
        )
        r2_text = (r2.content[0].text if r2.content else "").strip()
        final_summary = summary1
        score, critique = 8, ""
        try:
            if "```" in r2_text:
                for part in r2_text.split("```"):
                    s = part.strip().lstrip("json").strip()
                    if s.startswith("{"):
                        r2_text = s
                        break
            parsed = json.loads(r2_text)
            score = int(parsed.get("score", 8))
            critique = parsed.get("critique", "")
            if score < 7 and parsed.get("improved_summary"):
                final_summary = parsed["improved_summary"]
        except Exception:
            pass

        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO pr_memory_items
                           (client_id, project, scope, scope_ref, content, reviewer_score, reviewer_critique)
                       VALUES (1, %s,'feature',%s,%s,%s,%s)
                       RETURNING id""",
                    (project, wi_name, final_summary, score, critique or None),
                )
                row = cur.fetchone()
                if not row:
                    return None
                memory_id = str(row[0])
                # Embed into pgvector for semantic search
                try:
                    from memory.mem_embeddings import embed_and_store
                    asyncio.create_task(embed_and_store(
                        project, "memory_item", memory_id, final_summary,
                        doc_type="feature_summary",
                    ))
                except Exception:
                    pass
                return memory_id
    except Exception as e:
        log.debug(f"_summarize_feature_memory failed: {e}")
        return None


async def _extract_project_facts(project: str, memory_item_id: str | None = None) -> int:
    """Layer 3: Extract durable architectural facts from recent memory_items.

    Uses the 'internal_project_fact' agent role from mng_agent_roles for the
    prompt text and model choice — the user can edit both in the Roles tab.

    Facts use temporal validity: valid_until=NULL means current.  Changing a
    fact invalidates the old row (sets valid_until=NOW()) and inserts the new
    value, preserving the full history.

    Returns count of new facts inserted.
    """
    if not db.is_available():
        return 0
    try:
        from core.api_keys import get_key
        import anthropic

        # ── Load the internal role (system_prompt + model + provider) ─────────
        role_system = ""
        role_model = settings.haiku_model
        role_provider = "claude"
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT system_prompt, model, provider FROM mng_agent_roles
                           WHERE client_id=1 AND project='_global'
                             AND name='internal_project_fact' AND is_active=TRUE
                           LIMIT 1""",
                    )
                    row = cur.fetchone()
                    if row and row[0]:
                        role_system   = row[0]
                        role_model    = row[1] or settings.haiku_model
                        role_provider = row[2] or "claude"
        except Exception as _re:
            log.debug(f"_extract_project_facts: could not load role: {_re}")

        key = get_key(role_provider) or get_key("claude") or get_key("anthropic")
        if not key:
            return 0

        # ── Load sources: recent memory_items + existing facts ────────────────
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id::text, content FROM pr_memory_items
                       WHERE client_id=1 AND project=%s
                       ORDER BY created_at DESC LIMIT 6""",
                    (project,),
                )
                mem_rows = cur.fetchall()
                cur.execute(
                    """SELECT fact_key, fact_value FROM pr_project_facts
                       WHERE client_id=1 AND project=%s AND valid_until IS NULL
                       ORDER BY fact_key""",
                    (project,),
                )
                existing_facts = {r[0]: r[1] for r in cur.fetchall()}

        if not mem_rows:
            return 0

        source_ids = [r[0] for r in mem_rows]
        combined   = "\n\n---\n\n".join(r[1] for r in mem_rows[:5])

        existing_block = ""
        if existing_facts:
            existing_block = (
                "Already-extracted facts (confirm if still true, update value if changed, "
                "skip entirely if unchanged):\n"
                + "\n".join(f"  {k}: {v}" for k, v in list(existing_facts.items())[:20])
                + "\n\n"
            )

        user_msg = (
            f"{existing_block}"
            f"Development notes to analyze:\n{combined[:3500]}"
        )

        # ── Call the LLM ──────────────────────────────────────────────────────
        client_a = anthropic.AsyncAnthropic(api_key=key)
        resp = await client_a.messages.create(
            model=role_model,
            max_tokens=600,
            system=role_system,
            messages=[{"role": "user", "content": user_msg}],
        )
        text = (resp.content[0].text if resp.content else "").strip()

        # Strip markdown fences if present
        if "```" in text:
            for part in text.split("```"):
                s = part.strip().lstrip("json").strip()
                if s.startswith("["):
                    text = s
                    break

        # ── Parse JSON array [{"key": ..., "value": ..., "confidence": ...}] ──
        raw_list = json.loads(text)
        if not isinstance(raw_list, list):
            return 0

        # Filter: valid structure + confidence >= 0.7
        CONFIDENCE_THRESHOLD = 0.70
        facts: list[tuple[str, str]] = []
        for item in raw_list:
            if not isinstance(item, dict):
                continue
            k = str(item.get("key", "")).strip()
            v = str(item.get("value", "")).strip()
            conf = float(item.get("confidence", 1.0))
            if k and v and conf >= CONFIDENCE_THRESHOLD:
                facts.append((k, v))

        if not facts:
            return 0

        # ── Upsert with temporal validity ─────────────────────────────────────
        # source_memory_id: use the most recent memory_item for traceability
        src_id = source_ids[0] if source_ids else None
        inserted = 0
        with db.conn() as conn:
            with conn.cursor() as cur:
                for k, v in facts:
                    # If value changed → expire the old fact
                    cur.execute(
                        """UPDATE pr_project_facts SET valid_until=NOW()
                           WHERE client_id=1 AND project=%s
                             AND fact_key=%s AND valid_until IS NULL
                             AND fact_value != %s""",
                        (project, k, v),
                    )
                    # Insert new fact (ON CONFLICT skips if value identical)
                    try:
                        cur.execute(
                            """INSERT INTO pr_project_facts
                                   (client_id, project, fact_key, fact_value, source_memory_id)
                               VALUES (1, %s, %s, %s, %s::uuid)
                               ON CONFLICT (client_id, project, fact_key) WHERE valid_until IS NULL
                               DO NOTHING""",
                            (project, k, v, memory_item_id or src_id),
                        )
                        inserted += cur.rowcount
                    except Exception:
                        pass
            log.debug(
                f"_extract_project_facts: {project} → {inserted} new, "
                f"{len(facts)} passed threshold (model={role_model})"
            )
        return inserted
    except Exception as e:
        log.debug(f"_extract_project_facts failed: {e}")
        return 0


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

    # Load recent history (last 40 entries with user_input, excluding noisy entries)
    recent: list[dict] = []
    hist_file = sys_dir / "history.jsonl"
    if hist_file.exists():
        with open(hist_file) as f:
            raw_lines = [l.strip() for l in f if l.strip()]
        for line in raw_lines[-120:]:
            try:
                e = json.loads(line)
                if e.get("user_input") and not _is_noisy(e):
                    recent.append(e)
            except Exception:
                pass
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
                    cur.execute(
                        """SELECT c.name AS category, c.icon,
                                  v.id, v.name, v.description, v.status, v.due_date, v.parent_id,
                                  COUNT(DISTINCT et.event_id)                                          AS event_count,
                                  COUNT(DISTINCT CASE WHEN ev.event_type='commit' THEN et.event_id END) AS commit_count
                           FROM mng_entity_categories c
                           JOIN mng_entity_values v ON v.category_id = c.id
                           LEFT JOIN pr_event_tags et ON et.entity_value_id = v.id
                           LEFT JOIN pr_events ev ON ev.id = et.event_id AND ev.client_id=1 AND ev.project=%s
                           WHERE c.client_id=1 AND v.project=%s AND v.status != 'archived'
                           GROUP BY c.name, c.icon, v.id, v.name, v.description, v.status, v.due_date, v.parent_id
                           ORDER BY c.name, v.status, COUNT(DISTINCT et.event_id) DESC""",
                        (project_name, project_name),
                    )
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

    # ── Layer 1: summarize new sessions into pr_memory_items (awaited so fresh
    #    summaries are available when we load distilled context below) ──────────
    if db.is_available():
        try:
            await _summarize_session_memory(project_name)
        except Exception:
            pass

    # ── Load distilled context: project_facts + recent memory_items ──────────
    distilled_facts: list[dict] = []
    distilled_memory_items: list[dict] = []
    if db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT fact_key, fact_value FROM pr_project_facts
                           WHERE client_id=1 AND project=%s AND valid_until IS NULL
                           ORDER BY fact_key""",
                        (project_name,),
                    )
                    distilled_facts = [{"key": r[0], "value": r[1]} for r in cur.fetchall()]
                    cur.execute(
                        """SELECT content, scope, scope_ref, created_at FROM pr_memory_items
                           WHERE client_id=1 AND project=%s
                           ORDER BY created_at DESC LIMIT 8""",
                        (project_name,),
                    )
                    distilled_memory_items = [
                        {
                            "content": r[0],
                            "scope": r[1],
                            "scope_ref": r[2] or "",
                            "date": str(r[3])[:10] if r[3] else "",
                        }
                        for r in cur.fetchall()
                    ]
        except Exception as _df_err:
            log.debug(f"distilled context load failed: {_df_err}")

    # Build distilled entity/memory text for synthesis
    distilled_text = ""
    if distilled_facts:
        facts_lines = "\n".join(f"  {f['key']}: {f['value']}" for f in distilled_facts[:12])
        distilled_text += f"[Project Facts]\n{facts_lines}\n\n"
    if distilled_memory_items:
        summaries = "\n---\n".join(m["content"] for m in distilled_memory_items[:3])
        distilled_text += f"[Recent Memory Summaries]\n{summaries}"

    # Merge with entity text for LLM
    combined_entity_text = "\n\n".join(filter(None, [entity_text_for_llm, distilled_text]))

    # ── LLM synthesis (optional — degrades to mechanical approach if API unavailable) ──
    # Incremental: only send new entries to Haiku when ≥3 exist since last run.
    # When distilled memory_items exist, use those instead of raw history to reduce tokens.
    prior_synthesis: dict = state_data.get("_synthesis_cache", {})
    new_entries = [e for e in recent if (e.get("ts") or "") > (last_memory_run or "")]
    # If we have distilled memory, send fewer raw entries (just the newest)
    if distilled_memory_items and len(new_entries) < 10:
        entries_for_llm = new_entries  # distilled context covers the rest
    elif len(new_entries) >= 3:
        entries_for_llm = new_entries
    else:
        entries_for_llm = recent  # fallback: no distilled context yet

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

    # Project Facts — durable extracted facts (always injected, no search needed)
    if distilled_facts:
        memory_lines.append("## Project Facts\n")
        for f in distilled_facts:
            memory_lines.append(f"- **{f['key']}**: {f['value']}")
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

    # Recent Memory — high-quality Trycycle-reviewed summaries from pr_memory_items
    if distilled_memory_items:
        memory_lines.append("## Recent Memory\n")
        memory_lines.append("> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.\n")
        # Show feature-scope items first, then session items
        sorted_items = sorted(
            distilled_memory_items[:6],
            key=lambda m: (0 if m["scope"] == "feature" else 1, m["date"]),
            reverse=False,
        )
        for m in sorted_items:
            scope_label = f"`{m['scope']}"
            if m["scope_ref"]:
                scope_label += f": {m['scope_ref'][:40]}"
            scope_label += f"` — {m['date']}" if m["date"] else "`"
            memory_lines.append(f"### {scope_label}\n")
            memory_lines.append(m["content"])
            memory_lines.append("")

    if synthesis and synthesis.get("memory_digest"):
        # LLM synthesis across all context (supplements memory_items or standalone)
        memory_lines.append("## AI Synthesis\n")
        memory_lines.append(synthesis["memory_digest"])
    elif not distilled_memory_items:
        # Fallback: mechanical Q&A truncation (no API key or synthesis failed and no memory_items)
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
    # Prepend project facts block (high-value stable context)
    if distilled_facts:
        facts_compact = "; ".join(f"{f['key']}={f['value']}" for f in distilled_facts[:6])
        aicli_lines.insert(0, f"[Project Facts] {facts_compact}")
        aicli_lines.insert(1, "")  # blank line separator
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

    # ── Layer 3: extract project facts in background after synthesis ─────────
    if db.is_available() and synthesis:
        try:
            asyncio.create_task(_extract_project_facts(project_name))
        except Exception:
            pass

    # ── Fire-and-forget background tasks (incremental — only process new data) ─
    try:
        from memory.mem_embeddings import ingest_history as _ih, ingest_roles as _ir, ingest_commit as _ic
        # Pass since=last_memory_run so only new history entries are embedded
        asyncio.create_task(_ih(project_name, since=last_memory_run))
        asyncio.create_task(_ir(project_name))  # roles: always re-embed (files may change)

        # Ingest new commits (already filtered by "not in embeddings table")
        code_dir_for_git = cfg.get("code_dir", "")
        if code_dir_for_git and db.is_available():
            asyncio.create_task(_ingest_new_commits(project_name, code_dir_for_git, _ic))

    except Exception:
        pass

    # Entity sync + auto-tag + relationship detection (fire-and-forget)
    if db.is_available():
        try:
            asyncio.create_task(_sync_and_autotag(project_name, since=last_memory_run))
            asyncio.create_task(_detect_relationships(project_name, since=last_memory_run))
        except Exception:
            pass

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
                            cur.execute(
                                """SELECT id, name FROM mng_entity_values
                                   WHERE client_id=1 AND project=%s AND status='active'
                                   ORDER BY name LIMIT 50""",
                                (project_name,),
                            )
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

    # Also count from pr_interactions table (new storage)
    interactions_total = 0
    interactions_since = 0
    if db.is_available():
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) FROM pr_interactions WHERE client_id=1 AND project=%s AND event_type='prompt'",
                        (project_name,),
                    )
                    interactions_total = (cur.fetchone() or (0,))[0]
                    if last_memory_run:
                        cur.execute(
                            "SELECT COUNT(*) FROM pr_interactions WHERE client_id=1 AND project=%s AND event_type='prompt' AND created_at > %s::timestamptz",
                            (project_name, last_memory_run),
                        )
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


async def _ingest_new_commits(project: str, code_dir: str, ingest_commit_fn) -> None:
    """Embed any commits in the DB that have no embeddings yet."""
    if not db.is_available():
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                # Find commit hashes not yet in embeddings
                cur.execute(
                    """SELECT c.commit_hash FROM pr_commits c
                       WHERE c.client_id=1 AND c.project=%s
                         AND NOT EXISTS (
                           SELECT 1 FROM pr_embeddings e
                           WHERE e.client_id=1 AND e.project=%s
                             AND e.source_type='commit' AND e.source_id=c.commit_hash
                       )
                       ORDER BY c.committed_at DESC LIMIT 30""",
                    (project, project),
                )
                hashes = [r[0] for r in cur.fetchall()]
        for h in hashes:
            await ingest_commit_fn(project, h, code_dir)
    except Exception as e:
        logging.getLogger(__name__).debug(f"_ingest_new_commits failed: {e}")


async def _sync_and_autotag(project: str, since: str | None = None) -> None:
    """Sync events then LLM-auto-tag untagged events. Silent on error.

    since: ISO timestamp — only auto-tag events created after this time.
    """
    _log = logging.getLogger(__name__)
    try:
        from routers.entities import _do_sync_events
        _do_sync_events(project)
    except Exception as e:
        _log.debug(f"_sync_and_autotag sync failed: {e}")
        return

    try:
        from core.api_keys import get_key
        key = get_key("claude") or get_key("anthropic")
        if not key:
            return

        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT v.id, c.name AS category, v.name
                       FROM mng_entity_values v
                       JOIN mng_entity_categories c ON c.id = v.category_id AND c.client_id=1
                       WHERE v.client_id=1 AND v.project=%s AND v.status='active'
                       ORDER BY c.name, v.name""",
                    (project,),
                )
                all_values = cur.fetchall()
                if not all_values:
                    return

                # Only tag events that are new (after since) and have no tags yet
                since_filter = "AND e.created_at > %s::timestamptz" if since else ""
                params: list = [project]
                if since:
                    params.append(since)
                cur.execute(
                    f"""SELECT e.id, e.event_type, e.title
                        FROM pr_events e
                        WHERE e.client_id=1 AND e.project=%s
                          AND NOT EXISTS (SELECT 1 FROM pr_event_tags et WHERE et.event_id=e.id)
                          {since_filter}
                        ORDER BY e.created_at DESC LIMIT 30""",
                    params,
                )
                untagged = cur.fetchall()

        if not untagged:
            return

        values_list = "\n".join(f"  {vid}: {cat}/{name}" for vid, cat, name in all_values)
        events_list = "\n".join(f"  {eid}: [{etype}] {title[:80]}" for eid, etype, title in untagged)

        prompt = (
            "You are tagging project events with entity values.\n\n"
            f"Entity values (id: category/name):\n{values_list}\n\n"
            f"Events to tag (id: [type] title):\n{events_list}\n\n"
            "Return ONLY a JSON object mapping event_id (string) to an array of matching "
            "value_ids (integers). Only include confident, specific matches.\n"
            "Example: {\"123\": [2, 5], \"124\": [5]}"
        )

        import anthropic
        client = anthropic.AsyncAnthropic(api_key=key)
        response = await client.messages.create(
            model=settings.haiku_model,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        content = (response.content[0].text if response.content else "").strip()
        if "```" in content:
            for part in content.split("```"):
                s = part.strip()
                if s.startswith("json"):
                    s = s[4:].strip()
                if s.startswith("{"):
                    content = s
                    break

        suggestions: dict = json.loads(content)
        with db.conn() as conn:
            with conn.cursor() as cur:
                for event_id_str, value_ids in suggestions.items():
                    try:
                        eid = int(event_id_str)
                    except (ValueError, TypeError):
                        continue
                    for vid in (value_ids or []):
                        try:
                            cur.execute(
                                "INSERT INTO pr_event_tags (event_id, entity_value_id, auto_tagged) "
                                "VALUES (%s,%s,TRUE) ON CONFLICT DO NOTHING",
                                (eid, int(vid)),
                            )
                        except Exception:
                            pass

    except Exception as e:
        logging.getLogger(__name__).debug(f"_sync_and_autotag auto-tag failed: {e}")


async def _detect_relationships(project: str, since: str | None = None) -> None:
    """Detect and create relationships between new events. Silent on error.

    Two strategies:
    1. Keyword: commit messages containing fix/close/resolve → links to bug events
    2. LLM: Haiku analyzes batches of new events and suggests semantic relationships
    """
    _log = logging.getLogger(__name__)
    if not db.is_available():
        return
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                # Get new events (after since)
                if since:
                    where_clause = "AND created_at > %s::timestamptz"
                    params: list = [project, since]
                else:
                    where_clause = ""
                    params = [project]
                cur.execute(
                    f"""SELECT id, event_type, source_id, title, content, metadata
                        FROM pr_events
                        WHERE client_id=1 AND project=%s {where_clause}
                        ORDER BY created_at DESC LIMIT 50""",
                    params,
                )
                new_events = cur.fetchall()  # (id, type, source_id, title, content, meta)

                if not new_events:
                    return

                rows_by_type: dict[str, list] = {}
                for r in new_events:
                    eid, etype, src_id, title, content, meta = r
                    rows_by_type.setdefault(etype, []).append((eid, src_id, title, content, meta))

                # Keyword: commits with fix/close/resolve → link to bug events
                import re as _re
                bug_events = {
                    r[2].lower(): r[0]  # title.lower() → id
                    for r in new_events if r[1] == "prompt"  # look for bug-tagged prompts
                }
                for eid, src_id, title, content, meta in rows_by_type.get("commit", []):
                    msg = (title or content or "").lower()
                    link_type = None
                    if _re.search(r'\b(fix|fixe[sd]|close[sd]?|resolve[sd]?)\b', msg):
                        link_type = "fixes"
                    elif _re.search(r'\bimplements?\b', msg):
                        link_type = "implements"
                    if not link_type:
                        continue
                    # Try to link to a feature/bug event by keyword match
                    for bug_title, bug_id in bug_events.items():
                        if eid != bug_id and any(
                            word in msg for word in bug_title.split()[:3] if len(word) > 4
                        ):
                            try:
                                cur.execute(
                                    "INSERT INTO pr_event_links (from_event_id, to_event_id, link_type) "
                                    "VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                                    (eid, bug_id, link_type),
                                )
                            except Exception:
                                pass

        # Strategy 2: LLM-based relationship suggestion (only if Anthropic key available)
        from core.api_keys import get_key
        key = get_key("claude") or get_key("anthropic")
        if not key or len(new_events) < 2:
            return

        events_summary = "\n".join(
            f"  {r[0]}: [{r[1]}] {r[3][:80]}" for r in new_events[:20]
        )
        prompt = (
            "Analyze these project events and identify meaningful relationships between them.\n\n"
            f"Events (id: [type] title):\n{events_summary}\n\n"
            "Return ONLY a JSON array of relationships. Each item: "
            "{\"from\": id, \"to\": id, \"type\": link_type}\n"
            f"link_type must be one of: implements, fixes, causes, relates_to, references, closes\n"
            "Only include high-confidence relationships. Return [] if none are clear.\n"
            "Example: [{\"from\": 10, \"to\": 5, \"type\": \"fixes\"}]"
        )

        import anthropic
        client = anthropic.AsyncAnthropic(api_key=key)
        response = await client.messages.create(
            model=settings.haiku_model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        text = (response.content[0].text if response.content else "").strip()
        import re as _re2
        match = _re2.search(r'\[.*?\]', text, _re2.DOTALL)
        if not match:
            return
        relationships: list = json.loads(match.group())

        if not relationships:
            return

        with db.conn() as conn:
            with conn.cursor() as cur:
                for rel in relationships:
                    try:
                        cur.execute(
                            "INSERT INTO pr_event_links (from_event_id, to_event_id, link_type) "
                            "VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                            (int(rel["from"]), int(rel["to"]), rel["type"]),
                        )
                    except Exception:
                        pass

    except Exception as e:
        _log.debug(f"_detect_relationships failed: {e}")


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
