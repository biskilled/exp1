# Project Memory — aicli
_Generated: 2026-04-06 09:50 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform integrating Claude, OpenAI, and other LLM providers with PostgreSQL + pgvector for semantic search, dual-layer memory synthesis, and an Electron desktop UI featuring async DAG workflow visualization. Currently in active development focused on fixing PostgreSQL batch upsert JSONB type casting, completing memory layer implementation (mem_ai_* table population), and comprehensive memory architecture documentation to enable core memory functionality.

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
- **stale_code_removed**: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
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
- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization + auto-tag suggestions
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local bash/npm
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with JSONB UNION batch upsert queries
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + npm run dev

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
- Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling
- Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking
- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↩ link) showing only that prompt's commits
- Feature snapshot consolidation: rename plannet_tags to feature_snapshot and establish unified linkage to work_items and memory structures

## In Progress

- PostgreSQL batch upsert JSONB type casting fix: resolved execute_values error on line 466 where tags || EXCLUDED.tags required explicit ::jsonb cast; UNION query consolidation for commit deduplication across multiple sources
- History display fix: dual-hook architecture ensuring both prompt and LLM response display via hook-response (saves to mem_mrr_prompts.response) and session-summary hooks
- Hook verification and consolidation: confirmed all four background hooks (hook-response, session-summary, memory, auto-detect-bugs) properly defined and triggering correct memory synthesis workflows
- Memory items and project_facts population: enable event-based triggering for core memory functionality with proper differentiated process_item/messages handling
- Copy-to-clipboard functionality: implement text selection and copying capability in history UI for improved usability
- Memory architecture documentation: comprehensive aicli_memory.md covering all layers, mirroring mechanism, event triggers, and processing prompts at each step

## Active Features / Bugs / Tasks

### Ai_suggestion

- **test123** `[open]`

### Bug

- **hooks** `[open]`

### Doc_type

- **architecture-decision** `[open]`
- **customer-meeting** `[open]`
- **Test** `[open]`
- **low-level-design** `[open]`
- **high-level-design** `[open]`
- **retrospective** `[open]`

### Feature

- **UI** `[open]`
- **pagination** `[open]`
- **test-picker-feature** `[open]`
- **graph-workflow** `[open]`
- **billing** `[open]`
- **embeddings** `[open]`
- **tagging** `[open]`
- **mcp** `[open]`
- **workflow-runner** `[open]`
- **shared-memory** `[open]`
- **auth** `[open]`
- **dropbox** `[open]`

### Phase

- **prod** `[open]`
- **development** `[open]`
- **discovery** `[open]`

### Task

- **implement-projects-tab** `[open]`
- **memory** `[open]`

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `prompt_batch: b9e39fae-45bf-482c-a3e9-fa65ed840b6c` — 2026-04-06

The history display was updated to capture both LLM responses and prompts by ensuring the `hook-response` background hook is properly configured to save responses to the database, and all four session-stop hooks (response logging, session summary, memory regeneration, and bug detection) are now synchronized and functional across both template locations.

### `session_summary: b9e39fae-45bf-482c-a3e9-fa65ed840b6c` — 2026-04-06

Summary:
• History view was showing only prompt text instead of full prompt + LLM response • User needs expanded view in history to see complete prompt and response text • User requested ability to copy text from history UI for easier access • History previously displayed both prompt and full LLM response but regressed to showing only prompt

### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index 8ea1253..840ed25 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -49,11 +49,11 @@
     "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel",
     "Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates",
     "Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI",
+    "Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention",
+    "Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev",
     "Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling",
     "Phase persistence with red \u26a0 badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking",
     "Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash \u21a9 link) showing only that prompt's commits",
-    "Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev",
-    "Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention",
     "Feature snapshot consolidation: rename plannet_tags to feature_snapshot and establish unified linkage to work_items and memory structures"
   ],
   "implemented_features": [
@@ -120,7 +120,7 @@
     "cloud": "Railway (Dockerfile + railway.toml)",
     "desktop": "Electron-builder: Mac dmg (arm64+x64), Windows nsis, Linux AppImage+deb"
   },
-  "last_memory_run": "2026-04-06T01:36:35Z",
+  "last_memory_run": "2026-04-06T01:37:27Z",
   "_synthesis_cache": {
     "key_decisions": [
       "Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files",
@@ -132,11 +132,11 @@
       "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel",
       "Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates",
       "Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI",
+      "Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention",
+      "Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev",
       "Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling",
       "Phase persistence with red \u26a0 badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking",
       "Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash \u21a9 link) showing only that prompt's commits",
-      "Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev",
-      "Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention",
       "Feature snapshot consolidation: rename plannet_tags to feature_snapshot and establish unified linkage to work_items and memory structures"
     ],
     "in_progress": [
@@ -161,11 +161,14 @@
       "memory_synthesis": "Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization + auto-tag suggestions",
       "chunking": "Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)",
       "mcp": "Stdio MCP server with 12+ tools",
-      "deployment": "Railway (Dockerfile + railway.toml); Electron-builder; local bash/npm",
-      "database": "PostgreSQL 15+",
-      "build_tooling": "npm 8+ with Electron-builder; Vite dev server"
+      "deployment_cloud": "Railway (Dockerfile + railway.toml)",
+      "deployment_desktop": "Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)",
+      "deployment_local": "bash start_backend.sh + npm run dev",
+      "config_management": "config.py + YAML pipelines + pyproject.toml",
+      "dev_environment": "PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root",
+      "database_version": "PostgreSQL 15+"
     },
-    "project_summary": "aicli is a shared AI memory platform that integrates Claude, OpenAI, and other LLM providers with a PostgreSQL backend, dual-layer memory synthesis, and an Electron desktop UI featuring workflow visualization and semantic search via pgvector embeddings. Currently in active development with focus on memory layer implementation (populate memory_items and project_facts tables), comprehensive memory architecture documentation, and feature snapshot unification to enable core memory functionality.",
-    "memory_digest": "**[2026-04-05]** `development-session` \u2014 Requested comprehensive memory architecture documentation (aicli_memory.md) covering all layers, mirroring mechanism, event triggers, and specific prompts used at each processing step. **[2026-04-05]** `development-session` \u2014 Feature snapshot consolidation: merge plannet_tags into properly named feature_

### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 9523355..b3f5136 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-06 01:35 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-06 01:37 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -55,11 +55,11 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
+- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
+- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
 - Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling
 - Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking
 - Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↩ link) showing only that prompt's commits
-- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
-- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
 - Feature snapshot consolidation: rename plannet_tags to feature_snapshot and establish unified linkage to work_items and memory structures
 
 ## Recent Context (last 5 changes)


### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 7e7f5d8..60f36f8 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -666,3 +666,5 @@
 {"ts": "2026-04-06T01:35:16Z", "action": "commit_push", "source": "claude_cli", "session_id": "b9e39fae-45bf-482c-a3e9-fa65ed840b6c", "hash": "7eb54cee", "message": "docs: update system context and memory files post-session", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "b9e39fae-45bf-482c-a3e9-fa65ed840b6c", "hash": "d54f4027", "message": "chore: remove stale system context and claude config files", "files_count": 55, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-06T01:36:01Z"}
 {"ts": "2026-04-06T01:35:52Z", "action": "commit_push", "source": "claude_cli", "session_id": "b9e39fae-45bf-482c-a3e9-fa65ed840b6c", "hash": "d54f4027", "message": "chore: remove stale system context and claude config files", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "b9e39fae-45bf-482c-a3e9-fa65ed840b6c", "hash": "0c856f94", "message": "docs: update memory and rules after claude cli session b9e39fae", "files_count": 58, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-06T01:37:12Z"}
+{"ts": "2026-04-06T01:36:10Z", "action": "commit_push", "source": "claude_cli", "session_id": "b9e39fae-45bf-482c-a3e9-fa65ed840b6c", "hash": "0c856f94", "message": "docs: update memory and rules after claude cli session b9e39fae", "pushed": true, "push_error": ""}


### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index 4059973..af290a5 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-06 01:35 UTC by aicli /memory_
+_Generated: 2026-04-06 01:37 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform that integrates Claude, OpenAI, and other LLM providers with a PostgreSQL backend, dual-layer memory synthesis, and an Electron desktop UI featuring workflow visualization and semantic search via pgvector embeddings. Currently in active development with focus on memory layer implementation (populate memory_items and project_facts tables), comprehensive memory architecture documentation, and feature snapshot unification to enable core memory functionality.
+aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to enable multi-user project collaboration with semantic memory synthesis, workflow automation, and LLM-powered decision support. The system consolidates project events, code analysis, and work items into unified PostgreSQL tables with pgvector embeddings, while an async DAG workflow engine orchestrates complex multi-step processes. Current development focuses on completing memory layer table population, documenting memory architecture, and unifying feature snapshots with work item relationships.
 
 ## Project Facts
 
@@ -95,11 +95,11 @@ Reviewer: ```json
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
+- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
+- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
 - Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling
 - Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking
 - Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↩ link) showing only that prompt's commits
-- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
-- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
 - Feature snapshot consolidation: rename plannet_tags to feature_snapshot and establish unified linkage to work_items and memory structures
 
 ## In Progress
@@ -272,4 +272,4 @@ Requested comprehensive `aicli_memory.md` documentation including:
 
 ## AI Synthesis
 
-**[2026-04-05]** `development-session` — Requested comprehensive memory architecture documentation (aicli_memory.md) covering all layers, mirroring mechanism, event triggers, and specific prompts used at each processing step. **[2026-04-05]** `development-session` — Feature snapshot consolidation: merge plannet_tags into properly named feature_snapshot structure with complete work_item relationship mapping and unified linkage. **[2026-04-05]** `development-session` — LLM model identifier visibility: expose model identifier as visible tag in UI interface for transparency and tracking across sessions. **[2026-03-18]** `memory-summary` — Identified critical memory mechanism gap: memory_items and project_facts tables are not being updated as designed; needs implementation to enable proper memory functionality. **[2026-03-18]** `bug-fix` — Fixed backend startup race condition via retry_logic_handles_empty_project_list_on_first_load in _continueToApp(). **[2026-03-18]** `bug-fix` — Fixed CLAUDE.md memory endpoint error by resolving undefined code_dir variable at line 1120. **[2026-03-18]** `bug-fix` — Fixed _Database attribute error by removing stale db.ensure_project_schema() call from main.py. **[2026-03-18]** `architecture` — Clarified data model structure: confirmed users are nested under clients (one client → multiple users) with login_as_first_level_hierarchy pattern. **[2026-03-18]** `ui-fix` — Fixed project visibility issue: AiCli project now displays correctly in project list (not just Recent), addressing missing current project indicator. **[2026-02-xx]** `architecture-decision` — _ensure_shared_schema replaces ensure_project_schema convention for database initialization consistency.
\ No newline at end of file
+**[2026-04-05]** `session_request` — Comprehensive memory architecture documentation requested for aicli_memory.md covering all memory layers, mirroring mechanisms, event triggers, and specific prompts at each processing step to clarify data flow and work_item linkage relationships. **[2026-04-05]** `feature_request` — LLM model identifier visibility enhancement to expose model identifier as visible tag in UI interface for transparency and cross-session tracking. **[2026-04-05]** `consolidation` — Feature snapshot unification approved: merge plannet_tags into properly named feature_snapshot structure with complete work_item relationship mapping across database and API layers. **[2026-03-18]** `bug_fix` — Backend startup resilience improved by adding retry logic in _continueToApp() to handle race condition when projects list returns empty on first load. **[2026-03-18]** `bug_fix` — Fixed 

## AI Synthesis

**[2026-04-06]** `claude_cli` — Fixed critical PostgreSQL batch upsert bug: JSONB type casting required explicit `::jsonb` cast in `tags || EXCLUDED.tags` operator to resolve execute_values error on line 466 in route_history. **[2026-04-05]** `development-session` — History display verified to capture both LLM responses and prompts via hook-response background hook saving to mem_mrr_prompts.response; all four session-stop hooks (response logging, session summary, memory regeneration, bug detection) now synchronized. **[2026-04-05]** `development-session` — Comprehensive memory architecture documentation (aicli_memory.md) requested covering all synthesis layers, event-trigger mirroring mechanism, and specific LLM prompts at each processing step. **[2026-04-05]** `development-session` — Feature snapshot consolidation: merge plannet_tags into feature_snapshot with unified linkage to work_items and memory structures to enable core memory functionality. **[2026-04-05]** `development-session` — Copy-to-clipboard functionality requested for history UI to allow text selection and copying of prompts/responses for improved user experience. **[2026-04-04]** `development-session` — Memory items and project_facts table population marked as pending implementation; event-based triggering with differentiated process_item/messages handling required to complete memory layer.