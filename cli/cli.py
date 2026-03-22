"""
cli/cli.py — aicli HTTP-only CLI client.

Interactive REPL that communicates exclusively with the backend via HTTP.
No direct LLM provider imports — all AI calls go through POST /chat.

Features:
  - prompt_toolkit REPL with history + tab completion
  - Session persistence (JSON file)
  - [Project Facts] context injected before each prompt
  - /memory, /switch, /project, /history slash commands
  - SSE streaming display
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Iterator

import httpx
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# ── Config ─────────────────────────────────────────────────────────────────────

_AICLI_DIR = Path.home() / ".aicli"
_AICLI_DIR.mkdir(exist_ok=True)

_config_path = _AICLI_DIR / "config.json"
_session_path = _AICLI_DIR / "cli_session.json"
_history_path = _AICLI_DIR / "cli_history"


def _load_config() -> dict:
    if _config_path.exists():
        try:
            return json.loads(_config_path.read_text())
        except Exception:
            pass
    return {}


def _save_config(cfg: dict) -> None:
    _config_path.write_text(json.dumps(cfg, indent=2))


_cfg = _load_config()
BACKEND_URL: str = os.environ.get("BACKEND_URL", _cfg.get("backend_url", "http://localhost:8000"))
ACTIVE_PROJECT: str = os.environ.get("ACTIVE_PROJECT", _cfg.get("active_project", "aicli"))
ACTIVE_PROVIDER: str = os.environ.get("PROVIDER", _cfg.get("provider", "claude"))

console = Console()

SLASH_COMMANDS = [
    "/memory", "/switch", "/project", "/history", "/search",
    "/status", "/help", "/clear", "/exit", "/run",
    "/tag", "/tags", "/phase",
    "/role", "/pipeline",
]

# ── Session state ──────────────────────────────────────────────────────────────

def _load_session() -> dict:
    if _session_path.exists():
        try:
            return json.loads(_session_path.read_text())
        except Exception:
            pass
    return {
        "session_id": f"cli_{int(time.time())}",
        "provider": ACTIVE_PROVIDER,
        "project": ACTIVE_PROJECT,
        "phase": "",
        "feature": "",
    }


def _save_session(state: dict) -> None:
    _session_path.write_text(json.dumps(state, indent=2))


# ── Backend HTTP helpers ───────────────────────────────────────────────────────

def _backend_get(path: str, timeout: float = 5.0) -> dict | list | None:
    try:
        r = httpx.get(f"{BACKEND_URL}{path}", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _backend_post(path: str, body: dict, timeout: float = 30.0) -> dict | None:
    try:
        r = httpx.post(f"{BACKEND_URL}{path}", json=body, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        console.print(f"[red]Backend error: {e}[/red]")
        return None


def _stream_chat(body: dict) -> str:
    """Call POST /chat and stream SSE response. Returns full text."""
    url = f"{BACKEND_URL}/chat"
    full_text = ""
    try:
        with httpx.stream("POST", url, json=body, timeout=120.0) as resp:
            resp.raise_for_status()
            console.print()
            for line in resp.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        text = chunk.get("content", "") or chunk.get("text", "")
                        if text:
                            print(text, end="", flush=True)
                            full_text += text
                    except json.JSONDecodeError:
                        print(data, end="", flush=True)
                        full_text += data
            print()  # newline after streaming
    except httpx.HTTPStatusError as e:
        console.print(f"\n[red]HTTP {e.response.status_code}: {e.response.text[:200]}[/red]")
    except Exception as e:
        if full_text:
            pass  # partial response received
        else:
            console.print(f"\n[red]Stream error: {e}[/red]")
    return full_text


def _load_project_facts(project: str) -> str:
    """Fetch project facts from backend (used as context prefix)."""
    data = _backend_get(f"/work-items/facts?project={project}", timeout=2.0)
    if not data or not isinstance(data, dict):
        return ""
    facts = data.get("facts", {})
    if not facts:
        return ""
    lines = [f"  {k}: {v}" for k, v in facts.items()]
    return "[Project Facts]\n" + "\n".join(lines)


def _load_context_md(project: str) -> str:
    """Load _system/aicli/context.md from workspace if available."""
    cfg = _load_config()
    workspace = cfg.get("workspace_dir") or str(Path.home() / "workspace")
    ctx_path = Path(workspace) / project / "_system" / "aicli" / "context.md"
    if ctx_path.exists():
        try:
            return ctx_path.read_text()[:3000]
        except Exception:
            pass
    return ""


# ── Slash command handlers ─────────────────────────────────────────────────────

def _cmd_memory(session: dict) -> None:
    project = session["project"]
    console.print(f"[yellow]Generating memory for {project}...[/yellow]")
    result = _backend_post(f"/projects/{project}/memory", {}, timeout=180.0)
    if result:
        console.print("[green]Memory updated.[/green]")
        if result.get("suggested_tags"):
            console.print(f"[dim]Suggested tags: {result['suggested_tags']}[/dim]")
    else:
        console.print("[red]Memory generation failed.[/red]")


def _cmd_switch(session: dict, args: str) -> None:
    parts = args.strip().split()
    if not parts:
        console.print("[yellow]Usage: /switch <provider>[/yellow]")
        return
    provider = parts[0].lower()
    session["provider"] = provider
    _save_session(session)
    console.print(f"[green]Switched to provider: {provider}[/green]")


def _cmd_project(session: dict, args: str) -> None:
    parts = args.strip().split()
    if not parts:
        console.print(f"Current project: [cyan]{session['project']}[/cyan]")
        return
    project = parts[0]
    session["project"] = project
    _save_session(session)
    console.print(f"[green]Switched to project: {project}[/green]")


def _cmd_history(session: dict) -> None:
    project = session["project"]
    data = _backend_get(f"/history?project={project}&limit=10")
    if not data:
        console.print("[dim]No history.[/dim]")
        return
    entries = data if isinstance(data, list) else data.get("entries", [])
    for e in entries[-10:]:
        ts = e.get("timestamp", "")[:16]
        role = e.get("role", "")
        text = (e.get("content", "") or "")[:80]
        console.print(f"[dim]{ts}[/dim] [cyan]{role}[/cyan]: {text}...")


def _cmd_status(session: dict) -> None:
    data = _backend_get("/health")
    if data:
        console.print(Panel(
            f"Backend: [green]ok[/green]\n"
            f"Project: [cyan]{session['project']}[/cyan]\n"
            f"Provider: [cyan]{session['provider']}[/cyan]\n"
            f"Phase: [cyan]{session.get('phase', '-')}[/cyan]",
            title="aicli status",
        ))
    else:
        console.print(f"[red]Backend not reachable: {BACKEND_URL}[/red]")


def _cmd_help() -> None:
    console.print(Panel(
        "\n".join([
            "[bold]/memory[/bold]               Synthesize and save project memory",
            "[bold]/switch <p>[/bold]           Switch LLM provider (claude/openai/deepseek/gemini/grok)",
            "[bold]/project <n>[/bold]          Switch active project",
            "[bold]/history[/bold]              Show recent conversation history",
            "[bold]/status[/bold]               Show backend status",
            "[bold]/run <name>[/bold]           Trigger a named workflow pipeline",
            "[bold]/role list[/bold]            List all agent roles",
            "[bold]/role view <name>[/bold]     Show role details (tools, ReAct, etc.)",
            "[bold]/role push <yaml>[/bold]     Sync a YAML role file to DB",
            "[bold]/role pull <name>[/bold]     Export a DB role to YAML file",
            "[bold]/pipeline list[/bold]        List all pipelines",
            "[bold]/pipeline view <name>[/bold] Show pipeline nodes",
            "[bold]/pipeline push <yaml>[/bold] Import a YAML pipeline to DB",
            "[bold]/pipeline pull <name>[/bold] Export a pipeline to YAML file",
            "[bold]/clear[/bold]                Clear screen",
            "[bold]/exit[/bold]                 Exit the CLI",
        ]),
        title="aicli Commands",
    ))


def _cmd_role(session: dict, args: str) -> None:
    """Handle /role list|view|push|pull commands."""
    parts = args.strip().split(None, 1)
    sub   = parts[0].lower() if parts else "list"
    rest  = parts[1] if len(parts) > 1 else ""

    if sub == "list":
        data = _backend_get(f"/agent-roles/?project=_global")
        if not data:
            console.print("[red]Could not fetch roles.[/red]")
            return
        roles = data.get("roles", [])
        from rich.table import Table
        t = Table(show_header=True, header_style="bold cyan")
        t.add_column("Name", min_width=20)
        t.add_column("Provider", width=12)
        t.add_column("Model", width=22)
        t.add_column("Tools", width=6, justify="right")
        t.add_column("ReAct", width=6)
        for r in roles:
            if r.get("role_type") == "internal":
                continue
            t.add_row(
                r.get("name", ""),
                r.get("provider", ""),
                r.get("model", ""),
                str(len(r.get("tools", []))),
                "✓" if r.get("react") else "—",
            )
        console.print(t)

    elif sub == "view":
        name = rest.strip()
        if not name:
            console.print("[yellow]Usage: /role view <name>[/yellow]")
            return
        data = _backend_get(f"/agent-roles/?project=_global")
        if not data:
            console.print("[red]Could not fetch roles.[/red]")
            return
        roles = data.get("roles", [])
        role  = next((r for r in roles if r["name"].lower() == name.lower()), None)
        if not role:
            console.print(f"[red]Role '{name}' not found.[/red]")
            return
        tools = role.get("tools", [])
        console.print(Panel(
            f"[bold]{role['name']}[/bold]  [{role.get('role_type','agent')}]\n"
            f"Provider: [cyan]{role.get('provider','')}[/cyan]  "
            f"Model: [cyan]{role.get('model','')}[/cyan]\n"
            f"ReAct: {'[green]yes[/green]' if role.get('react') else '[dim]no[/dim]'}  "
            f"Max iter: {role.get('max_iterations',10)}\n"
            f"Tools ({len(tools)}): {', '.join(tools) or '[dim]none[/dim]'}\n\n"
            f"{role.get('description','')}",
            title="Role Details",
        ))

    elif sub == "push":
        yaml_path = rest.strip()
        if not yaml_path:
            console.print("[yellow]Usage: /role push <yaml_path>[/yellow]")
            return
        p = Path(yaml_path).expanduser()
        if not p.exists():
            console.print(f"[red]File not found: {yaml_path}[/red]")
            return
        yaml_content = p.read_text()
        result = _backend_post("/agent-roles/sync-yaml", {
            "yaml_content": yaml_content,
            "project":      "_global",
        })
        if result:
            console.print(f"[green]{result.get('message', 'Role synced.')}[/green]")
        else:
            console.print("[red]Push failed.[/red]")

    elif sub == "pull":
        parts2   = rest.strip().split(None, 1)
        name     = parts2[0] if parts2 else ""
        out_path = parts2[1] if len(parts2) > 1 else ""
        if not name:
            console.print("[yellow]Usage: /role pull <name> [out_path][/yellow]")
            return
        # Find role ID
        data = _backend_get(f"/agent-roles/?project=_global")
        if not data:
            console.print("[red]Could not fetch roles.[/red]")
            return
        roles = data.get("roles", [])
        role  = next((r for r in roles if r["name"].lower() == name.lower()), None)
        if not role or not role.get("id"):
            console.print(f"[red]Role '{name}' not found or has no DB ID.[/red]")
            return
        try:
            r = httpx.get(f"{BACKEND_URL}/agent-roles/{role['id']}/export-yaml", timeout=10.0)
            r.raise_for_status()
            yaml_str = r.text
        except Exception as e:
            console.print(f"[red]Export failed: {e}[/red]")
            return
        if not out_path:
            cfg = _load_config()
            workspace = cfg.get("workspace_dir", str(Path.home() / "workspace"))
            out_path  = str(Path(workspace) / "_templates" / "roles" / f"{name.lower().replace(' ', '_')}.yaml")
        out_p = Path(out_path).expanduser()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(yaml_str)
        console.print(f"[green]Role '{name}' saved to {out_p}[/green]")

    else:
        console.print("[yellow]Usage: /role list | view <name> | push <yaml> | pull <name> [path][/yellow]")


def _cmd_pipeline(session: dict, args: str) -> None:
    """Handle /pipeline list|view|push|pull commands."""
    parts = args.strip().split(None, 1)
    sub   = parts[0].lower() if parts else "list"
    rest  = parts[1] if len(parts) > 1 else ""
    project = session["project"]

    if sub == "list":
        data = _backend_get(f"/graph-workflows/?project={project}")
        if not data:
            console.print("[red]Could not fetch pipelines.[/red]")
            return
        workflows = data if isinstance(data, list) else data.get("workflows", [])
        from rich.table import Table
        t = Table(show_header=True, header_style="bold cyan")
        t.add_column("Name", min_width=25)
        t.add_column("Max Iter", width=10, justify="right")
        t.add_column("Created", width=12)
        for w in workflows:
            ts = (w.get("created_at") or "")[:10]
            t.add_row(w.get("name", ""), str(w.get("max_iterations", "?")), ts)
        console.print(t)

    elif sub == "view":
        name = rest.strip()
        if not name:
            console.print("[yellow]Usage: /pipeline view <name>[/yellow]")
            return
        data = _backend_get(f"/graph-workflows/?project={project}")
        if not data:
            console.print("[red]Could not fetch pipelines.[/red]")
            return
        workflows = data if isinstance(data, list) else data.get("workflows", [])
        wf = next((w for w in workflows if w.get("name", "").lower() == name.lower()), None)
        if not wf:
            console.print(f"[red]Pipeline '{name}' not found.[/red]")
            return
        detail = _backend_get(f"/graph-workflows/{wf['id']}")
        if not detail:
            console.print("[red]Could not fetch pipeline details.[/red]")
            return
        nodes = detail.get("nodes", [])
        lines = [f"[bold]{wf['name']}[/bold]  ({len(nodes)} nodes)"]
        for i, n in enumerate(nodes, 1):
            lines.append(f"  {i}. {n.get('name','')} — role: {n.get('role_id','?')}")
        console.print(Panel("\n".join(lines), title="Pipeline"))

    elif sub == "push":
        yaml_path = rest.strip()
        if not yaml_path:
            console.print("[yellow]Usage: /pipeline push <yaml_path>[/yellow]")
            return
        p = Path(yaml_path).expanduser()
        if not p.exists():
            console.print(f"[red]File not found: {yaml_path}[/red]")
            return
        yaml_content = p.read_text()
        result = _backend_post("/graph-workflows/import-yaml", {
            "yaml_content": yaml_content,
            "project":      project,
        })
        if result:
            console.print(f"[green]Pipeline synced: {result.get('name', 'ok')}[/green]")
        else:
            console.print("[red]Push failed.[/red]")

    elif sub == "pull":
        parts2   = rest.strip().split(None, 1)
        name     = parts2[0] if parts2 else ""
        out_path = parts2[1] if len(parts2) > 1 else ""
        if not name:
            console.print("[yellow]Usage: /pipeline pull <name> [out_path][/yellow]")
            return
        data = _backend_get(f"/graph-workflows/?project={project}")
        if not data:
            console.print("[red]Could not fetch pipelines.[/red]")
            return
        workflows = data if isinstance(data, list) else data.get("workflows", [])
        wf = next((w for w in workflows if w.get("name", "").lower() == name.lower()), None)
        if not wf:
            console.print(f"[red]Pipeline '{name}' not found.[/red]")
            return
        try:
            r = httpx.get(f"{BACKEND_URL}/graph-workflows/{wf['id']}/export-yaml", timeout=10.0)
            r.raise_for_status()
            yaml_str = r.text
        except Exception as e:
            console.print(f"[red]Export failed: {e}[/red]")
            return
        if not out_path:
            cfg = _load_config()
            workspace = cfg.get("workspace_dir", str(Path.home() / "workspace"))
            out_path  = str(Path(workspace) / project / "pipelines" / f"{name.lower().replace(' ', '_')}.yaml")
        out_p = Path(out_path).expanduser()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(yaml_str)
        console.print(f"[green]Pipeline '{name}' saved to {out_p}[/green]")

    else:
        console.print("[yellow]Usage: /pipeline list | view <name> | push <yaml> | pull <name> [path][/yellow]")


def _cmd_run(session: dict, args: str) -> None:
    name = args.strip()
    if not name:
        console.print("[yellow]Usage: /run <pipeline-name>[/yellow]")
        return
    project = session["project"]
    # Look up workflow by name
    workflows = _backend_get(f"/graph/workflows?project={project}")
    if not workflows:
        console.print("[red]No workflows found.[/red]")
        return
    wf = next((w for w in workflows if w.get("name", "").lower() == name.lower()), None)
    if not wf:
        console.print(f"[red]Workflow '{name}' not found.[/red]")
        console.print(f"Available: {', '.join(w['name'] for w in workflows)}")
        return
    result = _backend_post("/graph/run", {
        "workflow_id": wf["id"],
        "user_input": f"Run {name}",
        "project": project,
    })
    if result:
        run_id = result.get("run_id", "?")
        console.print(f"[green]Pipeline started: run_id={run_id}[/green]")


# ── Main REPL ──────────────────────────────────────────────────────────────────

def main() -> None:
    session = _load_session()
    # Allow overriding via env
    if os.environ.get("ACTIVE_PROJECT"):
        session["project"] = os.environ["ACTIVE_PROJECT"]
    if os.environ.get("PROVIDER"):
        session["provider"] = os.environ["PROVIDER"]

    completer = WordCompleter(SLASH_COMMANDS, match_middle=True)
    ps = PromptSession(
        history=FileHistory(str(_history_path)),
        auto_suggest=AutoSuggestFromHistory(),
        completer=completer,
    )

    console.print(Panel(
        f"[bold cyan]aicli[/bold cyan]  project=[green]{session['project']}[/green]  "
        f"provider=[green]{session['provider']}[/green]\n"
        f"backend=[dim]{BACKEND_URL}[/dim]  /help for commands",
        title="aicli CLI",
    ))

    # Warm up: check backend
    health = _backend_get("/health", timeout=2.0)
    if not health:
        console.print(f"[yellow]⚠ Backend not reachable at {BACKEND_URL} — start it first.[/yellow]")

    while True:
        try:
            project = session["project"]
            provider = session["provider"]
            prompt_str = f"[{project}][{provider}]> "
            user_input = ps.prompt(prompt_str).strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Bye![/dim]")
            break

        if not user_input:
            continue

        # ── Slash commands ────────────────────────────────────────────────────
        if user_input.startswith("/"):
            parts = user_input.split(None, 1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            if cmd in ("/exit", "/quit"):
                console.print("[dim]Bye![/dim]")
                break
            elif cmd == "/clear":
                os.system("clear")
            elif cmd == "/help":
                _cmd_help()
            elif cmd == "/memory":
                _cmd_memory(session)
            elif cmd == "/switch":
                _cmd_switch(session, args)
            elif cmd in ("/project", "/p"):
                _cmd_project(session, args)
            elif cmd == "/history":
                _cmd_history(session)
            elif cmd == "/status":
                _cmd_status(session)
            elif cmd == "/run":
                _cmd_run(session, args)
            elif cmd == "/role":
                _cmd_role(session, args)
            elif cmd == "/pipeline":
                _cmd_pipeline(session, args)
            else:
                console.print(f"[red]Unknown command: {cmd}[/red]  /help for list")
            continue

        # ── Chat ──────────────────────────────────────────────────────────────
        project = session["project"]
        provider = session["provider"]

        # Build context prefix
        facts = _load_project_facts(project)
        context_md = _load_context_md(project)
        prefix_parts = []
        if facts:
            prefix_parts.append(facts)
        if context_md:
            prefix_parts.append(context_md)

        full_prompt = "\n\n".join(prefix_parts + [user_input]) if prefix_parts else user_input

        body = {
            "message": full_prompt,
            "provider": provider,
            "project": project,
            "session_id": session.get("session_id", ""),
            "phase": session.get("phase", ""),
            "feature": session.get("feature", ""),
            "stream": True,
        }

        _stream_chat(body)

    _save_session(session)


if __name__ == "__main__":
    main()
