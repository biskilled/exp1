"""
Projects router — list/create/switch projects from templates.
"""

import asyncio
import json
import shutil
import yaml
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from config import settings

router = APIRouter()


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
    claude_cli_support: bool = False
    cursor_support: bool = False
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

        if body.claude_cli_support and hooks_src.exists():
            # Install hooks into _system/hooks/ (not .aicli/scripts/)
            hooks_dest = sys_dir / "hooks"
            hooks_dest.mkdir(parents=True, exist_ok=True)
            for sh in hooks_src.glob("*.sh"):
                shutil.copy2(str(sh), str(hooks_dest / sh.name))
            # Render settings.template.json → {code_dir}/.claude/settings.local.json
            # Hooks point to workspace/{project}/_system/hooks/ (canonical location)
            tpl_file = hooks_src / "settings.template.json"
            if tpl_file.exists():
                tpl_content = (tpl_file.read_text()
                               .replace("{{WORKSPACE_DIR}}", str(ws))
                               .replace("{{PROJECT_NAME}}", body.name))
                settings_dir = code_path / ".claude"
                settings_dir.mkdir(parents=True, exist_ok=True)
                (settings_dir / "settings.local.json").write_text(tpl_content)
            setup_results["claude_cli"] = str(hooks_dest)

        if body.cursor_support:
            cursor_rules_dir = code_path / ".cursor" / "rules"
            cursor_rules_dir.mkdir(parents=True, exist_ok=True)
            # Initial rules stub
            proj_md = dest_dir / "PROJECT.md"
            proj_summary = proj_md.read_text()[:400] if proj_md.exists() else ""
            rules_content = f"# AI Rules — {body.name}\n> Managed by aicli. Re-run `/memory` to refresh.\n\n## Project\n{proj_summary}\n"
            (cursor_rules_dir / "aicli.mdrules").write_text(rules_content)
            setup_results["cursor"] = str(cursor_rules_dir)

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

    # 4. Recent history — last 15 exchanges (in _system/)
    recent: list[dict] = []
    for hist_file in [sys_dir / "history.jsonl", proj_dir / "history" / "history.jsonl"]:
        if hist_file.exists():
            with open(hist_file) as f:
                lines = [l.strip() for l in f if l.strip()]
            for line in lines[-30:]:
                try:
                    e = json.loads(line)
                    if e.get("user_input"):
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


@router.post("/{project_name}/memory")
async def generate_memory(project_name: str):
    """Generate per-LLM memory files and copy to code_dir.

    Reads history.jsonl + project_state.json to generate:
      _system/claude/MEMORY.md    — distilled session history
      _system/claude/CLAUDE.md    — refreshed project context
      _system/cursor/rules.md     — Cursor AI rules
      _system/aicli/context.md    — compact aicli injection block
    Then copies files to code_dir if set in project.yaml.
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

    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Load recent history (last 30 entries)
    recent: list[dict] = []
    hist_file = sys_dir / "history.jsonl"
    if hist_file.exists():
        with open(hist_file) as f:
            lines = [l.strip() for l in f if l.strip()]
        for line in lines[-60:]:
            try:
                e = json.loads(line)
                if e.get("user_input"):
                    recent.append(e)
            except Exception:
                pass
        recent = recent[-30:]

    # Load project_state.json
    state_data: dict = {}
    for p in [sys_dir / "project_state.json", proj_dir / "project_state.json"]:
        if p.exists():
            try:
                state_data = json.loads(p.read_text())
                break
            except Exception:
                pass

    # Load PROJECT.md
    project_md = ""
    if (proj_dir / "PROJECT.md").exists():
        project_md = (proj_dir / "PROJECT.md").read_text()

    generated: list[str] = []

    # ── 1. MEMORY.md ──────────────────────────────────────────────────────────
    memory_lines = [
        f"# Project Memory — {project_name}",
        f"_Generated: {ts}_\n",
        "## Recent Sessions\n",
        "| Date | Source | Prompt |",
        "|------|--------|--------|",
    ]
    for e in recent[-10:]:
        date = (e.get("ts") or "")[:10]
        source = e.get("source", "")
        preview = (e.get("user_input") or "")[:80].replace("\n", " ").replace("|", "\\|")
        memory_lines.append(f"| {date} | {source} | {preview} |")

    if state_data.get("key_decisions"):
        memory_lines.append("\n## Key Decisions\n")
        for d in state_data["key_decisions"]:
            memory_lines.append(f"- {d}")

    if cfg.get("active_workflows"):
        memory_lines.append("\n## Active Workflows\n")
        for w in cfg["active_workflows"]:
            memory_lines.append(f"- {w}")

    memory_md = "\n".join(memory_lines)
    (sys_dir / "claude" / "MEMORY.md").write_text(memory_md)
    generated.append("_system/claude/MEMORY.md")

    # ── 2. CLAUDE.md — reuse get_context logic ────────────────────────────────
    # Call get_context with save=True to regenerate both CONTEXT.md and CLAUDE.md
    try:
        ctx_result = await get_project_context(project_name, save=True)
        claude_md_content = ctx_result.get("claude_md", "")
        generated.append("_system/claude/CLAUDE.md")
    except Exception:
        claude_md_content = ""

    # ── 3. cursor/rules.md ────────────────────────────────────────────────────
    cursor_lines = [
        f"# AI Rules — {project_name}",
        "> Managed by aicli. Re-run `/memory` to refresh.\n",
        "## Project\n",
        project_md[:400] if project_md else f"Project: {project_name}",
    ]
    if state_data.get("tech_stack"):
        cursor_lines.append("\n## Tech Stack\n")
        for k, v in state_data["tech_stack"].items():
            cursor_lines.append(f"- **{k}**: {v}")
    if state_data.get("key_decisions"):
        cursor_lines.append("\n## Key Decisions\n")
        for d in state_data["key_decisions"]:
            cursor_lines.append(f"- {d}")
    cursor_md = "\n".join(cursor_lines)
    (sys_dir / "cursor" / "rules.md").write_text(cursor_md)
    generated.append("_system/cursor/rules.md")

    # ── 4. aicli/context.md — compact injection block ─────────────────────────
    aicli_lines = [f"# {project_name} context"]
    if project_md:
        aicli_lines.append(project_md[:500])
    if state_data.get("in_progress"):
        aicli_lines.append(f"\nIn progress: {', '.join(state_data['in_progress'][:3])}")
    if recent:
        last = recent[-1]
        aicli_lines.append(f"\nLast prompt ({(last.get('ts') or '')[:10]}): {(last.get('user_input') or '')[:100]}")
    aicli_context = "\n".join(aicli_lines)
    (sys_dir / "aicli" / "context.md").write_text(aicli_context)
    generated.append("_system/aicli/context.md")

    # ── 5. Copy to code_dir ───────────────────────────────────────────────────
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
            try:
                (code_path / "CLAUDE.md").write_text(claude_md_content)
                copied_to.append(str(code_path / "CLAUDE.md"))
            except Exception:
                pass
            try:
                (code_path / "MEMORY.md").write_text(memory_md)
                copied_to.append(str(code_path / "MEMORY.md"))
            except Exception:
                pass
            try:
                cursor_rules_path = code_path / ".cursor" / "rules"
                cursor_rules_path.mkdir(parents=True, exist_ok=True)
                (cursor_rules_path / "aicli.mdrules").write_text(cursor_md)
                copied_to.append(str(cursor_rules_path / "aicli.mdrules"))
            except Exception:
                pass

    return {"generated": generated, "copied_to": copied_to, "skipped_copy": skipped_copy}


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
