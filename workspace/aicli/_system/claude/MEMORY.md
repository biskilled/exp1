# Project Memory — aicli
_Generated: 2026-04-01 12:26 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform unifying development context across Claude CLI, LLM assistants, and web/desktop UIs through PostgreSQL semantic storage (pgvector), async DAG workflows, and Claude Haiku-powered memory synthesis. The architecture features an Electron desktop UI combining Vanilla JS with xterm.js, Monaco editor, and Cytoscape.js for workflow visualization; the backend is FastAPI-based with support for multiple LLM providers and MCP integration. Current focus is on stabilizing the unified mem_ai_* table schema, ensuring data persistence across session switches, and automating memory synthesis from project facts and work items.

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

- Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state and memory files
- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users; login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules; Claude Haiku for dual-layer memory synthesis generating 5 output files
- Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load; backend_startup_race_condition mitigated
- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking, not in summary arrays
- MCP server (stdio) with 12+ tools configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations (depends_on, relates_to, blocks, implements) managed via CLI/admin UI
- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix), agents/mcp/ for MCP server
- CLI: Python 3.12 + prompt_toolkit + rich with verb-noun command routing; memory endpoint template variable scoping fixed
- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local via bash start_backend.sh + ui/npm run dev
- Config management: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing storage in data/provider_storage/

## In Progress

- Memory file generation automation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md auto-regenerated from mem_ai_project_facts and mem_ai_work_items with timestamp tracking completed
- Unified event table validation: mem_ai_events consolidates embeddings and memory events; removed event_summary_tags array and deprecated metadata columns; schema migration applied
- Data persistence across session switches: tags disappearing root cause traced to cache invalidation during DB reload; fix ensures mem_ai_tags_relations persistence with proper row ID linking
- Schema documentation cleanup: project_state.json and rules.md updated to reflect mem_ai_* unified naming; removed conflicting legacy database_schema field
- Backend startup race condition resolution: AiCli project appearing in Recent but unselectable on first load; retry logic implemented for empty project list handling during initialization
- Database migrations and tag column schema correction: mem_ai_tags_relations DDL fixed; persistence validated across session switches with proper tag column handling

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index a9ad786..c170f70 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -120,7 +120,7 @@
     "cloud": "Railway (Dockerfile + railway.toml)",
     "desktop": "Electron-builder: Mac dmg (arm64+x64), Windows nsis, Linux AppImage+deb"
   },
-  "last_memory_run": "2026-04-01T08:46:52Z",
+  "last_memory_run": "2026-04-01T08:56:56Z",
   "_synthesis_cache": {
     "key_decisions": [
       "Engine/workspace separation: aicli/ contains backend logic; workspace/ holds per-project content; _system/ stores project state",
@@ -157,16 +157,13 @@
       "authentication": "JWT (python-jose + bcrypt) + DEV_MODE toggle",
       "llm_providers": "Claude (Haiku), OpenAI, DeepSeek, Gemini, Grok",
       "workflow_engine": "Async DAG executor (asyncio.gather) + YAML config",
-      "memory_synthesis": "Claude Haiku dual-layer with 5 output files",
-      "chunking": "Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)",
       "mcp": "Stdio MCP server with 12+ tools",
       "deployment_cloud": "Railway (Dockerfile + railway.toml)",
       "deployment_desktop": "Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)",
       "deployment_local": "bash start_backend.sh + ui/npm run dev",
-      "build_tooling": "npm 8+ with Electron-builder; Vite dev server",
-      "dev_environment": "PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root"
+      "build_tooling": "npm 8+ with Electron-builder; Vite dev server"
     },
-    "project_summary": "aicli is a shared AI memory platform that gives every LLM (Claude CLI, aicli CLI, Cursor, web UI) identical project memory, billing, multi-LLM workflows, and a unified knowledge graph. Built on FastAPI + PostgreSQL with pgvector, it provides an Electron desktop UI with xterm.js, Monaco editor, and Cytoscape.js for workflow visualization. Current focus is stabilizing the unified mem_ai_* table schema, ensuring data persistence across session switches, and automating memory synthesis from project facts and work items.",
-    "memory_digest": "**2026-03-14** `schema_consolidation` \u2014 Unified database schema completed: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, and mem_ai_features replace per-project event tables and deprecated metadata structures.\n**2026-03-14** `persistence_fix` \u2014 Tag disappearance on session switch root-caused to cache invalidation; resolved by fixing DB reload logic and ensuring tags persist in mem_ai_tags_relations with proper row ID linking.\n**2026-03-14** `documentation_alignment` \u2014 project_state.json and rules.md updated to reflect unified table naming; removed legacy database_schema field that conflicted with unified architecture.\n**2026-03-14** `memory_generation_automation` \u2014 Memory synthesis pipeline generates 5 output files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) automatically from mem_ai_project_facts and mem_ai_work_items with timestamp tracking.\n**2026-03-09** `backend_startup_race` \u2014 AiCli project appearing in Recent but unselectable on first load fixed via retry logic for empty project list handling during backend initialization.\n**2026-03-09** `schema_migration` \u2014 mem_ai_tags_relations DDL corrected and database migrations applied; persistence validated across session switches with proper tag column handling."
+    "project_summary": "aicli is a shared AI memory platform that unifies development context across Claude CLI, LLM assistants, and web/desktop UIs through PostgreSQL semantic storage (pgvector), async DAG workflows, and Claude Haiku-powered memory synthesis. The desktop application combines Electron with Vanilla JS, xterm.js, Monaco editor, and Cytoscape.js for workflow visualization and terminal interaction; the backend is FastAPI-based with multi-provide

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index bec097a..1629c5a 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-01T08:56:35Z",
+  "last_updated": "2026-04-01T09:06:25Z",
   "last_session_id": "11163d9b-a609-4847-8ca9-702fce4165c5",
-  "last_session_ts": "2026-04-01T08:56:35Z",
-  "session_count": 324,
+  "last_session_ts": "2026-04-01T09:06:25Z",
+  "session_count": 325,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 2eeeb85..106de7b 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 08:46 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 08:56 UTC
 
 # aicli — Shared AI Memory Platform
 


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index f28a3de..80e672e 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -563,3 +563,5 @@
 {"ts": "2026-04-01T08:27:38Z", "action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "31002ada", "message": "docs: update AI assistant rules and memory after session 11163d9b", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "19cc32ab", "message": "chore: update AI rules, memory, and minor backend router fixes", "files_count": 33, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T08:40:27Z"}
 {"ts": "2026-04-01T08:40:17Z", "action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "19cc32ab", "message": "chore: update AI rules, memory, and minor backend router fixes", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "fc265cbe", "message": "chore: update system docs, memory, and session artifacts", "files_count": 32, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T08:56:44Z"}
+{"ts": "2026-04-01T08:56:35Z", "action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "fc265cbe", "message": "chore: update system docs, memory, and session artifacts", "pushed": true, "push_error": ""}


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index 63d804f..be95dd8 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-01 08:46 UTC by aicli /memory_
+_Generated: 2026-04-01 08:56 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform that gives every LLM (Claude CLI, aicli CLI, Cursor, web UI) identical project memory, billing, multi-LLM workflows, and a unified knowledge graph. Built on FastAPI + PostgreSQL with pgvector, it provides an Electron desktop UI with xterm.js, Monaco editor, and Cytoscape.js for workflow visualization. Current focus is stabilizing the unified mem_ai_* table schema, ensuring data persistence across session switches, and automating memory synthesis from project facts and work items.
+aicli is a shared AI memory platform that unifies development context across Claude CLI, LLM assistants, and web/desktop UIs through PostgreSQL semantic storage (pgvector), async DAG workflows, and Claude Haiku-powered memory synthesis. The desktop application combines Electron with Vanilla JS, xterm.js, Monaco editor, and Cytoscape.js for workflow visualization and terminal interaction; the backend is FastAPI-based with multi-provider LLM adapter support and MCP server integration. Current focus is stabilizing the unified mem_ai_* event/fact/work-item table schema, resolving data persistence across session switches, and automating memory file generation with proper cache management.
 
 ## Project Facts
 
@@ -115,413 +115,61 @@ Reviewer: ```json
 
 > Distilled summaries (Trycycle-reviewed). Feature summaries shown first.
 
-### `commit` — 2026-04-01
-
-diff --git a/workspace/aicli/_system/session_tags.json b/workspace/aicli/_system/session_tags.json
-new file mode 100644
-index 0000000..9dd1da3
---- /dev/null
-+++ b/workspace/aicli/_system/session_tags.json
-@@ -0,0 +1,6 @@
-+{
-+  "phase": "discovery",
-+  "feature": null,
-+  "bug_ref": null,
-+  "extra": {}
-+}
-\ No newline at end of file
-
-
-### `commit` — 2026-04-01
-
-diff --git a/workspace/aicli/_system/session_phases.json b/workspace/aicli/_system/session_phases.json
-new file mode 100644
-index 0000000..673bdfb
---- /dev/null
-+++ b/workspace/aicli/_system/session_phases.json
-@@ -0,0 +1,29 @@
-+{
-+  "test-cli-session-123": {
-+    "phase": "development"
-+  },
-+  "03f774e9-ad60-4cf3-8c0c-0191ba9a78d0": {
-+    "phase": "discovery"
-+  },
-+  "05e9af57-76f6-4aef-bb28-8347693f4099": {
-+    "phase": "development"
-+  },
-+  "cc70394f-9674-433a-88ce-489c9759ccf4": {
-+    "phase": "testing"
-+  },
-+  "ffeb4281-920b-4404-a108-37a3b8e54d40": {
-+    "phase": "review"
-+  },
-+  "0f976fad-b2e0-40f7-ad36-702093d8dda7": {
-+    "phase": "testing"
-+  },
-+  "5b19c863-f99a-439c-b595-b415d0d342ed": {
-+    "phase": "discovery"
-+  },
-+  "ffe274ef-6d8d-4548-9a15-a6c9801a9f6e": {
-+    "phase": "discovery"
-+  },
-+  "484c8545-5032-4d6f-a27d-b31f285d6993": {
-+    "phase": "discovery"
-+  }
-+}
-\ No newline at end of file
-
-
-### `commit` — 2026-04-01
-
-diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
-new file mode 100644
-index 0000000..ab0fa5b
---- /dev/null
-+++ b/workspace/aicli/_system/project_state.json
-@@ -0,0 +1,171 @@
-+{
-+  "project": "aicli",
-+  "description": "Shared AI memory platform \u2014 gives every LLM (Claude CLI, aicli CLI, Cursor, web UI) identical project memory, billing, multi-LLM workflows, and a unified knowledge graph across all tools.",
-+  "last_updated": "2026-03-09",
-+  "version": "2.1.0",
-+  "tech_stack": {
-+    "cli": "Python 3.12 + prompt_toolkit + rich",
-+    "backend": "FastAPI + uvicorn + python-jose + bcrypt + psycopg2",
-+    "frontend": "Vanilla JS (no framework, no bundler) + Electron s

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/aicli/copilot.md b/workspace/aicli/_system/aicli/copilot.md
index 02ead5b..874adc9 100644
--- a/workspace/aicli/_system/aicli/copilot.md
+++ b/workspace/aicli/_system/aicli/copilot.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-01 08:46 UTC
+> Generated by aicli 2026-04-01 08:56 UTC
 
 # aicli — Shared AI Memory Platform
 


## AI Synthesis

**2026-04-01** `memory_generation` — Automated memory synthesis pipeline completing 5-file generation (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from unified mem_ai_project_facts and mem_ai_work_items tables with timestamp tracking.
**2026-03-14** `schema_consolidation` — Unified database schema finalized: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features replacing per-project event tables and deprecated structures.
**2026-03-14** `persistence_fix` — Tag disappearance on session switch root-caused to cache invalidation during DB reload; resolved by fixing reload logic and ensuring mem_ai_tags_relations persistence with row ID linking.
**2026-03-14** `documentation_alignment` — project_state.json and rules.md updated to reflect unified mem_ai_* table naming; removed conflicting legacy database_schema field.
**2026-03-09** `backend_startup_race` — AiCli project unselectable on first load despite appearing in Recent; fixed via retry logic for empty project list handling during backend initialization.
**2026-03-09** `schema_migration` — mem_ai_tags_relations DDL corrected; database migrations applied and persistence validated across session switches with proper tag column schema.