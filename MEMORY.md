# Project Memory — aicli
_Generated: 2026-04-07 01:11 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI backend (FastAPI + PostgreSQL + pgvector), Electron desktop UI (Vanilla JS + Cytoscape DAG visualization), and multi-provider LLM support (Claude/OpenAI/DeepSeek/Gemini/Grok) for semantic tagging, workflow automation, and collaborative memory synthesis. Currently stabilizing work item drag-drop UI, dual-status tracking, and memory population after recent schema consolidation around unified mem_ai_* tables.

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
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb); local bash/npm
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
- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
- Tag filtering in work item list: ai_category must match tag's category, not work item's own category (fixed regression in _loadTagLinkedWorkItems)
- Session-level UI consolidation: Planner tab unified for all tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created
- Work item persistence across navigation: drag-drop linkage saves correctly to DB; reload of project/page maintains linked work items in list display
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash/npm dev

## In Progress

- Work item UI drag-and-drop refinement: fixing hover state propagation (only target tag highlights) and ensuring dropped work items persist in correct parent and disappear from source list after reload
- Work item column alignment and source_session_id semantics: investigating column sizing consistency and clarifying source_session_id usage in work_items table schema
- Frontend reference error resolution: fixing _plannerSelectAiSubtype undefined error in routers.route_logs; ensuring all planner helper functions are properly scoped and exported
- Work item dual-status UI completion: integrating status_user dropdown + status_ai badge with separate color indicators throughout table and item drawer views
- Work item embedding strategy for cross-matching: unified embedding space via code_summary + requirements + summary fields for cosine-similarity matching with planner_tags
- Memory items and system state refresh: running /memory endpoint to update all memory_items with latest session data and ensure memory tables are properly populated across workspace

## Active Features / Bugs / Tasks

### Ai_suggestion

- **test123** `[open]`

### Bug

- **hooks** `[open]`

### Doc_type

- **retrospective** `[open]`
- **Test** `[open]`
- **architecture-decision** `[open]`
- **customer-meeting** `[open]`
- **high-level-design** `[open]`
- **low-level-design** `[open]`

### Feature

- **pagination**
- **test-picker-feature** `[open]`
- **graph-workflow** `[open]`
- **billing** `[open]`
- **embeddings** `[open]`
- **tagging** `[open]`
- **mcp** `[open]`
- **workflow-runner** `[open]`
- **shared-memory** `[open]`
- **UI** `[open]`
- **auth** `[open]`
- **dropbox** `[open]`

### Phase

- **development** `[open]`
- **discovery** `[open]`
- **prod** `[open]`

### Task

- **memory** `[open]`
- **implement-projects-tab** `[open]`

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-06

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 3044ebd..5f65c9c 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-06 18:14 UTC
+> Generated by aicli 2026-04-06 22:55 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -56,8 +56,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
 - Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
-- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with mem_mrr_commits table
-- Dual-hook architecture: hook-response saves LLM responses to mem_mrr_prompts.response; session-summary hook consolidates prompt/response pairs for synthesis
-- Memory layer event-based triggering with differentiated process_item/messages handling for core memory functionality activation
-- Backend startup race condition: retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
-- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
\ No newline at end of file
+- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
+- Tag filtering in work item list: ai_category must match tag's category, not work item's own category (fixed regression in _loadTagLinkedWorkItems)
+- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash start_backend.sh + npm run dev
+- Session-level UI consolidation: Planner tab unified for all tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created
+- Work item persistence across navigation: drag-drop linkage saves correctly to DB; reload of project/page maintains linked work items in list display
\ No newline at end of file


### `commit` — 2026-04-06

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index 2c8d399..40da97b 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-06 18:14 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-06 22:55 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -56,8 +56,16 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
 - Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
-- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with mem_mrr_commits table
-- Dual-hook architecture: hook-response saves LLM responses to mem_mrr_prompts.response; session-summary hook consolidates prompt/response pairs for synthesis
-- Memory layer event-based triggering with differentiated process_item/messages handling for core memory functionality activation
-- Backend startup race condition: retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
-- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
+- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
+- Tag filtering in work item list: ai_category must match tag's category, not work item's own category (fixed regression in _loadTagLinkedWorkItems)
+- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash start_backend.sh + npm run dev
+- Session-level UI consolidation: Planner tab unified for all tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created
+- Work item persistence across navigation: drag-drop linkage saves correctly to DB; reload of project/page maintains linked work items in list display
+
+## Recent Context (last 5 changes)
+
+- [2026-04-06] I would like to make sure columns are aligned in work_items. What is source_session_id usaed from in work_items? Also th
+- [2026-04-06] I do see an issue - Uncaught ReferenceError: _plannerSelectAiSubtype is not defined in ERROR    | routers.route_logs    
+- [2026-04-06] is it possilbe to actual move the work_item (drag) and drop that under the item (so work_item is removed from the lower 
+- [2026-04-06] There are some issue - when I drag all tabs that I hoover on top are marked (not just the tag I wanted to drop of). also
+- [2026-04-06] Looks better, still when I drag work_item - I do not see that droped under the item (now also when I try to go out and c
\ No newline at end of file


### `commit` — 2026-04-06

diff --git a/.ai/rules.md b/.ai/rules.md
index 2c8d399..40da97b 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-06 18:14 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-06 22:55 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -56,8 +56,16 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
 - Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
-- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with mem_mrr_commits table
-- Dual-hook architecture: hook-response saves LLM responses to mem_mrr_prompts.response; session-summary hook consolidates prompt/response pairs for synthesis
-- Memory layer event-based triggering with differentiated process_item/messages handling for core memory functionality activation
-- Backend startup race condition: retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
-- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
+- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
+- Tag filtering in work item list: ai_category must match tag's category, not work item's own category (fixed regression in _loadTagLinkedWorkItems)
+- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash start_backend.sh + npm run dev
+- Session-level UI consolidation: Planner tab unified for all tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created
+- Work item persistence across navigation: drag-drop linkage saves correctly to DB; reload of project/page maintains linked work items in list display
+
+## Recent Context (last 5 changes)
+
+- [2026-04-06] I would like to make sure columns are aligned in work_items. What is source_session_id usaed from in work_items? Also th
+- [2026-04-06] I do see an issue - Uncaught ReferenceError: _plannerSelectAiSubtype is not defined in ERROR    | routers.route_logs    
+- [2026-04-06] is it possilbe to actual move the work_item (drag) and drop that under the item (so work_item is removed from the lower 
+- [2026-04-06] There are some issue - when I drag all tabs that I hoover on top are marked (not just the tag I wanted to drop of). also
+- [2026-04-06] Looks better, still when I drag work_item - I do not see that droped under the item (now also when I try to go out and c
\ No newline at end of file


### `commit` — 2026-04-06

Commit: docs: update system context and memory after claude session 04974a99
Hash: d760cb38
Files changed (20):
  - .ai/rules.md
  - .cursor/rules/aicli.mdrules
  - .github/copilot-instructions.md
  - CLAUDE.md
  - MEMORY.md
  - ui/frontend/views/entities.js
  - workspace/aicli/PROJECT.md
  - workspace/aicli/_system/CLAUDE.md
  - workspace/aicli/_system/CONTEXT.md
  - workspace/aicli/_system/aicli/context.md
  - workspace/aicli/_system/aicli/copilot.md
  - workspace/aicli/_system/claude/CLAUDE.md
  - workspace/aicli/_system/claude/MEMORY.md
  - workspace/aicli/_system/commit_log.jsonl
  - workspace/aicli/_system/cursor/rules.md
  - workspace/aicli/_system/dev_runtime_state.json
  - workspace/aicli/_system/llm_prompts/compact.md
  - workspace/aicli/_system/llm_prompts/full.md
  - workspace/aicli/_system/llm_prompts/gemini_context.md
  - workspace/aicli/_system/project_state.json

### `commit` — 2026-04-07

diff --git a/.ai/rules.md b/.ai/rules.md
index 40da97b..e9d7895 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-06 22:55 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-06 23:06 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -64,8 +64,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-06] I would like to make sure columns are aligned in work_items. What is source_session_id usaed from in work_items? Also th
 - [2026-04-06] I do see an issue - Uncaught ReferenceError: _plannerSelectAiSubtype is not defined in ERROR    | routers.route_logs    
 - [2026-04-06] is it possilbe to actual move the work_item (drag) and drop that under the item (so work_item is removed from the lower 
 - [2026-04-06] There are some issue - when I drag all tabs that I hoover on top are marked (not just the tag I wanted to drop of). also
-- [2026-04-06] Looks better, still when I drag work_item - I do not see that droped under the item (now also when I try to go out and c
\ No newline at end of file
+- [2026-04-06] Looks better, still when I drag work_item - I do not see that droped under the item (now also when I try to go out and c
+- [2026-04-06] I would like to be able to move work_item back to work_item or to another items. also merge - merge can happend only to 
\ No newline at end of file


### `commit` — 2026-04-07

Commit: docs: update system prompts and memory after claude session
Hash: 46b5b785
Files changed (24):
  - .ai/rules.md
  - .cursor/rules/aicli.mdrules
  - .github/copilot-instructions.md
  - MEMORY.md
  - backend/core/database.py
  - backend/memory/memory_planner.py
  - backend/routers/route_tags.py
  - backend/routers/route_work_items.py
  - ui/frontend/utils/api.js
  - ui/frontend/views/entities.js
  - workspace/_templates/memory/prompts.yaml
  - workspace/aicli/_system/CLAUDE.md
  - workspace/aicli/_system/CONTEXT.md
  - workspace/aicli/_system/aicli/context.md
  - workspace/aicli/_system/aicli/copilot.md
  - workspace/aicli/_system/claude/CLAUDE.md
  - workspace/aicli/_system/claude/MEMORY.md
  - workspace/aicli/_system/commit_log.jsonl
  - workspace/aicli/_system/cursor/rules.md
  - workspace/aicli/_system/dev_runtime_state.json

## AI Synthesis

**[2026-04-06]** `claude_cli` — Fixed tag filtering regression: ai_category must now match tag's category (not work item's own category) in _loadTagLinkedWorkItems to ensure correct work item associations. **[2026-04-06]** `system` — Unified session-level UI in Planner tab for centralized tag management with single tags view; suggested tags visually distinguished from user-created tags. **[2026-04-06]** `system` — Confirmed work item persistence across navigation: drag-drop linkage properly saves to database; reload maintains linked work items in list display. **[2026-04-06]** `frontend` — Identified _plannerSelectAiSubtype undefined ReferenceError in routers.route_logs; planner helper functions require proper scoping and export. **[2026-04-06]** `ui` — Work item drag-and-drop has hover state propagation issue: all hovered tabs highlight instead of just target tag; needs refinement for better UX. **[2026-04-06]** `schema` — Clarifying source_session_id semantics in work_items table; investigating column alignment consistency for improved UI layout. **[2026-04-06]** `integration` — Work item dual-status UI integration: status_user dropdown + status_ai badge with separate color indicators needed across table and drawer views. **[2026-04-06]** `embeddings` — Work item cross-matching via unified embedding space: code_summary + requirements + summary fields enable cosine-similarity against planner_tags. **[2026-04-07]** `memory` — Initiate /memory endpoint refresh to populate all memory_items with latest session data; ensure memory tables properly reflect project state.