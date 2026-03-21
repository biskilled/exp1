"""
aicli — AI-powered development CLI

Uses prompt_toolkit for the interactive REPL instead of typer+input():
  - ↑/↓ command history
  - Tab autocomplete for slash commands
  - Ctrl+C safe (doesn't crash)
  - Multi-line paste support

Claude uses the Anthropic SDK (not subprocess CLI):
  - Same CLAUDE.md awareness (passed as system prompt)
  - Same conversation history (self.messages list)
  - Added: tool use (bash, read_file, write_file, list_directory)
    → replicates what the claude CLI provides as built-in tools
  - Cross-session memory via MemoryStore (JSONL)
"""

import os
import sys
import json as _json
import shutil
import yaml
import concurrent.futures
from datetime import datetime
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.columns import Columns

from providers.claude_agent import ClaudeAgent
from providers.openai_agent import OpenAIAgent
from core.conversation import ConversationState
from core.git_supervisor import GitSupervisor
from core.analytics import ProjectAnalytics
from core.logger import StructuredLogger
from core.memory import MemoryStore
from core.hooks import HookRunner
from core.project_docs import ProjectDocs, TEMPLATE
from core.summary import build_project_summary, generate_system_summary
from core.env_loader import load_environment
from workflows.runner import WorkflowRunner
from gitops.manager import checkout_branch, get_current_branch
from prompts.loader import build_md, load_openai_role, load_openai_system
from core.session_store import (
    SessionStore,
    load_session_state,
    save_session_state,
    format_session_state_for_prompt,
)

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Resolved once at import time — stays correct after os.chdir()
CLI_ROOT = Path(__file__).parent.resolve()

console = Console()

SLASH_COMMANDS = [
    "/switch", "/workflow", "/project",
    "/memory",
    "/branch", "/feature", "/tag", "/tags", "/search-tag",
    "/docs", "/docs generate", "/docs todo",
    "/compare",
    "/status", "/history", "/analytics",
    "/reload", "/clear", "/push",
    "/deploy", "/qa", "/help", "/exit",
    # Legacy aliases
    "/claude", "/openai",
    "/project new", "/project list", "/project switch",
]

PROVIDER_NAMES = ["claude", "openai", "deepseek", "gemini", "grok"]


# ======================================================================
# OSC 8 hyperlink helper
# ======================================================================

def _hyperlink(text: str, uri: str) -> str:
    """Return an OSC 8 terminal hyperlink (opens uri on click in supported terminals)."""
    return f"\033]8;;{uri}\033\\{text}\033]8;;\033\\"


# ======================================================================
# INITIALIZATION
# ======================================================================

def load_config() -> dict:
    with open(CLI_ROOT / "aicli.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def initialize_project(config: dict) -> None:
    """
    Build CLAUDE.md from prompt modules and combine with PROJECT.md.

    CLAUDE.md in the working folder = role instructions + '---' + PROJECT.md
    Both the native claude CLI and aicli read this as the system prompt,
    so Claude always has full project context from the start.
    """
    module = config.get("module")
    working_folder = config.get("working_folder")
    prompts_root = CLI_ROOT / config.get("prompts_root", "prompts")

    if not module:
        raise ValueError("'module' must be set in aicli.yaml")

    if config.get("rebuild_prompts_on_start", True):
        build_md(
            module_name=module,
            provider_name="claude",
            output_file=prompts_root / module / "CLAUDE.md",
        )

    if working_folder:
        working_path = Path(working_folder).resolve()
        if not working_path.exists():
            raise ValueError(f"working_folder not found: {working_path}")

        source = prompts_root / module / "CLAUDE.md"
        role_instructions = source.read_text(encoding="utf-8") if source.exists() else ""

        project_md_path = working_path / "PROJECT.md"
        if not project_md_path.exists():
            project_md_path.write_text(TEMPLATE, encoding="utf-8")

        project_content = project_md_path.read_text(encoding="utf-8").strip()

        combined = role_instructions.rstrip()
        if project_content:
            combined += "\n\n---\n\n# PROJECT KNOWLEDGE\n\n" + project_content

        (working_path / "CLAUDE.md").write_text(combined + "\n", encoding="utf-8")

        os.chdir(working_path)


# ======================================================================
# CONTEXT BUILDER (for interactive prompts)
# ======================================================================

def _build_claude_prompt(
    user_input: str,
    conversation: ConversationState,
    memory: MemoryStore,
    max_memory_chars: int = 3000,
    session_state: dict | None = None,
    memory_summary: str = "",
    aicli_context: str = "",
) -> str:
    """
    Build an augmented prompt for any provider (not just Claude).
    Injects: aicli context → session state → memory summary → project summary →
             current context → relevant memory → current request.
    """
    sections: list[str] = []

    # 0. aicli project context (from _system/aicli/context.md)
    if aicli_context:
        sections.append(f"[PROJECT CONTEXT]\n{aicli_context.strip()}")

    # 1. Previous session handoff (most prominent — tells the LLM where work stands)
    if session_state:
        state_block = format_session_state_for_prompt(session_state)
        if state_block:
            sections.append(state_block)

    # 2. Historical memory summary (accumulated summaries of old entries)
    if memory_summary:
        sections.append(f"[HISTORICAL CONTEXT]\n{memory_summary.strip()}")

    # 3. Current session project summary
    summary = conversation.data.get("project_summary", "")
    if summary:
        sections.append(f"PROJECT SUMMARY:\n{summary}")

    # 4. Active feature / tag context
    context_parts = []
    if conversation.get_feature():
        context_parts.append(f"Feature: {conversation.get_feature()}")
    if conversation.get_tag():
        context_parts.append(f"Tag: {conversation.get_tag()}")
    if context_parts:
        sections.append("CONTEXT: " + " | ".join(context_parts))

    # 5. Relevant memory entries (keyword-matched to this query)
    docs = memory.search(user_input)
    memory_block = "\n\n".join(docs)
    if len(memory_block) > max_memory_chars:
        memory_block = memory_block[:max_memory_chars]
    if memory_block:
        sections.append(f"RELEVANT PAST CONTEXT:\n{memory_block}")

    sections.append(f"CURRENT REQUEST:\n{user_input}")
    return "\n\n".join(sections)


# ======================================================================
# PROMPT COMPARISON
# ======================================================================

def _run_compare(
    prompt_file: str,
    provider_names: list[str],
    config: dict,
    logger,
) -> None:
    """
    Run the same prompt against multiple providers in parallel and show
    results side-by-side. User picks the winner; result logged to
    workspace/<project>/prompt_evals.jsonl.
    """
    prompt_path = Path(prompt_file)
    if not prompt_path.exists():
        # Try workspace-relative
        workspace_dir = Path(config.get("workspace_dir", CLI_ROOT / "workspace"))
        project_name = config.get("active_project", "")
        if project_name:
            prompt_path = workspace_dir / project_name / prompt_file
    if not prompt_path.exists():
        console.print(f"[red]Prompt file not found: {prompt_file}[/red]")
        return

    prompt_text = prompt_path.read_text(encoding="utf-8")
    console.print(f"\n[bold]Comparing prompt:[/bold] {prompt_path.name}")
    console.print(f"[dim]Providers: {', '.join(provider_names)}[/dim]\n")

    def _call_provider(name: str) -> tuple[str, str]:
        try:
            if name == "claude":
                agent = ClaudeAgent(config=config, logger=logger)
                output = agent.send(prompt_text)
                return name, output
            elif name == "openai":
                prov_cfg = config.get("providers", {}).get("openai", {})
                agent = OpenAIAgent(
                    model=prov_cfg.get("model", "gpt-4.1"),
                    api_key_env=prov_cfg.get("api_key_env", "OPENAI_API_KEY"),
                    logger=logger,
                )
                return name, agent.send("", prompt_text)
            elif name == "deepseek":
                from providers.deepseek_agent import DeepSeekAgent
                prov_cfg = config.get("providers", {}).get("deepseek", {})
                agent = DeepSeekAgent(
                    model=prov_cfg.get("model", "deepseek-chat"),
                    api_key_env=prov_cfg.get("api_key_env", "DEEPSEEK_API_KEY"),
                    logger=logger,
                )
                return name, agent.send(prompt_text)
            elif name == "gemini":
                from providers.gemini_agent import GeminiAgent
                prov_cfg = config.get("providers", {}).get("gemini", {})
                agent = GeminiAgent(
                    model=prov_cfg.get("model", "gemini-2.0-flash"),
                    api_key_env=prov_cfg.get("api_key_env", "GEMINI_API_KEY"),
                    logger=logger,
                )
                return name, agent.send(prompt_text)
            elif name == "grok":
                from providers.grok_agent import GrokAgent
                prov_cfg = config.get("providers", {}).get("grok", {})
                agent = GrokAgent(
                    model=prov_cfg.get("model", "grok-3"),
                    api_key_env=prov_cfg.get("api_key_env", "XAI_API_KEY"),
                    logger=logger,
                )
                return name, agent.send(prompt_text)
            else:
                return name, f"[unknown provider: {name}]"
        except Exception as e:
            return name, f"[error: {e}]"

    # Run in parallel
    outputs: dict[str, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(provider_names)) as executor:
        futures = {executor.submit(_call_provider, p): p for p in provider_names}
        for future in concurrent.futures.as_completed(futures):
            name, output = future.result()
            outputs[name] = output
            console.print(f"[dim]{name} ✓[/dim]")

    # Display side-by-side
    panels = []
    for i, name in enumerate(provider_names, 1):
        out = outputs.get(name, "(no output)")
        panels.append(Panel(
            Markdown(out[:1500]),
            title=f"[bold]{i}. {name.upper()}[/bold]",
            expand=True,
        ))
    console.print(Columns(panels))

    # Pick winner
    try:
        choice = console.input(
            f"\nPick winner (1-{len(provider_names)}, or Enter to skip): "
        ).strip()
    except (KeyboardInterrupt, EOFError):
        return

    winner = None
    notes = ""
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(provider_names):
            winner = provider_names[idx]
            try:
                notes = console.input("Notes (optional): ").strip()
            except (KeyboardInterrupt, EOFError):
                pass

    # Log result
    workspace_dir = Path(config.get("workspace_dir", CLI_ROOT / "workspace"))
    project_name = config.get("active_project", "")
    if project_name:
        log_dir = workspace_dir / project_name
        log_dir.mkdir(parents=True, exist_ok=True)
        evals_path = log_dir / "prompt_evals.jsonl"
        entry = {
            "ts": datetime.utcnow().isoformat(),
            "prompt_file": str(prompt_path),
            "providers": provider_names,
            "outputs": {k: v[:500] for k, v in outputs.items()},
            "winner": winner,
            "notes": notes,
        }
        with open(evals_path, "a", encoding="utf-8") as f:
            f.write(_json.dumps(entry) + "\n")
        console.print(f"[dim]Result logged to {evals_path}[/dim]")

    if winner:
        console.print(f"[green]Winner: {winner}[/green]")


# ======================================================================
# STARTUP PROJECT STATUS PANEL
# ======================================================================

def _show_project_status(project_md_path: Path, session_state: dict) -> None:
    """
    Parse PROJECT.md and display a concise status digest below the header panel.
    Shows: description, feature completion %, next TODO, previous session info.
    """
    lines_out: list[str] = []

    if project_md_path.exists():
        raw = project_md_path.read_text(encoding="utf-8")
        md_lines = raw.splitlines()

        # Extract description: first non-empty, non-heading paragraph
        description = ""
        for ln in md_lines:
            stripped = ln.strip()
            if stripped and not stripped.startswith("#"):
                description = stripped[:120]
                break

        # Count feature checkboxes: [x] done vs [ ] pending
        done = sum(1 for ln in md_lines if "- [x]" in ln or "- [X]" in ln)
        total = done + sum(1 for ln in md_lines if "- [ ]" in ln)
        pct = int(done / total * 100) if total else 0

        # Find first unchecked TODO
        next_todo = ""
        in_todo = False
        for ln in md_lines:
            if ln.strip().startswith("#") and "todo" in ln.lower():
                in_todo = True
                continue
            if in_todo and "- [ ]" in ln:
                next_todo = ln.strip().lstrip("-").lstrip("[ ]").strip()[:100]
                break
            if in_todo and ln.strip().startswith("#"):
                break

        if description:
            lines_out.append(f"[dim]{description}[/dim]")
        if total:
            bar_filled = int(pct / 10)
            bar = "█" * bar_filled + "░" * (10 - bar_filled)
            lines_out.append(
                f"  Features  [green]{bar}[/green] [bold]{pct}%[/bold] "
                f"[dim]({done}/{total} done)[/dim]"
            )
        if next_todo:
            lines_out.append(f"  Next      [yellow]→[/yellow] {next_todo}")

    # Previous session handoff
    if session_state:
        date_str = session_state.get("last_updated", "")[:10]
        prev_provider = session_state.get("active_provider", "")
        feature = session_state.get("feature", "")
        last_q = session_state.get("last_input_preview", "")[:70]
        sess_n = session_state.get("session_count", "")

        parts = []
        if date_str:
            parts.append(date_str)
        if prev_provider:
            parts.append(f"provider={prev_provider}")
        if feature:
            parts.append(f"feature={feature}")
        if sess_n:
            parts.append(f"session #{sess_n}")
        if parts:
            lines_out.append(f"  Last session  [dim]{' · '.join(parts)}[/dim]")
        if last_q:
            lines_out.append(f"  Last prompt   [italic dim]\"{last_q}\"[/italic dim]")

    if lines_out:
        console.print(Panel(
            "\n".join(lines_out),
            title="[bold]Project Status[/bold]",
            border_style="dim",
            expand=False,
        ))


# ======================================================================
# HELP
# ======================================================================

HELP_MD = """
## aicli commands

| Command | Description |
|---|---|
| `/switch <provider>` | Switch LLM provider (claude, openai, deepseek, gemini, grok) |
| `/workflow [name]` | List workflows or run named one |
| `/project new <name> [--template t]` | Create project from template |
| `/project list` | List all projects with hyperlinks |
| `/project switch <name>` | Switch active project |
| `/compare <prompt.md> [--providers p1,p2]` | Run prompt on multiple LLMs, pick winner |
| `/branch <name>` | Switch or create a git branch |
| `/feature <name>` | Set current feature context |
| `/tag <name>` | Set current tag |
| `/tags` | List all tags with entry counts |
| `/search-tag <tag>` | Search memory entries by tag |
| `/docs` | Show current PROJECT.md |
| `/docs generate` | Regenerate PROJECT.md (OpenAI) |
| `/docs todo <item>` | Append a TODO item |
| `/docs done <fragment>` | Mark a TODO item as done |
| `/push` | Summarise + commit + push |
| `/deploy <aws\\|railway>` | Deploy stub |
| `/status` | Show mode, history size, git status |
| `/history` | Show last 20 commits |
| `/analytics` | Project usage analytics |
| `/memory` | Refresh CLAUDE.md + CONTEXT.md → copy to code directory |
| `/reload` | Rebuild prompts and reload system prompt |
| `/clear` | Clear Claude conversation history |
| `/qa` | Run test suite |
| `/help` | Show this help |
| `/exit` | Exit |

**Legacy aliases**: `/claude` → `/switch claude`, `/openai <role>` → role-based OpenAI mode
"""


# ======================================================================
# MAIN
# ======================================================================

def main():
    load_environment(CLI_ROOT / ".env")
    config = load_config()
    initialize_project(config)

    # Compute CLI data dir: workspace/{project}/_system/aicli/
    # Falls back to .aicli/ if workspace or project not set (e.g. first run).
    workspace_dir_early = Path(config.get("workspace_dir", CLI_ROOT / "workspace"))
    active_project_early = config.get("active_project", "")
    if active_project_early and (workspace_dir_early / active_project_early / "_system").exists():
        _cli_data_dir = str(workspace_dir_early / active_project_early / "_system" / "aicli")
    else:
        _cli_data_dir = config.get("cli_data_dir", str(CLI_ROOT / ".aicli"))

    # Inject derived paths into config so sub-modules (logger, memory, etc.) pick them up
    config["cli_data_dir"] = _cli_data_dir
    config.setdefault("log_path", str(Path(_cli_data_dir) / "logs.jsonl"))

    # Ensure the data dir exists before any module tries to write to it
    Path(_cli_data_dir).mkdir(parents=True, exist_ok=True)

    logger = StructuredLogger(config)
    conversation = ConversationState(
        max_history=config.get("max_history", 200),
        path=str(Path(_cli_data_dir) / "current_session.json"),
        cli_data_dir=_cli_data_dir,
    )
    hook_runner = HookRunner(config, logger=logger)
    git_supervisor = GitSupervisor(config, logger=logger, hook_runner=hook_runner)

    claude = ClaudeAgent(config=config, logger=logger)
    openai = OpenAIAgent(
        model=config["providers"]["openai"]["model"],
        api_key_env=config["providers"]["openai"]["api_key_env"],
        logger=logger,
    )
    memory = MemoryStore(config, logger=logger)

    # Session persistence and handoff state — stored inside _cli_data_dir
    working_dir = Path.cwd()
    session_store = SessionStore(working_dir, cli_data_dir=_cli_data_dir)
    session_state = load_session_state(working_dir, cli_data_dir=_cli_data_dir)
    memory_summary = memory.load_summary()

    # Collect startup notices quietly — display them AFTER the panel
    _startup_notices: list[str] = []

    # Restore conversation history for Claude and OpenAI from previous session
    saved_claude = session_store.load_messages("claude")
    if saved_claude:
        claude.messages = saved_claude
        _startup_notices.append(f"Restored {len(saved_claude) // 2} Claude turns")

    saved_openai = session_store.load_messages("openai")
    if saved_openai:
        openai.messages = saved_openai
        _startup_notices.append(f"Restored {len(saved_openai) // 2} OpenAI turns")

    # Compact memory if it's grown large (uses OpenAI cheaply)
    compact_threshold = config.get("memory_compact_threshold", 200)
    if memory.count() > compact_threshold:
        try:
            compacted = memory.maybe_compact(openai, threshold=compact_threshold, keep_recent=50)
            if compacted:
                memory_summary = memory.load_summary()
                _startup_notices.append("Memory compacted → .aicli/memory_summary.md")
        except Exception as e:
            logger.warning("memory_compact_failed", error=str(e))

    # Cache for non-Claude providers — instantiated once per session, not per message
    _provider_cache: dict = {}

    # Rolling turn counter for session_state
    _session_turn_count = session_state.get("session_count", 0)
    docs = ProjectDocs(Path.cwd(), openai)

    # Workspace + project tracking
    workspace_dir = Path(config.get("workspace_dir", CLI_ROOT / "workspace"))
    active_project = config.get("active_project", "")

    def _load_aicli_context() -> str:
        """Read _system/aicli/context.md for the active project, prepend project_facts."""
        if not active_project:
            return ""

        # Prepend project facts from backend (best-effort, timeout=2s)
        facts_block = ""
        try:
            import urllib.request as _urlreq
            import json as _json
            _bu = config.get("backend_url", "http://localhost:8000")
            _req = _urlreq.Request(
                f"{_bu}/work-items/facts?project={active_project}",
                headers={"Accept": "application/json"},
            )
            with _urlreq.urlopen(_req, timeout=2) as _resp:
                _data = _json.loads(_resp.read())
            facts = _data.get("facts", [])
            if facts:
                facts_block = "[Project Facts]\n" + "\n".join(
                    f"{f['fact_key']}: {f['fact_value']}" for f in facts
                ) + "\n\n"
        except Exception:
            pass

        ctx_file = workspace_dir / active_project / "_system" / "aicli" / "context.md"
        if ctx_file.exists():
            try:
                ctx_text = ctx_file.read_text(encoding="utf-8").strip()
                return facts_block + ctx_text if facts_block else ctx_text
            except Exception:
                pass
        return facts_block.strip()

    aicli_context = _load_aicli_context()

    def _warn_if_memory_stale() -> None:
        """Print a one-time yellow warning if too many prompts have accumulated since last /memory."""
        if not active_project:
            return
        proj_dir = workspace_dir / active_project
        sys_dir  = proj_dir / "_system"

        # Load last_memory_run from project_state.json
        last_memory_run: str | None = None
        for sp in [sys_dir / "project_state.json", proj_dir / "project_state.json"]:
            if sp.exists():
                try:
                    import json as _json
                    sd = _json.loads(sp.read_text())
                    last_memory_run = sd.get("last_memory_run")
                    threshold = int(sd.get("_memory_threshold", 20))
                    break
                except Exception:
                    pass
        else:
            threshold = 20

        # Load threshold from project.yaml if not in state
        yaml_path = proj_dir / "project.yaml"
        if yaml_path.exists():
            try:
                import yaml as _yaml
                cfg = _yaml.safe_load(yaml_path.read_text()) or {}
                threshold = int(cfg.get("memory_threshold", threshold))
            except Exception:
                pass

        # Count prompts since last_memory_run
        hist = sys_dir / "history.jsonl"
        if not hist.exists():
            return
        count = 0
        try:
            import json as _json
            for line in hist.read_text().splitlines():
                if not line.strip():
                    continue
                try:
                    e = _json.loads(line)
                except Exception:
                    continue
                if not e.get("user_input"):
                    continue
                ts = e.get("ts") or ""
                if last_memory_run is None or ts > last_memory_run:
                    count += 1
        except Exception:
            return

        if count < threshold:
            return

        date_str = (last_memory_run or "never")[:10]
        console.print(
            f"\n[yellow]⚠  {count} new prompts since last /memory ({date_str}).[/yellow]"
            "\n[dim]   Run [bold]/memory[/bold] to refresh AI context files.[/dim]\n"
        )

    # Show warning once at startup (not blocking)
    try:
        _warn_if_memory_stale()
    except Exception:
        pass

    def _make_runner() -> WorkflowRunner | None:
        if not active_project:
            return None
        return WorkflowRunner(
            config=config,
            workspace_root=workspace_dir,
            project_name=active_project,
            logger=logger,
        )

    # ------------------------------------------------------------------
    # Prompt log
    # ------------------------------------------------------------------
    _prompt_log = Path(".aicli/prompt_log.jsonl")

    def _log_prompt(provider: str, role: str | None, user_input: str, output: str) -> None:
        from datetime import timezone
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": "aicli",
            "provider": provider,
            "role": role or "",
            "user_input": user_input,
            "output_preview": output[:300],
        }
        with open(_prompt_log, "a", encoding="utf-8") as _f:
            _f.write(_json.dumps(entry) + "\n")

    current_mode: str = config.get("providers", {}).get("default", "claude")
    current_openai_role: str | None = None
    prompts_root = CLI_ROOT / config.get("prompts_root", "prompts")
    module = config.get("module", "")

    history = conversation.data.get("conversation", [])
    if history:
        summary = build_project_summary(history)
        claude.send(f"[Session context restored:]\n{summary}")
        _startup_notices.append("Previous session context loaded")

    # ------------------------------------------------------------------
    # Clear screen and render startup panels
    # ------------------------------------------------------------------
    console.clear()
    branch = get_current_branch()

    console.print(Panel(
        f"[bold cyan]aicli[/bold cyan]  "
        f"branch=[cyan]{branch or 'none'}[/cyan]  "
        f"mode=[green]{current_mode.upper()}[/green]  "
        f"memory=[yellow]{memory.count()} entries[/yellow]"
        + (f"  project=[magenta]{active_project}[/magenta]" if active_project else "")
        + "\n[dim]Type /help for commands[/dim]",
        expand=False,
    ))

    # Project status panel — read PROJECT.md and show a digest
    _project_md_path = Path.cwd() / "PROJECT.md"
    if not _project_md_path.exists() and active_project:
        _project_md_path = workspace_dir / active_project / "PROJECT.md"
    _show_project_status(_project_md_path, session_state)

    # Startup notices (session restore, compaction) — one compact line
    if _startup_notices:
        console.print("[dim]  › " + "  ·  ".join(_startup_notices) + "[/dim]")
    console.print()

    os.makedirs(".aicli", exist_ok=True)
    pt_session: PromptSession = PromptSession(
        history=FileHistory(".aicli/prompt_history"),
        auto_suggest=AutoSuggestFromHistory(),
        completer=WordCompleter(SLASH_COMMANDS, sentence=True),
    )

    def get_prompt_text() -> str:
        proj = f"[{active_project}]" if active_project else ""
        if current_mode == "claude":
            return f"(CLAUDE){proj}> "
        if current_mode == "openai" and current_openai_role:
            return f"(OPENAI:{current_openai_role}){proj}> "
        return f"({current_mode.upper()}){proj}> "

    # ==================================================================
    # MAIN LOOP
    # ==================================================================

    while True:
        try:
            user_input = pt_session.prompt(get_prompt_text()).strip()
        except KeyboardInterrupt:
            console.print("\n[dim]Ctrl+C — type /exit to quit.[/dim]")
            continue
        except EOFError:
            break

        if not user_input:
            continue

        logger.debug("cli_input", input=user_input[:200])

        # ----------------------------------------------------------
        # /exit
        # ----------------------------------------------------------
        if user_input == "/exit":
            break

        # ----------------------------------------------------------
        # /help
        # ----------------------------------------------------------
        if user_input == "/help":
            console.print(Markdown(HELP_MD))
            continue

        # ----------------------------------------------------------
        # /clear
        # ----------------------------------------------------------
        if user_input == "/clear":
            claude.clear_history()
            openai.clear_history()
            for p in _provider_cache.values():
                if hasattr(p, "clear_history"):
                    p.clear_history()
            session_store.clear()         # delete all saved message histories
            session_state = {}            # reset handoff state in memory
            console.print("[dim]Conversation history cleared for all providers (session files deleted).[/dim]")
            continue

        # ----------------------------------------------------------
        # /memory  — generate per-LLM memory files, copy to code dir
        # ----------------------------------------------------------
        if user_input == "/memory":
            if not active_project:
                console.print("[yellow]No active project. Use /project switch <name> first.[/yellow]")
                continue
            backend_url = config.get("backend_url", "http://localhost:8000")
            refreshed = False
            try:
                import urllib.request as _urlreq
                import urllib.error as _urlerr
                req = _urlreq.Request(
                    f"{backend_url}/projects/{active_project}/memory",
                    data=b"{}",
                    method="POST",
                    headers={"Content-Type": "application/json"},
                )
                with _urlreq.urlopen(req, timeout=30) as _resp:
                    _data = _json.loads(_resp.read())
                generated = _data.get("generated", [])
                copied = _data.get("copied_to", [])
                if generated:
                    console.print(f"[green]✓ Generated: {', '.join(generated)}[/green]")
                if copied:
                    console.print(f"[green]✓ Copied to: {', '.join(copied)}[/green]")
                claude.reload_system_prompt()
                aicli_context = _load_aicli_context()
                refreshed = True
            except Exception:
                pass
            if not refreshed:
                # Backend offline — copy existing _system/claude/CLAUDE.md to code_dir directly
                sys_dir = workspace_dir / active_project / "_system"
                sys_claude = sys_dir / "claude" / "CLAUDE.md"
                if not sys_claude.exists():
                    sys_claude = sys_dir / "CLAUDE.md"  # legacy fallback
                if sys_claude.exists():
                    try:
                        import yaml as _yaml
                        proj_yaml = workspace_dir / active_project / "project.yaml"
                        proj_cfg = _yaml.safe_load(proj_yaml.read_text()) if proj_yaml.exists() else {}
                        code_dir_str = proj_cfg.get("code_dir", "")
                        if code_dir_str:
                            code_p = Path(code_dir_str) if Path(code_dir_str).is_absolute() \
                                else (workspace_dir / active_project / code_dir_str).resolve()
                            if code_p.exists():
                                (code_p / "CLAUDE.md").write_text(sys_claude.read_text())
                                console.print(f"[green]✓ CLAUDE.md copied from _system/ to {code_p}[/green]")
                                refreshed = True
                    except Exception as _ce:
                        console.print(f"[yellow]Could not copy CLAUDE.md: {_ce}[/yellow]")
                if not refreshed:
                    console.print("[yellow]Backend offline — start it and run /memory to regenerate context.[/yellow]")
            continue

        # ----------------------------------------------------------
        # /reload
        # ----------------------------------------------------------
        if user_input == "/reload":
            initialize_project(config)
            claude.reload_system_prompt()
            console.print("[green]Prompts rebuilt and system prompt reloaded.[/green]")
            continue

        # ----------------------------------------------------------
        # /switch <provider>
        # ----------------------------------------------------------
        if user_input.startswith("/switch"):
            parts = user_input.split(None, 1)
            if len(parts) < 2:
                console.print(f"[red]Usage: /switch <provider>  (options: {', '.join(PROVIDER_NAMES)})[/red]")
                continue
            name = parts[1].strip().lower()
            if name not in PROVIDER_NAMES:
                console.print(f"[red]Unknown provider: {name}. Options: {', '.join(PROVIDER_NAMES)}[/red]")
                continue
            current_mode = name
            console.print(f"[green]Switched to {name.upper()}[/green]")
            continue

        # ----------------------------------------------------------
        # /claude (legacy alias)
        # ----------------------------------------------------------
        if user_input == "/claude":
            current_mode = "claude"
            console.print("[green]Switched to CLAUDE[/green]")
            continue

        # ----------------------------------------------------------
        # /openai <role> (legacy alias — role-based)
        # ----------------------------------------------------------
        if user_input.startswith("/openai"):
            parts = user_input.split(None, 1)
            if len(parts) < 2:
                console.print("[red]Usage: /openai <role_name>[/red]")
                continue
            current_mode = "openai"
            current_openai_role = parts[1].strip()
            console.print(f"[green]Switched to OPENAI role: {current_openai_role}[/green]")
            continue

        # ----------------------------------------------------------
        # /project new <name> [--template <t>]  |  list  |  switch <name>
        # ----------------------------------------------------------
        if user_input.startswith("/project"):
            parts = user_input.split(None, 3)
            sub = parts[1] if len(parts) > 1 else ""

            if not sub or sub == "list":
                # List projects
                if not workspace_dir.exists():
                    console.print("[dim]No workspace directory found.[/dim]")
                else:
                    projects = [
                        d.name for d in sorted(workspace_dir.iterdir())
                        if d.is_dir() and not d.name.startswith("_")
                    ]
                    if not projects:
                        console.print("[dim]No projects yet. Use /project new <name>[/dim]")
                    else:
                        console.print("[bold]Projects:[/bold]")
                        for p in projects:
                            marker = " ← active" if p == active_project else ""
                            proj_dir = workspace_dir / p
                            link = _hyperlink(p, proj_dir.as_uri())
                            console.print(f"  {link}{marker}")

            elif sub == "new":
                if len(parts) < 3:
                    console.print("[red]Usage: /project new <name> [--template blank|python_api|quant_notebook|ui_app][/red]")
                    continue
                new_name = parts[2]
                template = "blank"
                if "--template" in user_input:
                    t_parts = user_input.split("--template", 1)
                    template = t_parts[1].strip().split()[0] if t_parts[1].strip() else "blank"

                template_dir = workspace_dir / "_templates" / template
                if not template_dir.exists():
                    console.print(f"[red]Template not found: {template}[/red]")
                    continue

                dest_dir = workspace_dir / new_name
                if dest_dir.exists():
                    console.print(f"[red]Project already exists: {new_name}[/red]")
                    continue

                shutil.copytree(template_dir, dest_dir)

                # Replace template vars in project.yaml
                proj_yaml = dest_dir / "project.yaml"
                if proj_yaml.exists():
                    content = proj_yaml.read_text()
                    content = content.replace("{{PROJECT_NAME}}", new_name)
                    content = content.replace("{{DATE}}", datetime.utcnow().strftime("%Y-%m-%d"))
                    proj_yaml.write_text(content)

                # Replace in PROJECT.md
                proj_md = dest_dir / "PROJECT.md"
                if proj_md.exists():
                    content = proj_md.read_text()
                    content = content.replace("{{PROJECT_NAME}}", new_name)
                    content = content.replace("{{DATE}}", datetime.utcnow().strftime("%Y-%m-%d"))
                    proj_md.write_text(content)

                console.print(f"[green]Project created: {new_name} (from {template} template)[/green]")
                console.print(f"[dim]{dest_dir}[/dim]")

                # Auto-switch
                active_project = new_name
                config["active_project"] = new_name
                console.print(f"[green]Switched to project: {new_name}[/green]")

            elif sub == "switch":
                if len(parts) < 3:
                    console.print("[red]Usage: /project switch <name>[/red]")
                    continue
                new_name = parts[2]
                if not (workspace_dir / new_name).exists():
                    console.print(f"[red]Project not found: {new_name}[/red]")
                    continue
                active_project = new_name
                config["active_project"] = new_name
                console.print(f"[green]Switched to project: {new_name}[/green]")

            else:
                console.print("[red]Usage: /project [list | new <name> | switch <name>][/red]")
            continue

        # ----------------------------------------------------------
        # /compare <prompt.md> [--providers p1,p2,p3]
        # ----------------------------------------------------------
        if user_input.startswith("/compare"):
            parts = user_input.split()
            if len(parts) < 2:
                console.print("[red]Usage: /compare <prompt.md> [--providers claude,deepseek,openai][/red]")
                continue
            prompt_file = parts[1]
            providers = ["claude", "deepseek"]  # default
            if "--providers" in user_input:
                idx = parts.index("--providers") if "--providers" in parts else -1
                if idx >= 0 and idx + 1 < len(parts):
                    providers = parts[idx + 1].split(",")
            _run_compare(prompt_file, providers, config, logger)
            continue

        # ----------------------------------------------------------
        # /workflow [name]
        # ----------------------------------------------------------
        if user_input.startswith("/workflow"):
            parts = user_input.split(None, 1)
            runner = _make_runner()

            if len(parts) < 2:
                # List available workflows
                if runner:
                    wf_list = runner.list_workflows()
                    if wf_list:
                        console.print("[bold]Workflows:[/bold]")
                        for wf in wf_list:
                            wf_dir = workspace_dir / active_project / "workflows" / wf
                            link = _hyperlink(wf, wf_dir.as_uri())
                            console.print(f"  {link}")
                    else:
                        console.print("[dim]No workflows found in project workspace.[/dim]")
                else:
                    console.print("[yellow]No active project. Use /project switch <name> first.[/yellow]")
                continue

            wf_name = parts[1].strip()

            # Legacy: check aicli.yaml workflows
            old_workflows = config.get("workflows", {})
            if wf_name in old_workflows and not runner:
                console.print(f"[yellow]Running legacy workflow: {wf_name}[/yellow]")
                from workflows.engine import WorkflowEngine
                initial = pt_session.prompt("Workflow prompt: ").strip()
                engine = WorkflowEngine(
                    claude_agent=claude,
                    openai_agent=openai,
                    conversation=conversation,
                    git_supervisor=git_supervisor,
                )
                engine.run(old_workflows[wf_name], initial)
                continue

            if not runner:
                console.print("[yellow]No active project. Use /project switch <name> first.[/yellow]")
                continue

            try:
                initial = pt_session.prompt("Workflow input (Enter to skip): ").strip()
                runner.run(wf_name, initial)
            except FileNotFoundError as e:
                console.print(f"[red]{e}[/red]")
                wf_list = runner.list_workflows()
                if wf_list:
                    console.print(f"Available: {', '.join(wf_list)}")
            continue

        # ----------------------------------------------------------
        # /branch <name>
        # ----------------------------------------------------------
        if user_input.startswith("/branch"):
            parts = user_input.split(None, 1)
            if len(parts) < 2:
                console.print("[red]Usage: /branch <branch_name>[/red]")
                continue
            checkout_branch(parts[1].strip())
            console.print(f"[green]Branch: {parts[1].strip()}[/green]")
            continue

        # ----------------------------------------------------------
        # /feature <name>
        # ----------------------------------------------------------
        if user_input.startswith("/feature"):
            parts = user_input.split(None, 1)
            if len(parts) < 2:
                console.print("[red]Usage: /feature <name>[/red]")
                continue
            conversation.set_feature(parts[1].strip())
            console.print(f"[cyan]Feature: {parts[1].strip()}[/cyan]")
            continue

        # ----------------------------------------------------------
        # /tag <name>
        # ----------------------------------------------------------
        if user_input.startswith("/tag "):
            tag_name = user_input[5:].strip()
            conversation.set_tag(tag_name)
            console.print(f"[cyan]Tag: #{tag_name}[/cyan]")
            continue

        # ----------------------------------------------------------
        # /tags
        # ----------------------------------------------------------
        if user_input == "/tags":
            tags = conversation.list_tags()
            if not tags:
                console.print("[dim]No tags yet.[/dim]")
            else:
                rows = "\n".join(
                    f"  [cyan]#{t}[/cyan]  {c} entries"
                    for t, c in sorted(tags.items(), key=lambda x: -x[1])
                )
                console.print(f"Tags:\n{rows}")
            continue

        # ----------------------------------------------------------
        # /search-tag <tag>
        # ----------------------------------------------------------
        if user_input.startswith("/search-tag"):
            parts = user_input.split(None, 1)
            if len(parts) < 2:
                console.print("[red]Usage: /search-tag <tag>[/red]")
                continue
            tag_query = parts[1].strip()
            found_docs = memory.search_by_tag(tag_query)
            conv_entries = conversation.get_entries_by_tag(tag_query)
            if not found_docs and not conv_entries:
                console.print(f"[dim]No entries for #{tag_query}[/dim]")
            else:
                console.print(f"\n[bold]Memory entries for #{tag_query}:[/bold]")
                for d in found_docs:
                    console.print(Panel(d[:400], expand=False))
                if conv_entries:
                    console.print(f"\n[bold]Conversation entries:[/bold]")
                    for e in conv_entries:
                        ts = e["timestamp"][:10]
                        console.print(f"  [{ts}] {e['provider']}: {e['user_input'][:80]}")
            continue

        # ----------------------------------------------------------
        # /status
        # ----------------------------------------------------------
        if user_input == "/status":
            console.print(
                f"Mode:    [green]{current_mode}[/green]\n"
                f"Project: [magenta]{active_project or '(none)'}[/magenta]\n"
                f"Feature: [cyan]{conversation.get_feature() or '(none)'}[/cyan]\n"
                f"Tag:     [cyan]{conversation.get_tag() or '(none)'}[/cyan]\n"
                f"Branch:  [yellow]{get_current_branch()}[/yellow]\n"
                f"History: {len(conversation.data['conversation'])} turns\n"
                f"Commits: {len(conversation.data['commits'])}\n"
                f"Memory:  {memory.count()} entries\n"
                f"Changes: {git_supervisor.get_change_stats() or 'none'}"
            )
            continue

        # ----------------------------------------------------------
        # /history
        # ----------------------------------------------------------
        if user_input == "/history":
            commits = conversation.data.get("commits", [])
            if not commits:
                console.print("[dim]No commits recorded.[/dim]")
            else:
                console.print(f"[bold]{'Hash':10} {'Feature':15} {'Tag':10} Message[/bold]")
                console.print("─" * 70)
                for c in commits[-20:]:
                    h = (c.get("commit_hash") or "")[:8]
                    f = (c.get("feature") or "-")[:15]
                    t = (c.get("tag") or "-")[:10]
                    m = (c.get("commit_message") or "")[:40]
                    console.print(f"{h:10} {f:15} {t:10} {m}")
            continue

        # ----------------------------------------------------------
        # /push
        # ----------------------------------------------------------
        if user_input == "/push":
            try:
                snippets = memory.recent(top_k=20)
                summary_text = generate_system_summary(openai, conversation.data.get("commits", []))
                if summary_text:
                    conversation.update_summary(summary_text)
                git_supervisor.handle_commit(summary_text or "push", openai, context={
                    "provider": current_mode,
                    "feature": conversation.get_feature() or "",
                    "tag": conversation.get_tag() or "",
                })
                console.print("[green]Summarised, committed, and pushed.[/green]")
            except Exception as e:
                console.print(f"[red]Push failed: {e}[/red]")
            continue

        # ----------------------------------------------------------
        # /deploy <aws|railway>
        # ----------------------------------------------------------
        if user_input.startswith("/deploy"):
            parts = user_input.split(None, 1)
            target = parts[1].strip() if len(parts) > 1 else ""
            if target == "aws":
                script = CLI_ROOT / ".aicli/scripts/deploy_aws.sh"
                if script.exists():
                    os.system(f"bash {script}")
                else:
                    console.print("[yellow]deploy_aws.sh not found — stub only.[/yellow]")
            elif target == "railway":
                console.print("[yellow]Railway deploy not yet implemented.[/yellow]")
            else:
                console.print("[red]Usage: /deploy <aws|railway>[/red]")
            continue

        # ----------------------------------------------------------
        # /qa
        # ----------------------------------------------------------
        if user_input == "/qa":
            git_supervisor.run_tests()
            continue

        # ----------------------------------------------------------
        # /docs  |  /docs generate  |  /docs todo <item>  |  /docs done <fragment>
        # ----------------------------------------------------------
        if user_input.startswith("/docs"):
            parts = user_input.split(None, 2)
            sub = parts[1] if len(parts) > 1 else ""

            if not sub:
                content = docs.read()
                if not content:
                    console.print("[dim]PROJECT.md is empty. Run /docs generate to create it.[/dim]")
                else:
                    console.print(Markdown(content))

            elif sub == "generate":
                console.print("[dim]Generating PROJECT.md with OpenAI...[/dim]")
                try:
                    snippets = memory.recent(top_k=20)
                    new_doc = docs.generate(snippets)
                    initialize_project(config)
                    claude.reload_system_prompt()
                    console.print("[green]PROJECT.md updated — CLAUDE.md rebuilt.[/green]\n")
                    console.print(Markdown(new_doc))
                except Exception as e:
                    console.print(f"[red]Docs generation failed: {e}[/red]")

            elif sub == "todo":
                item = parts[2].strip() if len(parts) > 2 else ""
                if not item:
                    console.print("[red]Usage: /docs todo <item text>[/red]")
                else:
                    docs.add_todo(item)
                    initialize_project(config)
                    console.print(f"[green]TODO added: {item}[/green]")

            elif sub == "done":
                fragment = parts[2].strip() if len(parts) > 2 else ""
                if not fragment:
                    console.print("[red]Usage: /docs done <fragment of todo text>[/red]")
                elif docs.mark_done(fragment):
                    initialize_project(config)
                    console.print(f"[green]Marked done: {fragment}[/green]")
                else:
                    console.print(f"[yellow]No unchecked TODO found matching: {fragment}[/yellow]")

            else:
                console.print("[red]Usage: /docs  |  /docs generate  |  /docs todo <item>  |  /docs done <fragment>[/red]")

            continue

        # ----------------------------------------------------------
        # /analytics
        # ----------------------------------------------------------
        if user_input == "/analytics":
            a = ProjectAnalytics(conversation)
            console.print(
                f"\n[bold]PROJECT ANALYTICS[/bold]\n"
                f"Prompts:       {a.total_prompts()}\n"
                f"Commits:       {a.total_commits()}\n"
                f"Files changed: {a.total_files_changed()}\n"
                f"Session hours: {a.session_duration_hours():.2f}\n"
                f"Est. cost:     ${a.estimate_cost():.4f}"
            )
            by_feature = a.commits_by_feature()
            if by_feature:
                console.print("\n[bold]By feature:[/bold]")
                for feat, cnt in by_feature.items():
                    console.print(f"  {feat}: {cnt}")
            by_tag = a.commits_by_tag()
            if by_tag:
                console.print("\n[bold]By tag:[/bold]")
                for tag, cnt in by_tag.items():
                    console.print(f"  #{tag}: {cnt}")

            # Show workflow cost summary if available
            if active_project:
                costs_path = workspace_dir / active_project / ".aicli" / "workflow_costs.jsonl"
                if costs_path.exists():
                    total_wf_cost = 0.0
                    with open(costs_path) as f:
                        for line in f:
                            try:
                                total_wf_cost += _json.loads(line).get("total_cost_usd", 0)
                            except Exception:
                                pass
                    console.print(f"\n[bold]Workflow cost total:[/bold] ${total_wf_cost:.5f}")
            continue

        # ----------------------------------------------------------
        # Periodic summary
        # ----------------------------------------------------------
        commits = conversation.data.get("commits", [])
        if len(commits) > 0 and len(commits) % 5 == 0:
            try:
                summary_text = generate_system_summary(openai, commits)
                if summary_text:
                    conversation.update_summary(summary_text)
            except Exception as e:
                logger.warning("summary_failed", error=str(e))

        hook_ctx = {
            "provider": current_mode,
            "role": current_openai_role or "",
            "user_input": user_input,
            "feature": conversation.get_feature() or "",
            "tag": conversation.get_tag() or "",
            "branch": get_current_branch(),
        }

        hook_runner.run("pre_prompt", hook_ctx)

        # ==============================================================
        # CLAUDE MODE
        # ==============================================================
        if current_mode == "claude":
            augmented = _build_claude_prompt(
                user_input, conversation, memory,
                session_state=session_state,
                memory_summary=memory_summary,
                aicli_context=aicli_context,
            )

            try:
                output = claude.send(augmented)
            except Exception as e:
                console.print(f"[red][Claude error] {e}[/red]")
                logger.error("claude_error", error=str(e))
                continue

            _log_prompt("claude", None, user_input, output)
            hook_runner.run("post_prompt", {**hook_ctx, "output": output})

            commit_data = None
            try:
                commit_data = git_supervisor.handle_commit(output, openai, context=hook_ctx)
            except Exception as e:
                logger.warning("commit_error", error=str(e))

            conversation.append(
                provider="claude", role=None,
                user_input=user_input, output=output, commit=commit_data,
            )
            memory.add_entry(
                provider="claude", role=None,
                user_input=user_input, output=output,
                commit_data=commit_data,
                feature=conversation.get_feature(),
                tag=conversation.get_tag(),
            )

            # Persist Claude's conversation history and update handoff state
            _session_turn_count += 1
            session_store.save_messages("claude", claude.messages)
            save_session_state(
                working_dir, "claude", active_project,
                conversation.get_feature() or "", conversation.get_tag() or "",
                user_input, output, _session_turn_count, cli_data_dir=_cli_data_dir,
            )
            session_state = load_session_state(working_dir, cli_data_dir=_cli_data_dir)  # keep in sync

        # ==============================================================
        # OPENAI MODE (legacy role-based)
        # ==============================================================
        elif current_mode == "openai":
            if not current_openai_role:
                console.print("[red]Use /openai <role> or /switch openai first.[/red]")
                continue

            try:
                role_prompt = load_openai_role(prompts_root, module, current_openai_role)
            except ValueError as e:
                console.print(f"[red]{e}[/red]")
                continue

            system_prompt = load_openai_system(prompts_root, module)

            sections: list[str] = [role_prompt]
            proj_summary = conversation.data.get("project_summary", "")
            if proj_summary:
                sections.append(f"PROJECT SUMMARY:\n{proj_summary}")
            mem_docs = memory.search(user_input)
            if mem_docs:
                sections.append("RELEVANT PAST CONTEXT:\n" + "\n\n".join(mem_docs)[:3000])
            sections.append(f"CURRENT REQUEST:\n{user_input}")

            try:
                output = openai.send(system_prompt, "\n\n".join(sections))
            except Exception as e:
                console.print(f"[red][OpenAI error] {e}[/red]")
                logger.error("openai_error", error=str(e))
                continue

            console.print(Markdown(output))
            _log_prompt("openai", current_openai_role, user_input, output)
            hook_runner.run("post_prompt", {**hook_ctx, "output": output})

            commit_data = None
            try:
                commit_data = git_supervisor.handle_commit(output, openai, context=hook_ctx)
            except Exception as e:
                logger.warning("commit_error", error=str(e))

            conversation.append(
                provider="openai", role=current_openai_role,
                user_input=user_input, output=output, commit=commit_data,
            )
            memory.add_entry(
                provider="openai", role=current_openai_role,
                user_input=user_input, output=output,
                commit_data=commit_data,
                feature=conversation.get_feature(),
                tag=conversation.get_tag(),
            )

            _session_turn_count += 1
            session_store.save_messages("openai", openai.messages)
            save_session_state(
                working_dir, "openai", active_project,
                conversation.get_feature() or "", conversation.get_tag() or "",
                user_input, output, _session_turn_count, cli_data_dir=_cli_data_dir,
            )
            session_state = load_session_state(working_dir, cli_data_dir=_cli_data_dir)

        # ==============================================================
        # OTHER PROVIDERS (openai-role-free, deepseek, gemini, grok)
        # ==============================================================
        else:
            try:
                # Instantiate once per session; reuse for conversation history
                if current_mode not in _provider_cache:
                    if current_mode == "deepseek":
                        from providers.deepseek_agent import DeepSeekAgent
                        prov_cfg = config.get("providers", {}).get("deepseek", {})
                        _provider_cache[current_mode] = DeepSeekAgent(
                            model=prov_cfg.get("model", "deepseek-chat"),
                            api_key_env=prov_cfg.get("api_key_env", "DEEPSEEK_API_KEY"),
                            logger=logger,
                        )
                    elif current_mode == "gemini":
                        from providers.gemini_agent import GeminiAgent
                        prov_cfg = config.get("providers", {}).get("gemini", {})
                        _provider_cache[current_mode] = GeminiAgent(
                            model=prov_cfg.get("model", "gemini-2.0-flash"),
                            api_key_env=prov_cfg.get("api_key_env", "GEMINI_API_KEY"),
                            logger=logger,
                        )
                    elif current_mode == "grok":
                        from providers.grok_agent import GrokAgent
                        prov_cfg = config.get("providers", {}).get("grok", {})
                        _provider_cache[current_mode] = GrokAgent(
                            model=prov_cfg.get("model", "grok-3"),
                            api_key_env=prov_cfg.get("api_key_env", "XAI_API_KEY"),
                            logger=logger,
                        )
                    else:
                        console.print(f"[red]Unknown mode: {current_mode}[/red]")
                        continue

                    # Restore saved history for this provider (first time only)
                    saved = session_store.load_messages(current_mode)
                    if saved:
                        _provider_cache[current_mode].messages = saved
                        console.print(f"[dim]Restored {len(saved)//2} {current_mode} turns from last session.[/dim]")

                agent = _provider_cache[current_mode]

                # Augment with session state + memory (same as Claude mode)
                augmented = _build_claude_prompt(
                    user_input, conversation, memory,
                    session_state=session_state,
                    memory_summary=memory_summary,
                    aicli_context=aicli_context,
                )

                output = ""
                for chunk in agent.stream(augmented):
                    print(chunk, end="", flush=True)
                    output += chunk
                print()

            except Exception as e:
                console.print(f"[red][{current_mode} error] {e}[/red]")
                logger.error(f"{current_mode}_error", error=str(e))
                continue

            _log_prompt(current_mode, None, user_input, output)
            hook_runner.run("post_prompt", {**hook_ctx, "output": output})

            memory.add_entry(
                provider=current_mode, role=None,
                user_input=user_input, output=output,
                feature=conversation.get_feature(),
                tag=conversation.get_tag(),
            )

            _session_turn_count += 1
            session_store.save_messages(current_mode, agent.messages)
            save_session_state(
                working_dir, current_mode, active_project,
                conversation.get_feature() or "", conversation.get_tag() or "",
                user_input, output, _session_turn_count, cli_data_dir=_cli_data_dir,
            )
            session_state = load_session_state(working_dir, cli_data_dir=_cli_data_dir)

    # ==================================================================
    # On exit: save all provider histories one last time
    session_store.save_messages("claude", claude.messages)
    session_store.save_messages("openai", openai.messages)
    for name, prov in _provider_cache.items():
        session_store.save_messages(name, prov.messages)

    claude.close()
    console.print("[dim]Goodbye.[/dim]")


if __name__ == "__main__":
    main()
