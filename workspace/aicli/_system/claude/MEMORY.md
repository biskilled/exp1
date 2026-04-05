# Project Memory — aicli
_Generated: 2026-04-05 23:02 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

**aicli** is a shared AI memory platform combining a Python CLI + FastAPI backend + Electron desktop UI to capture, organize, and synthesize project knowledge using Claude AI, semantic PostgreSQL search, and workflow automation. Currently at v2.2.0, the project has consolidated UI components (Planner tab, Chat with tags), fixed critical session ordering and persistence bugs, and deployed inline commit tracking with tag deduplication across all views.

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
- **storage_primary**: PostgreSQL 15+
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization + auto-tag suggestions
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
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

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Session phase persistence with red ⚠ badge for missing phase; tag suggestions marked distinctly (separate color) and auto-saved via _acceptSuggestedTag
- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↗ link) showing only that prompt's commits
- Backend: FastAPI + uvicorn; routers/ for API endpoints, core/ for infrastructure, data/ (dl_ prefix) for access, agents/ for tools and MCP
- Unified Planner tab: single tags view with category/status/properties (active/inactive, short description, created date); tag management centralized from Chat
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash start_backend.sh + npm run dev
- Backend startup race condition fixed: retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention

## In Progress

- Session ordering by created_at verified: maintains chronological list and prevents phase/tag updates from reordering sessions
- Phase persistence enhanced: loads from database on init, PATCH /chat/sessions/{id}/tags saves phase, red ⚠ badge for missing phase across UI/CLI/workflow
- Commit-per-prompt inline display deployed: replaced session-level commit strip with inline commits at bottom of each prompt entry (accent left-border, hash ↗ link)
- Tag deduplication and cross-view sync verified: 149 total tags (0 duplicates); removal via ✕ buttons propagates across Chat/History/Commits simultaneously
- AI suggestion auto-save with tag management: suggestions create tags in proper category via _acceptSuggestedTag; marked distinctly with separate color; appear immediately in Planner
- Planner tab unified redesign completed: consolidated into single tags view with category, active/inactive status, short description, created date

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index a2ad8b8..99db52f 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -50,7 +50,7 @@
     "Data persistence: load_once_on_access, update_on_save pattern; tags in mem_ai_tags_relations with row ID linking and suggested/user-created distinction",
     "Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI",
     "Session ordering by created_at (not updated_at) to prevent tag/phase updates from reordering session list",
-    "Unified UI: Planner tab consolidates all tag management (single tags view with category/status/properties); Chat (+) for tag selection with category filtering",
+    "Unified Planner tab: single tags view with category/status/properties (active/inactive, short description, created date); tag management centralized from Chat (+) with category filtering",
     "Tag suggestions marked distinctly (separate color/mark) and auto-saved via _acceptSuggestedTag; phase persistence with red \u26a0 badge for missing phase",
     "Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash \u2197 link) showing only that prompt's commits",
     "Backend: FastAPI + uvicorn; routers/ for API, core/ for infrastructure, data/ (dl_ prefix) for access, agents/ for tools and MCP",
@@ -83,10 +83,10 @@
     "config.py reads ~/.aicli/config.json for WORKSPACE_DIR at startup"
   ],
   "in_progress": [
-    "Session ordering refactored: sessions now order by created_at instead of updated_at to maintain chronological list and prevent phase/tag updates from reordering",
+    "Session ordering by created_at implemented to maintain chronological list and prevent phase/tag updates from reordering sessions",
     "Phase persistence enhanced: loads from database on init, PATCH /chat/sessions/{id}/tags saves phase, red \u26a0 badge for missing phase across UI/CLI/workflow",
     "Commit-per-prompt inline display completed: replaced session-level commit strip with inline commits at bottom of each prompt entry (accent left-border, hash \u2197 link)",
-    "Tag deduplication and cross-view sync: 149 total tags (0 duplicates); removal via \u2715 buttons propagates across Chat/History/Commits simultaneously",
+    "Tag deduplication and cross-view sync verified: 149 total tags (0 duplicates); removal via \u2715 buttons propagates across Chat/History/Commits simultaneously",
     "AI suggestion auto-save with tag management: suggestions create tags in proper category via _acceptSuggestedTag; marked distinctly with separate color; appear immediately in Planner",
     "Planner tab unified redesign: consolidated into single tags view with category, active/inactive status, short description, created date; removed Feature/Bugs/Tags split"
   ],
@@ -120,7 +120,7 @@
     "cloud": "Railway (Dockerfile + railway.toml)",
     "desktop": "Electron-builder: Mac dmg (arm64+x64), Windows nsis, Linux AppImage+deb"
   },
-  "last_memory_run": "2026-04-05T18:10:33Z",
+  "last_memory_run": "2026-04-05T18:14:46Z",
   "_synthesis_cache": {
     "key_decisions": [
       "Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files",
@@ -133,17 +133,17 @@
       "Data persistence: load_once_on_access, update_on_save pattern; tags in mem_ai_tags_relations with row ID linking and suggested/user-created distinction",
       "Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI",
       "Session ordering by created_at (not updated_at) to prevent tag/phase updates from reordering session list",
-      "Unified UI: Planner tab consolidates all tag management (single tags view with category/status/properties); Chat (+) for tag selection with category filtering",
+  

### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/llm_prompts/gemini_context.md b/workspace/aicli/_system/llm_prompts/gemini_context.md
new file mode 100644
index 0000000..60b4bc9
--- /dev/null
+++ b/workspace/aicli/_system/llm_prompts/gemini_context.md
@@ -0,0 +1,44 @@
+# Project Context: aicli
+# Generated: 2026-04-05 18:22 UTC
+
+## Project Facts
+
+### General
+
+- auth_pattern: login_as_first_level_hierarchy
+- backend_startup_race_condition_fix: retry_logic_handles_empty_project_list_on_first_load
+- data_model_hierarchy: clients_contain_multiple_users
+- data_persistence_issue: tags_disappear_on_session_switch
+- db_engine: SQL
+- db_schema_method_convention: _ensure_shared_schema_replaces_ensure_project_schema
+- deployment_target: Claude_CLI_and_LLM_platforms
+- email_verification_integration: incremental_enhancement_to_existing_signin_register_forms
+- mcp_integration: embedding_and_data_retrieval_for_work_item_management
+- memory_endpoint_template_variable_scoping: code_dir_variable_fixed_at_line_1120
+- memory_management_pattern: load_once_on_access_update_on_save
+- pending_implementation: memory_items_and_project_facts_table_population
+- pending_issues: project_visibility_bug_active_project_not_displaying
+- performance_optimization: redundant_SQL_calls_eliminated
+- pipeline/auth: Acceptance criteria:
+# PM Analysis: Email Verification Feature
+
+---
+
+## Context Summary
+
+The tagged context reveals this work item is an **incremental enhancement** to an existing authentication system. Sign In and Create Account forms are already live and functional. The prior PM analysis identified email verification as the missing layer—the system currently accepts any email without confirming ownership. The analys
+
+Reviewer: ```json
+{
+  "passed": false,
+  "score": 4,
+  "issues": [
+    "Implementation is incomplete — cuts off mid-file in EmailService.ts without finishing AWS SES client setup, email template loading, or the
+- sql_performance_strategy: redundant_calls_eliminated_load_once_pattern
+- stale_code_removed: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
+- tagging_system: nested_hierarchy_beyond_2_levels
+- tagging_system_hierarchy: nested_hierarchy_beyond_2_levels_approved
+- ui_action_menu_pattern: 3_dot_menu_for_action_visibility
+- ui_library: 3_dot_menu_pattern
+- unimplemented_features: memory_items_and_project_facts_tables_not_updating
+- unresolved_issues: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition


### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/llm_prompts/full.md b/workspace/aicli/_system/llm_prompts/full.md
new file mode 100644
index 0000000..ac2ff6b
--- /dev/null
+++ b/workspace/aicli/_system/llm_prompts/full.md
@@ -0,0 +1,43 @@
+You are a senior developer working on **aicli**.
+Respect all project facts below. Never contradict them unless explicitly asked.
+When working on a specific feature, ask for its snapshot before making decisions.
+
+## Project Notes
+
+- **auth_pattern**: login_as_first_level_hierarchy
+- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
+- **data_model_hierarchy**: clients_contain_multiple_users
+- **data_persistence_issue**: tags_disappear_on_session_switch
+- **db_engine**: SQL
+- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
+- **deployment_target**: Claude_CLI_and_LLM_platforms
+- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
+- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
+- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
+- **memory_management_pattern**: load_once_on_access_update_on_save
+- **pending_implementation**: memory_items_and_project_facts_table_population
+- **pending_issues**: project_visibility_bug_active_project_not_displaying
+- **performance_optimization**: redundant_SQL_calls_eliminated
+- **pipeline/auth**: Acceptance criteria:
+# PM Analysis: Email Verification Feature
+
+---
+
+## Context Summary
+
+The tagged context reveals this work item is an **incremental enhancement** to an existing authentication system. Sign In and Create Account forms are already live and functional. The prior PM analysis identified email verification as the missing layer—the system currently accepts any email without confirming ownership. The analys
+
+Reviewer: ```json
+{
+  "passed": false,
+  "score": 4,
+  "issues": [
+    "Implementation is incomplete — cuts off mid-file in EmailService.ts without finishing AWS SES client setup, email template loading, or the
+- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
+- **stale_code_removed**: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
+- **tagging_system**: nested_hierarchy_beyond_2_levels
+- **tagging_system_hierarchy**: nested_hierarchy_beyond_2_levels_approved
+- **ui_action_menu_pattern**: 3_dot_menu_for_action_visibility
+- **ui_library**: 3_dot_menu_pattern
+- **unimplemented_features**: memory_items_and_project_facts_tables_not_updating
+- **unresolved_issues**: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition


### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/llm_prompts/compact.md b/workspace/aicli/_system/llm_prompts/compact.md
new file mode 100644
index 0000000..7c64f6b
--- /dev/null
+++ b/workspace/aicli/_system/llm_prompts/compact.md
@@ -0,0 +1,3 @@
+You are a senior developer working on **aicli**.
+Respect all project facts below. Never contradict them unless explicitly asked.
+When working on a specific feature, ask for its snapshot before making decisions.


### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index f2cc779..ff02e29 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-05T18:14:20Z",
+  "last_updated": "2026-04-05T18:23:16Z",
   "last_session_id": "c9289bdc-baf2-462e-a6ce-a1972bd529aa",
-  "last_session_ts": "2026-04-05T18:14:20Z",
-  "session_count": 355,
+  "last_session_ts": "2026-04-05T18:23:16Z",
+  "session_count": 356,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index da83136..8cf5059 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,63 +1 @@
-# aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-05 18:10 UTC
-
-# aicli — Shared AI Memory Platform
-
-_Last updated: 2026-03-14 | Version 2.2.0_
-
----
-
-## Tech Stack
-
-- **cli**: Python 3.12 + prompt_toolkit + rich
-- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
-- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
-- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
-- **storage_primary**: PostgreSQL 15+
-- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
-- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
-- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
-- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
-- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
-- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
-- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization + auto-tag suggestions
-- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
-- **mcp**: Stdio MCP server with 12+ tools
-- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
-- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
-- **config_management**: config.py + YAML pipelines + pyproject.toml
-- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
-- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
-- **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
-- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
-- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
-- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
-- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
-- **database**: PostgreSQL 15+
-- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
-- **database_version**: PostgreSQL 15+
-- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
-- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
-- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
-- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
-- **deployment_cloud**: Railway (Dockerfile + railway.toml)
-- **deployme

## AI Synthesis

**2026-04-05** `project_state.json` — Session ordering refactored to use created_at instead of updated_at, preventing tag/phase updates from reordering chronological list; phase persistence now loads from database on init with red ⚠ badge for missing phases. **2026-04-05** `project_state.json` — Commit-per-prompt inline display completed: replaced session-level commit strip with inline commits at bottom of each prompt entry (accent left-border, hash ↗ link showing only that prompt's commits). **2026-04-05** `project_state.json` — Tag deduplication verified across system: 149 total tags with 0 duplicates; removal via ✕ buttons now propagates across Chat/History/Commits views simultaneously. **2026-04-05** `project_state.json` — AI suggestion auto-save with tag management: suggestions create tags in proper category via _acceptSuggestedTag, marked distinctly with separate color, appear immediately in Planner tab. **2026-04-05** `project_state.json` — Planner tab unified redesign: consolidated into single tags view with category, active/inactive status, short description, and created date; removed Feature/Bugs/Tags split. **Earlier** `project_state.json` — Backend startup race condition fixed with retry_logic_handles_empty_project_list_on_first_load pattern; _ensure_shared_schema convention replaces ensure_project_schema for robust schema initialization.