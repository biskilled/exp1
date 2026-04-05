# Project Memory — aicli
_Generated: 2026-04-03 20:07 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining Claude CLI, FastAPI backend, Electron desktop UI, and PostgreSQL with pgvector for semantic search. It synthesizes project context into memory files (CLAUDE.md, MEMORY.md, etc.) via async DAG workflows, supporting multiple LLM providers with cost tracking and hierarchical user authentication. Currently refactoring memory generation to use inline planner_tags snapshot fields as canonical context, standardizing SQL cursor handling, and consolidating schema across unified tables.

## Project Facts

- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **db_engine**: SQL
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_target**: Claude_CLI_and_LLM_platforms
- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
- **memory_management_pattern**: load_once_on_access_update_on_save
- **pending_implementation**: memory_items_and_project_facts_table_population
- **pending_issues**: project_visibility_bug_active_project_not_displaying
- **performance_optimization**: redundant_SQL_calls_eliminated
- **pipeline/auth**: Acceptance criteria:
# PM Analysis: Email Verification Feature

---

## Context Summary

The tagged context reveals this work item is an **incremental enhancement** to an existing authentication system. Sign In and Create Account forms are already live and functional. The prior PM analysis identified email verification as the missing layer—the system currently accepts any email without confirming ownership. The analys

Reviewer: ```json
{
  "passed": false,
  "score": 4,
  "issues": [
    "Implementation is incomplete — cuts off mid-file in EmailService.ts without finishing AWS SES client setup, email template loading, or the
- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
- **stale_code_removed**: db_ensure_project_schema_call_replaced_with_ensure_shared_schema
- **tagging_system**: nested_hierarchy_beyond_2_levels
- **tagging_system_hierarchy**: nested_hierarchy_beyond_2_levels_approved
- **ui_action_menu_pattern**: 3_dot_menu_for_action_visibility
- **ui_library**: 3_dot_menu_pattern
- **unimplemented_features**: memory_items_and_project_facts_tables_not_updating
- **unresolved_issues**: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: PostgreSQL 15+
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) + timestamp tracking
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + ui/npm run dev

## Key Decisions

- Engine/workspace separation: aicli/ contains backend logic and CLI; workspace/ contains per-project content; _system/ stores project state and memory files
- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) replace per-project fragmentation
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract; Claude Haiku for dual-layer memory synthesis
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load preventing startup race conditions
- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; organized as routers/ for API, core/ for infrastructure, data/ (dl_ prefix) for data access
- MCP server (stdio) with 12+ tools for embedding and data retrieval; environment-configured via BACKEND_URL and ACTIVE_PROJECT
- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop; local via bash start_backend.sh + ui/npm run dev
- Memory file generation reads snapshot data from inline planner_tags fields (summary, action_items, design, code_summary); SQL cursor tuple unpacking standardized
- Config management: config.py for externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support
- Cost tracking via provider_costs.json with fallback pricing; billing storage in data/provider_storage/ with rich table output

## In Progress

- Memory file generation refactoring: planner_tags inline fields (summary, action_items, design, code_summary) now canonical context source; snapshot fields integrated across memory modules
- SQL cursor tuple unpacking standardization: memory_promotion.py and memory_files.py fixed for reliable 4-column unpacking; _SQL_ACTIVE_TAGS and _SQL_GET_CURRENT_FACTS corrected
- Feature details context loading: planner_tags query limited to 30 most recent; render_feature_claude_md() reads complete tag metadata from inline snapshot fields
- Memory file lifecycle enhancement: get_active_feature_tags() filters active/open tags with snapshots; context dict populated with id, name, short_desc, requirements, summary, action_items, design, code_summary
- Database cursor handling robustness: standardized tuple unpacking with improved SQL result column ordering; timestamp tracking added to memory synthesis metadata
- Schema consolidation: mem_ai_tags_relations relations section removed from feature rendering; inline snapshot fields integrated as primary data source

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-03

diff --git a/old/aicli/core/git_supervisor.py b/old/aicli/core/git_supervisor.py
deleted file mode 100644
index bf8c23e..0000000
--- a/old/aicli/core/git_supervisor.py
+++ /dev/null
@@ -1,200 +0,0 @@
-"""
-Git supervisor — detects changes, generates commit messages via OpenAI,
-and runs automated commit + push after each AI response.
-Fires post_commit and post_push hooks after each successful operation.
-"""
-
-import subprocess
-
-
-class GitSupervisor:
-
-    DEFAULT_IGNORED = [
-        ".aicli/",
-        "CLAUDE.md",
-        "OPENAI.md",
-        "prompts/",
-        "aicli.yaml",
-    ]
-
-    def __init__(self, config: dict, logger=None, hook_runner=None):
-        self.config = config
-        self.logger = logger
-        self.hook_runner = hook_runner
-        self.ignored_paths = config.get("ignored_paths", self.DEFAULT_IGNORED)
-
-    # ------------------------------------------------------------------
-    # Change detection
-    # ------------------------------------------------------------------
-
-    def get_change_stats(self) -> str:
-        result = subprocess.run(
-            ["git", "diff", "--shortstat"],
-            capture_output=True, text=True,
-        )
-        return result.stdout.strip()
-
-    def get_changed_files(self) -> list[str]:
-        staged = subprocess.run(
-            ["git", "diff", "--name-only", "--cached"],
-            capture_output=True, text=True,
-        ).stdout.strip().splitlines()
-
-        unstaged = subprocess.run(
-            ["git", "diff", "--name-only"],
-            capture_output=True, text=True,
-        ).stdout.strip().splitlines()
-
-        untracked = subprocess.run(
-            ["git", "ls-files", "--others", "--exclude-standard"],
-            capture_output=True, text=True,
-        ).stdout.strip().splitlines()
-
-        all_files = list(dict.fromkeys(staged + unstaged + untracked))  # dedup, preserve order
-        return self._filter_files(all_files)
-
-    def _filter_files(self, files: list[str]) -> list[str]:
-        return [
-            f for f in files
-            if f and not any(f.startswith(p) for p in self.ignored_paths)
-        ]
-
-    def get_current_branch(self) -> str:
-        result = subprocess.run(
-            ["git", "branch", "--show-current"],
-            capture_output=True, text=True,
-        )
-        return result.stdout.strip()
-
-    # ------------------------------------------------------------------
-    # Tests
-    # ------------------------------------------------------------------
-
-    def run_tests(self) -> bool:
-        if not self.config.get("run_tests"):
-            return True
-        test_command = self.config.get("test_command", "pytest")
-        print("Running tests...")
-        result = subprocess.run(test_command, shell=True)
-        if result.returncode != 0:
-            print("Tests failed — commit aborted.")
-            return False
-        return True
-
-    # ------------------------------------------------------------------
-    # Commit handler
-    # ------------------------------------------------------------------
-
-    def handle_commit(
-        self,
-        llm_output: str,
-        openai_agent,
-        context: dict | None = None,
-    ) -> dict | None:
-        """
-        If there are changed files: generate a commit message, stage, commit, push.
-        Fires post_commit and post_push hooks with full context.
-        Returns commit metadata dict or None.
-        """
-        changed_files = self.get_changed_files()
-        if not changed_files:
-            return None
-
-        stats = self.get_change_stats()
-
-        if self.logger:
-            self.logger.info("git_changes", files=changed_files, stats=stats)
-
-        print(f"\nChanges: {stats}  ({len(changed_files)} files)")
-
-        # Guard against huge accidental changes
-        threshold = self.config.get("large_change_file_threshold", 20)
-        if len(changed_files) > threshold:
-     

### `commit` — 2026-04-03

diff --git a/old/aicli/core/env_loader.py b/old/aicli/core/env_loader.py
deleted file mode 100644
index e110005..0000000
--- a/old/aicli/core/env_loader.py
+++ /dev/null
@@ -1,18 +0,0 @@
-"""
-Loads environment variables from a .env file.
-Accepts both str and Path objects.
-"""
-
-import os
-from pathlib import Path
-from dotenv import load_dotenv
-
-
-def load_environment(env_path: str | Path = ".env") -> dict:
-    env_file = Path(env_path)
-    if env_file.exists():
-        load_dotenv(dotenv_path=env_file, override=False)
-        print(f"[env] Loaded {env_file}")
-    else:
-        print("[env] No .env file found — using system environment.")
-    return dict(os.environ)


### `commit` — 2026-04-03

diff --git a/old/aicli/core/cost_tracker.py b/old/aicli/core/cost_tracker.py
deleted file mode 100644
index b7e1351..0000000
--- a/old/aicli/core/cost_tracker.py
+++ /dev/null
@@ -1,185 +0,0 @@
-"""
-Cost tracker — records token usage and cost per workflow step.
-
-Appends to workspace/<project>/runs/workflow_costs.jsonl.
-Prints a Rich table after each workflow run.
-
-Pricing is loaded from ui/backend/data/provider_costs.json (the single source of
-truth managed by the admin UI). Falls back to built-in defaults if the file is
-absent (e.g., backend not yet started).
-"""
-
-import json
-from datetime import datetime, timezone
-from pathlib import Path
-from typing import Optional
-
-from rich.console import Console
-from rich.table import Table
-
-# ── Fallback defaults (USD per token) — matches ui/backend/core/provider_costs.py ──
-# Only used when ui/backend/data/provider_costs.json is not available.
-_FALLBACK_PER_TOKEN: dict[str, dict[str, float]] = {
-    "claude-sonnet-4-6":         {"input": 0.000003,    "output": 0.000015},
-    "claude-opus-4-6":           {"input": 0.000015,    "output": 0.000075},
-    "claude-haiku-4-5-20251001": {"input": 0.0000008,   "output": 0.000004},
-    "gpt-4.1":                   {"input": 0.000002,    "output": 0.000008},
-    "gpt-4.1-mini":              {"input": 0.0000004,   "output": 0.0000016},
-    "gpt-4o":                    {"input": 0.000005,    "output": 0.000015},
-    "gpt-4o-mini":               {"input": 0.00000015,  "output": 0.0000006},
-    "deepseek-chat":             {"input": 0.00000027,  "output": 0.0000011},
-    "deepseek-reasoner":         {"input": 0.00000055,  "output": 0.00000219},
-    "grok-3":                    {"input": 0.000003,    "output": 0.000015},
-    "grok-3-fast":               {"input": 0.000005,    "output": 0.000025},
-    "grok-3-mini":               {"input": 0.0000003,   "output": 0.0000005},
-    "gemini-2.0-flash":          {"input": 0.0000001,   "output": 0.0000004},
-    "gemini-1.5-pro":            {"input": 0.0000035,   "output": 0.0000105},
-    "gemini-1.5-flash":          {"input": 0.000000075, "output": 0.0000003},
-}
-
-# Resolved once at import time — points to the canonical pricing file
-_ENGINE_ROOT = Path(__file__).parent.parent.resolve()
-_PROVIDER_COSTS_FILE = _ENGINE_ROOT / "ui" / "backend" / "data" / "provider_costs.json"
-
-
-def _load_pricing() -> dict[str, dict[str, float]]:
-    """
-    Load per-token costs from ui/backend/data/provider_costs.json.
-    Returns a flat model→{input,output} dict.
-    Falls back to _FALLBACK_PER_TOKEN if the file is missing or malformed.
-    """
-    try:
-        if _PROVIDER_COSTS_FILE.exists():
-            data = json.loads(_PROVIDER_COSTS_FILE.read_text(encoding="utf-8"))
-            flat: dict[str, dict[str, float]] = {}
-            for _provider, models in data.get("providers", {}).items():
-                for model, costs in models.items():
-                    flat[model] = {
-                        "input":  float(costs.get("input",  0.000001)),
-                        "output": float(costs.get("output", 0.000005)),
-                    }
-            if flat:
-                return flat
-    except Exception:
-        pass
-    return dict(_FALLBACK_PER_TOKEN)
-
-
-def _calc_cost(model: str, input_tokens: int, output_tokens: int) -> float:
-    """Calculate USD cost using the canonical pricing file."""
-    pricing = _load_pricing()
-    costs = pricing.get(model)
-    if costs is None:
-        # Try prefix match (e.g. "claude-sonnet" matches "claude-sonnet-4-6")
-        model_lower = model.lower()
-        for m, c in pricing.items():
-            if model_lower.startswith(m.lower()) or m.lower().startswith(model_lower):
-                costs = c
-                break
-    if costs is None:
-        costs = {"input": 0.000001, "output": 0.000005}  # conservative default
-    return round(input_tokens * costs["input"] + output_tokens * costs["output"], 8)
-
-
-c

### `commit` — 2026-04-03

diff --git a/old/aicli/core/conversation.py b/old/aicli/core/conversation.py
deleted file mode 100644
index bff52d0..0000000
--- a/old/aicli/core/conversation.py
+++ /dev/null
@@ -1,154 +0,0 @@
-"""
-Persistent conversation state with feature and tag tracking.
-Stores conversation turns, commits, and a rolling project summary.
-"""
-
-import json
-import os
-from datetime import datetime, timezone
-
-
-class ConversationState:
-
-    def __init__(self, max_history: int = 200, path: str = ".aicli/current_session.json", cli_data_dir: str = ".aicli"):
-        self.max_history = max_history
-        self.path = path
-
-        os.makedirs(os.path.dirname(path), exist_ok=True)
-
-        # Default structure — loaded from disk if file exists
-        self.data: dict = {
-            "session_id": datetime.now(timezone.utc).isoformat(),
-            "current_feature": None,
-            "current_tag": None,
-            "conversation": [],   # list of turn dicts
-            "commits": [],        # list of commit dicts
-            "project_summary": "",
-            "tags": {},           # {tag_name: [entry indices]}
-            "features": {},       # {feature_name: count}
-        }
-
-        self.load()
-
-    # ------------------------------------------------------------------
-    # Core operations
-    # ------------------------------------------------------------------
-
-    def append(self, provider: str, role, user_input: str, output: str, commit=None, usage=None):
-        """Record a conversation turn and optional commit metadata."""
-        entry = {
-            "timestamp": datetime.now(timezone.utc).isoformat(),
-            "provider": provider,
-            "role": role,
-            "user_input": user_input,
-            "output": output,
-            "feature": self.get_feature(),
-            "tag": self.get_tag(),
-            "usage": usage,
-        }
-
-        self.data["conversation"].append(entry)
-
-        # Update feature counter
-        if entry["feature"]:
-            self.data["features"][entry["feature"]] = (
-                self.data["features"].get(entry["feature"], 0) + 1
-            )
-
-        # Update tag index
-        if entry["tag"]:
-            tag = entry["tag"]
-            idx = len(self.data["conversation"]) - 1
-            if tag not in self.data["tags"]:
-                self.data["tags"][tag] = []
-            self.data["tags"][tag].append(idx)
-
-        if commit:
-            commit_entry = {
-                "timestamp": datetime.now(timezone.utc).isoformat(),
-                "feature": self.get_feature(),
-                "tag": self.get_tag(),
-                "provider": provider,
-                "role": role,
-                "user_prompt": user_input,
-                "commit_hash": commit.get("hash"),
-                "commit_message": commit.get("message"),
-                "files_changed": commit.get("files", []),
-                "change_stats": commit.get("stats"),
-            }
-            self.data["commits"].append(commit_entry)
-
-        # Trim conversation history to max
-        if len(self.data["conversation"]) > self.max_history:
-            self.data["conversation"] = self.data["conversation"][-self.max_history:]
-
-        self.save()
-
-    def update_summary(self, summary: str):
-        self.data["project_summary"] = summary
-        self.save()
-
-    # ------------------------------------------------------------------
-    # Persistence
-    # ------------------------------------------------------------------
-
-    def load(self):
-        if os.path.exists(self.path):
-            try:
-                with open(self.path, encoding="utf-8") as f:
-                    loaded = json.load(f)
-                # Merge loaded data, preserving new keys with defaults
-                for key, value in loaded.items():
-                    self.data[key] = value
-                # Ensure new keys exist even in old session files
-               

### `commit` — 2026-04-03

diff --git a/old/aicli/core/context_builder.py b/old/aicli/core/context_builder.py
deleted file mode 100644
index ad0ee40..0000000
--- a/old/aicli/core/context_builder.py
+++ /dev/null
@@ -1,167 +0,0 @@
-"""
-ContextBuilder — collects and formats files/memory for LLM injection.
-
-Resolves inject_files directives from workflow YAML:
-  - "PROJECT.md"              → from project workspace dir
-  - "{{code_dir}}/cli.py"    → from code dir
-  - "{{code_dir}}/providers/" → all .py files in folder
-  - "auto"                    → recently modified files in code_dir
-
-Template vars:
-  {{code_dir}}    → resolved code directory
-  {{project_dir}} → resolved project workspace directory
-"""
-
-import os
-import time
-from pathlib import Path
-from typing import Optional
-
-
-class ContextBuilder:
-
-    AUTO_EXTENSIONS = {".py", ".ts", ".js", ".yaml", ".yml", ".md", ".json", ".toml"}
-    MAX_FILE_CHARS = 20_000     # truncate individual large files
-    MAX_TOTAL_CHARS = 120_000   # total context cap
-
-    def __init__(
-        self,
-        project_dir: Path,
-        code_dir: Optional[Path] = None,
-    ):
-        self.project_dir = project_dir.resolve()
-        self.code_dir = code_dir.resolve() if code_dir else None
-        self._total_chars = 0
-
-    # ------------------------------------------------------------------
-    # Public
-    # ------------------------------------------------------------------
-
-    def build(
-        self,
-        inject_files: list[str] | None = None,
-        inject_context: list[str] | None = None,
-        memory_entries: list[str] | None = None,
-        summary_text: str | None = None,
-    ) -> str:
-        """
-        Build the full context block to prepend to a step prompt.
-        Returns an empty string if nothing to inject.
-        """
-        # Reset per-call so multiple workflow steps don't share the budget
-        self._total_chars = 0
-        sections: list[str] = []
-
-        # --- Files ---
-        if inject_files:
-            file_blocks = self._collect_files(inject_files)
-            if file_blocks:
-                sections.append("--- FILES ---\n" + "\n\n".join(file_blocks))
-
-        # --- Memory ---
-        if inject_context and "memory" in inject_context and memory_entries:
-            mem_text = "\n\n".join(memory_entries[:10])
-            sections.append(f"--- MEMORY (last {min(10, len(memory_entries))}) ---\n{mem_text}")
-
-        # --- Summary ---
-        if inject_context and "summary" in inject_context and summary_text:
-            sections.append(f"--- SUMMARY ---\n{summary_text}")
-
-        if not sections:
-            return ""
-
-        return "\n\n".join(sections) + "\n\n"
-
-    # ------------------------------------------------------------------
-    # Internal
-    # ------------------------------------------------------------------
-
-    def _resolve_var(self, path_str: str) -> str:
-        s = path_str
-        if self.code_dir:
-            s = s.replace("{{code_dir}}", str(self.code_dir))
-        s = s.replace("{{project_dir}}", str(self.project_dir))
-        return s
-
-    def _collect_files(self, directives: list[str]) -> list[str]:
-        blocks: list[str] = []
-        for directive in directives:
-            if self._total_chars >= self.MAX_TOTAL_CHARS:
-                break
-            directive = directive.strip()
-            if directive == "auto":
-                blocks.extend(self._auto_files())
-            else:
-                resolved = self._resolve_var(directive)
-                path = Path(resolved)
-                # Try project_dir relative if not absolute or found
-                if not path.is_absolute():
-                    path = self.project_dir / resolved
-                blocks.extend(self._path_to_blocks(path, label=directive))
-        return blocks
-
-    def _path_to_blocks(self, path: Path, label: str) -> list[str]:
-        blocks: list[str] = []
-        if not path.exists():
-

### `commit` — 2026-04-03

diff --git a/old/aicli/core/analytics.py b/old/aicli/core/analytics.py
deleted file mode 100644
index 3c9f7e5..0000000
--- a/old/aicli/core/analytics.py
+++ /dev/null
@@ -1,55 +0,0 @@
-"""
-Project analytics — usage statistics derived from ConversationState data.
-"""
-
-from collections import defaultdict
-from datetime import datetime
-
-
-class ProjectAnalytics:
-
-    def __init__(self, conversation):
-        self.data = conversation.data
-
-    def total_prompts(self) -> int:
-        return len(self.data.get("conversation", []))
-
-    def total_commits(self) -> int:
-        return len(self.data.get("commits", []))
-
-    def commits_by_feature(self) -> dict:
-        features: dict = defaultdict(int)
-        for commit in self.data.get("commits", []):
-            feature = commit.get("feature") or "unassigned"
-            features[feature] += 1
-        return dict(features)
-
-    def commits_by_tag(self) -> dict:
-        tags: dict = defaultdict(int)
-        for commit in self.data.get("commits", []):
-            tag = commit.get("tag") or "untagged"
-            tags[tag] += 1
-        return dict(tags)
-
-    def total_files_changed(self) -> int:
-        return sum(
-            len(c.get("files_changed", []))
-            for c in self.data.get("commits", [])
-        )
-
-    def session_duration_hours(self) -> float:
-        conversation = self.data.get("conversation", [])
-        if len(conversation) < 2:
-            return 0.0
-        first = datetime.fromisoformat(conversation[0]["timestamp"])
-        last = datetime.fromisoformat(conversation[-1]["timestamp"])
-        return (last - first).total_seconds() / 3600
-
-    def estimate_cost(self, cost_per_1k: float = 0.01) -> float:
-        total_tokens = 0
-        for entry in self.data.get("conversation", []):
-            usage = entry.get("usage")
-            if usage:
-                total_tokens += usage.get("input_tokens", 0)
-                total_tokens += usage.get("output_tokens", 0)
-        return (total_tokens / 1000) * cost_per_1k


## AI Synthesis

**2026-03-14** `PROJECT.md` — Consolidated aicli architecture with unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) replacing per-project fragmentation; established login_as_first_level_hierarchy auth pattern.
**Recent** `memory_modules` — Standardized SQL cursor tuple unpacking across memory_promotion.py and memory_files.py for reliable 4-column result handling; fixed _SQL_ACTIVE_TAGS and _SQL_GET_CURRENT_FACTS query column ordering.
**Recent** `feature_context` — Integrated planner_tags inline snapshot fields (summary, action_items, design, code_summary) as canonical context source; removed mem_ai_tags_relations relations section from feature rendering, simplified to 30 most recent tags.
**Recent** `memory_lifecycle` — Enhanced get_active_feature_tags() to filter open tags with snapshots; render_feature_claude_md() now reads complete tag metadata including requirements and design fields from inline planner_tags.
**Recent** `database_robustness` — Added timestamp tracking to memory synthesis metadata; improved SQL result column ordering documentation for cursor unpacking standardization.
**Removed** `git_supervisor.py, env_loader.py, cost_tracker.py` — Archived legacy Git automation, environment loading, and early cost tracking modules; retained cost calculation logic in provider_costs.json model.