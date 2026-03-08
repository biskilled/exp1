"""
Projects router — list/create/switch projects from templates.
"""

import asyncio
import json
import re
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
    # Embed updated PROJECT.md for semantic search (fire-and-forget)
    try:
        from core.embeddings import embed_and_store as _embed
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
) -> dict | None:
    """Use Claude Haiku to intelligently synthesize project history into structured memory.

    Reads the last 40 history entries and produces a dict with:
      key_decisions, in_progress, tech_stack, memory_digest, project_summary.
    Returns None silently if the API key is missing or any error occurs — callers
    fall back to mechanical string-slicing in that case.
    """
    try:
        import anthropic
        from core.api_keys import get_key

        key = get_key("claude")
        if not key:
            return None

        # Build history text (oldest first, last 40 entries with user_input)
        history_lines: list[str] = []
        for e in history[-40:]:
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

        prompt = (
            f'You are analyzing development history for project "{project_name}".\n\n'
            f"Current structured state:\n{current_state}\n\n"
            f"Project intro (from PROJECT.md):\n{proj_intro}\n\n"
            f"Development history ({len(history)} sessions, oldest→newest):\n{history_text}\n\n"
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
            model="claude-haiku-4-5-20251001",
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


@router.post("/{project_name}/memory")
async def generate_memory(project_name: str):
    """Generate per-LLM memory files and copy to code_dir.

    Generates files for every AI tool in use:
      _system/claude/MEMORY.md         — distilled Q&A history + decisions (Claude CLI reads at session start)
      _system/claude/CLAUDE.md         — refreshed project context + MEMORY.md reference
      _system/cursor/rules.md          — Cursor AI rules file
      _system/aicli/context.md         — compact block injected by aicli CLI into ALL providers
      _system/aicli/copilot.md         — GitHub Copilot instructions

    Copies to code_dir:
      {code_dir}/CLAUDE.md             → Claude CLI auto-loads
      {code_dir}/MEMORY.md             → referenced in CLAUDE.md so Claude reads it
      {code_dir}/.cursor/rules/aicli.mdrules  → Cursor AI
      {code_dir}/.github/copilot-instructions.md → GitHub Copilot
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

    # Load recent history (last 40 entries with user_input)
    recent: list[dict] = []
    hist_file = sys_dir / "history.jsonl"
    if hist_file.exists():
        with open(hist_file) as f:
            raw_lines = [l.strip() for l in f if l.strip()]
        for line in raw_lines[-80:]:
            try:
                e = json.loads(line)
                if e.get("user_input"):
                    recent.append(e)
            except Exception:
                pass
        recent = recent[-40:]

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

    # ── LLM synthesis (optional — degrades to mechanical approach if API unavailable) ──
    synthesis = await _synthesize_with_llm(project_name, recent, state_data, project_md)
    if synthesis:
        # Merge LLM-extracted structured data into state_data (LLM wins on new fields)
        if synthesis.get("tech_stack"):
            state_data.setdefault("tech_stack", {}).update(synthesis["tech_stack"])
        if synthesis.get("key_decisions"):
            state_data["key_decisions"] = synthesis["key_decisions"]
        if synthesis.get("in_progress"):
            state_data["in_progress"] = synthesis["in_progress"]
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

    if synthesis and synthesis.get("memory_digest"):
        # LLM-synthesized meaningful digest of recent work
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

    # Embed history + roles for semantic search (fire-and-forget)
    try:
        from core.embeddings import ingest_history as _ih, ingest_roles as _ir
        asyncio.create_task(_ih(project_name))
        asyncio.create_task(_ir(project_name))
    except Exception:
        pass

    return {
        "generated": generated,
        "copied_to": copied_to,
        "skipped_copy": skipped_copy,
        "synthesized": synthesis is not None,
    }


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
