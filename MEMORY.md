# Project Memory — aicli
_Generated: 2026-04-01 09:06 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to enable collaborative AI-assisted development with persistent context across multiple LLM tools. It features dual-storage (PostgreSQL 15+ + pgvector for semantic search), unified memory tables, async DAG workflow execution with Cytoscape visualization, and multi-provider LLM support (Claude, OpenAI, DeepSeek, Gemini, Grok) with server-side key management. Current focus is stabilizing schema consistency, validating data persistence across sessions, automating memory synthesis via Claude Haiku dual-layer processing, and resolving backend startup race conditions.

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
- **llm_providers**: Claude (Haiku), OpenAI, DeepSeek, Gemini, Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json); pricing, coupons, user_logs in SQL tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+
- **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + ui/npm run dev

## Key Decisions

- Engine/workspace separation: aicli/ contains backend logic; workspace/ holds per-project content; _system/ stores project state
- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- Electron desktop UI: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vanilla JS frontend (no framework/bundler); Vite dev server
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
- All LLM providers as independent adapters (Claude/OpenAI/DeepSeek/Gemini/Grok); Claude Haiku for dual-layer memory synthesis; server holds API keys
- Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for negotiation
- Memory synthesis: Claude Haiku dual-layer generates 5 files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from mem_ai_project_facts and mem_ai_work_items
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load; backend_startup_race_condition mitigated
- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations (linked via row id), not in summary arrays
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
- Manual relations managed via CLI/admin UI: depends_on, relates_to, blocks, implements; smart chunking by per-class/function (Python/JS/TS), per-section (MD), per-file (diff)
- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix), agents/mcp/ for MCP server
- CLI: Python 3.12 + prompt_toolkit + rich; command routing via verb-noun pattern; memory endpoint template variable scoping fixed
- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local dev via bash start_backend.sh + ui/npm run dev
- Config management: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing_storage in data/provider_storage/

## In Progress

- Memory file generation automation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md auto-regenerated from unified mem_ai_* tables with timestamp tracking
- Unified event table validation: mem_ai_events consolidates embeddings and memory events; removed event_summary_tags array and deprecated metadata columns
- Data persistence validation: tags disappearing on session switch root cause traced to cache invalidation triggering DB re-load; fix ensures persistence across switches
- Schema documentation cleanup: updated project_state.json and rules.md to reflect mem_ai_* unified table naming and removed deprecated database_schema field
- Tag column schema correction: mem_ai_tags_relations table DDL fixed; database migrations applied and persistence validated across session switches
- Backend startup race condition: AiCli appearing in Recent projects but unselectable on first load; retry logic implemented for empty project list handling

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/session_phases.json b/workspace/aicli/_system/session_phases.json
index 673bdfb..399a3ce 100644
--- a/workspace/aicli/_system/session_phases.json
+++ b/workspace/aicli/_system/session_phases.json
@@ -25,5 +25,14 @@
   },
   "484c8545-5032-4d6f-a27d-b31f285d6993": {
     "phase": "discovery"
+  },
+  "7d89c79f-b6f1-4bd4-a93f-09f2603fd1b1": {
+    "phase": "discovery"
+  },
+  "fa5883c1-6516-4c07-9124-67308c8aa1af": {
+    "phase": "discovery"
+  },
+  "1c7bb929-1715-485c-bcaa-d4dfd21450ad": {
+    "phase": "discovery"
   }
 }
\ No newline at end of file


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index ab0fa5b..a9ad786 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -27,11 +27,11 @@
     "pipeline_ui": "Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation",
     "billing_storage": "data/provider_storage/ (provider_costs.json); pricing, coupons, user_logs in SQL tables",
     "backend_modules": "routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server",
-    "dev_environment": "PyProject.toml + VS Code launch config (.vscode/launch.json); PyCharm: Mark backend/ as Sources Root",
+    "dev_environment": "PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root",
     "database": "PostgreSQL 15+",
     "node_modules_build": "npm 8+ with webpack/Electron-builder; dev server Vite on localhost",
     "database_version": "PostgreSQL 15+",
-    "build_tooling": "npm 8+ with webpack/Electron-builder; Vite dev server",
+    "build_tooling": "npm 8+ with Electron-builder; Vite dev server",
     "db_consolidation": "mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)",
     "db_tables_unified": "mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features",
     "unified_tables": "mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features",
@@ -120,7 +120,7 @@
     "cloud": "Railway (Dockerfile + railway.toml)",
     "desktop": "Electron-builder: Mac dmg (arm64+x64), Windows nsis, Linux AppImage+deb"
   },
-  "last_memory_run": "2026-04-01T08:28:00Z",
+  "last_memory_run": "2026-04-01T08:46:52Z",
   "_synthesis_cache": {
     "key_decisions": [
       "Engine/workspace separation: aicli/ contains backend logic; workspace/ holds per-project content; _system/ stores project state",
@@ -157,15 +157,16 @@
       "authentication": "JWT (python-jose + bcrypt) + DEV_MODE toggle",
       "llm_providers": "Claude (Haiku), OpenAI, DeepSeek, Gemini, Grok",
       "workflow_engine": "Async DAG executor (asyncio.gather) + YAML config",
-      "workflow_ui": "Cytoscape.js + cytoscape-dagre; 2-pane approval panel",
       "memory_synthesis": "Claude Haiku dual-layer with 5 output files",
       "chunking": "Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)",
       "mcp": "Stdio MCP server with 12+ tools",
-      "deployment": "Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev",
-      "config_management": "config.py + YAML pipelines + pyproject.toml",
-      "build_tooling": "npm 8+ with webpack/Electron-builder; Vite dev server"
+      "deployment_cloud": "Railway (Dockerfile + railway.toml)",
+      "deployment_desktop": "Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)",
+      "deployment_local": "bash start_backend.sh + ui/npm run dev",
+      "build_tooling": "npm 8+ with Electron-builder; Vite dev server",
+      "dev_environment": "PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root"
     },
-    "project_summary": "aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to enable collaborative AI-assisted development. It features dual-storage (PostgreSQL + pgvector for semantic search), unified memory tables (mem_ai_events, project_facts, work_items), async DAG workflow execution with Cytoscape visualization, and multi-provider LLM support (Claude, OpenAI, DeepSeek, Gemini, Grok) with server-side key management. Current focus is on stabilizing schema consistency, ensuring data persistence across sessions, and automating memory synthesis through Claude Haiku dual-layer processing.",
-    "memory_digest": "**20

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/history.jsonl b/workspace/aicli/_system/history.jsonl
index 6dc9eb6..5354120 100644
--- a/workspace/aicli/_system/history.jsonl
+++ b/workspace/aicli/_system/history.jsonl
@@ -59,153 +59,153 @@
 {"ts": "2026-03-17T18:18:33Z", "source": "claude_cli", "session_id": "484c8545-5032-4d6f-a27d-b31f285d6993", "provider": "claude", "user_input": "can you use the mcp tool and explain what the code is doing ?", "output": "Here's what **aicli** does:\n\n## aicli — Shared AI Memory Platform\n\n**Core idea**: When you switch between different AI tools (Claude CLI, Cursor, ChatGPT, the aicli web UI), they all forget your project context. aicli solves this by giving every LLM the **same persistent memory**.\n\n### What the code does\n\n1. **5-Layer Memory System** — Stores context at 5 levels: live conversation → session state → project docs → full history (JSONL + PostgreSQL) → global templates. The `/memory` command synthesizes all layers into files that each AI tool reads natively (CLAUDE.md, Cursor rules, Copilot instructions, etc.).\n\n2. **Multi-Provider CLI** — A terminal chat interface (`cli.py`) that talks to Claude, OpenAI, DeepSeek, Gemini, and xAI through a unified provider contract (`send(prompt, system) → str`). The server holds all API keys — the client sends none.\n\n3. **Entity/Knowledge Graph** — Every prompt and commit gets tagged to features, bugs, and tasks via the Planner UI. Nested tags, lifecycle tracking (idea → design → development → testing → done), and dependency links between entities.\n\n4. **Multi-Agent Workflows** — A graph DAG executor where you chain AI agents (architect → reviewer → developer → tester) with different roles and providers. Visualized with Cytoscape.js, configured in YAML.\n\n5. **Electron + FastAPI UI** — An Electron desktop app with tabs for Chat, Planner, Prompts, Code, Workflows, History, and Settings. FastAPI backend (16 routers), vanilla JS frontend (no React/bundler).\n\n6. **MCP Server** — 12+ tools exposed via Model Context Protocol (stdio) so Claude CLI and other MCP clients can query project state, search memory, create entities, sync GitHub issues, and run work-item pipelines.\n\n7. **Billing & Auth** — Multi-user with JWT auth, 3 roles (admin/paid/free), per-request billing with markup and coupons.\n\n### Available Roles\n- **architect.md** — for high-level design decisions\n- **reviewer.md** — for code review prompts\n\n### Current State\n- Phase: **dis", "user": null, "feature": null, "tags": [], "stop_reason": "end_turn", "phase": "discovery"}
 {"ts": "2026-03-17T18:28:02Z", "source": "claude_cli", "session_id": "484c8545-5032-4d6f-a27d-b31f285d6993", "provider": "claude", "user_input": "What is the claude agent sdk is uded for can it be used for my use cases for mutli agents (project manager (high design), develop , tester , reviewer) ?", "output": "## Claude Agent SDK vs Your Current Multi-Agent System\n\n### What is the Claude Agent SDK?\n\nThe **Claude Agent SDK** is Anthropic's official Python/TypeScript framework for building AI agents that can:\n- Execute tools (file read, bash, web search, custom MCP tools)\n- Delegate to **subagents** (specialized Claude instances with different system prompts)\n- Maintain conversation state across turns\n- Handle streaming and user approvals\n\n### Can it replace your PM → Developer → Tester → Reviewer pipeline?\n\n**Short answer: No — your custom system is already more powerful for this use case.** Here's why:\n\n| Capability | Claude Agent SDK | Your aicli DAG + Pipeline |\n|---|---|---|\n| **Loop-back** (Reviewer → Developer if score < 7) | Not native; workaround via resume | Built-in with iteration cap |\n| **Multi-provider** (Haiku for PM, Claude for Dev, DeepSeek for review) | Claude only | 5 providers per node |\n| **Conditional edges** | Via prompt instructions only | Native condition eval (eq, gte, contains...) |\n| **Approval gates** | Limited (user input tool) | Native `require_approval`

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index 93341c4..bec097a 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-01T08:40:17Z",
+  "last_updated": "2026-04-01T08:56:35Z",
   "last_session_id": "11163d9b-a609-4847-8ca9-702fce4165c5",
-  "last_session_ts": "2026-04-01T08:40:17Z",
-  "session_count": 323,
+  "last_session_ts": "2026-04-01T08:56:35Z",
+  "session_count": 324,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index f3daf43..2eeeb85 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 08:27 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 08:46 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -32,11 +32,11 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
 - **billing_storage**: data/provider_storage/ (provider_costs.json); pricing, coupons, user_logs in SQL tables
 - **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
-- **dev_environment**: PyProject.toml + VS Code launch config (.vscode/launch.json); PyCharm: Mark backend/ as Sources Root
+- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
 - **database**: PostgreSQL 15+
 - **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
 - **database_version**: PostgreSQL 15+
-- **build_tooling**: npm 8+ with webpack/Electron-builder; Vite dev server
+- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
 - **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
 - **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
 - **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 42e29bb..f28a3de 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -561,3 +561,5 @@
 {"ts": "2026-04-01T08:26:53Z", "action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "aebacdad", "message": "chore: update ai context files and session history", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "31002ada", "message": "docs: update AI assistant rules and memory after session 11163d9b", "files_count": 32, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pull warning: error: cannot pull with rebase: You have unstaged changes.\nerror: Please commit or stash them.", "ts": "2026-04-01T08:27:47Z"}
 {"ts": "2026-04-01T08:27:38Z", "action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "31002ada", "message": "docs: update AI assistant rules and memory after session 11163d9b", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "19cc32ab", "message": "chore: update AI rules, memory, and minor backend router fixes", "files_count": 33, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T08:40:27Z"}
+{"ts": "2026-04-01T08:40:17Z", "action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "19cc32ab", "message": "chore: update AI rules, memory, and minor backend router fixes", "pushed": true, "push_error": ""}


## AI Synthesis

**2026-03-17** `claude_cli` — Session analysis established aicli as a shared AI memory platform solving persistent context loss across multiple LLM tools (Claude CLI, Cursor, ChatGPT, web UI). Core architecture comprises 5-layer memory system (live conversation → session state → project docs → history → templates) synthesized into provider-native files. **2026-03-17** `claude_cli` — Multi-agent design validated: custom DAG executor with loop-back, conditional routing, and multi-provider support (Claude/OpenAI/DeepSeek/Gemini/Grok) proven superior to Claude Agent SDK for PM → Developer → Tester → Reviewer pipeline requiring iterative approval gates. **2026-04-01** `memory_synthesis` — Schema consolidation completed: unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) validated; deprecated database_schema field removed from project_state.json. **2026-04-01** `memory_synthesis` — Data persistence fix deployed: cache invalidation triggering spurious DB re-loads eliminated; tags now persist across session switches via mem_ai_tags_relations row-id linking. **2026-04-01** `memory_synthesis` — Backend startup race condition resolved: retry logic handles empty project list on first load; AiCli now consistently appears in Recent projects and remains selectable. **2026-04-01** `memory_synthesis` — Dev environment documentation clarified: Electron-builder confirmed (removed webpack reference); Vite dev server and PyProject.toml + VS Code launch.json configuration finalized.