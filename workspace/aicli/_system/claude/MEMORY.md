# Project Memory — aicli
_Generated: 2026-04-06 12:22 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform integrating Claude, OpenAI, and other LLM providers with PostgreSQL + pgvector for semantic search, dual-layer memory synthesis via Claude Haiku, and an Electron desktop UI featuring async DAG workflow visualization. Currently in active development focused on fixing PostgreSQL batch upsert operations, completing memory layer implementation via event-based table population, and comprehensive memory architecture documentation to enable core memory functionality.

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
- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) + JSONB UNION batch upsert
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
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) with JSONB UNION batch upsert queries
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
- PostgreSQL batch upsert with explicit ::jsonb casting for tags field to prevent duplicate row insertion on ON CONFLICT DO UPDATE
- Backend startup race condition: retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
- Commit deduplication by hash with UNION consolidation across multiple sources; commits linked per-prompt with inline display (accent left-border)
- Dual-hook architecture: hook-response saves LLM responses to mem_mrr_prompts.response; session-summary hook consolidates prompt/response pairs for synthesis
- Memory layer event-based triggering with differentiated process_item/messages handling for core memory functionality activation

## In Progress

- PostgreSQL batch upsert JSONB type casting: resolved execute_values error via explicit ::jsonb casting for tags field; commit deduplication via seen dict to prevent ON CONFLICT DO UPDATE processing same hash twice
- Commit sync and deduplication: /history/commits/sync endpoint imports unique commit hashes with proper prompt linkage; commit message truncation fixed to support full metadata display
- History display dual-hook architecture verification: hook-response saves LLM responses to mem_mrr_prompts.response; session-summary hook consolidates prompt/response pairs for synthesis activation
- Memory items and project_facts table population: enable event-based triggering with differentiated process_item/messages handling for core memory functionality activation
- MEMORY.md and aicli_memory.md documentation gap: tables in MEMORY.md updated to reflect current schema (mem_ai_* tables); comprehensive memory architecture documentation covering all layers, mirroring mechanisms, event triggers, and processing prompts
- Copy-to-clipboard functionality: text selection and copying capability in history UI for improved usability and better content accessibility

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

### `commit` — 2026-04-06

diff --git a/backend/routers/route_history.py b/backend/routers/route_history.py
index 4bd30ac..da8f333 100644
--- a/backend/routers/route_history.py
+++ b/backend/routers/route_history.py
@@ -453,6 +453,15 @@ async def sync_commits(project: str | None = Query(None)):
     if not rows:
         return {"imported": 0, "project": p}
 
+    # Deduplicate by commit_hash (index 1) — commit_log.jsonl may have the same hash
+    # multiple times (e.g. retry pushes). Keep the last occurrence per hash so the
+    # most-recent session_id / source wins. PostgreSQL ON CONFLICT DO UPDATE cannot
+    # process the same conflict-target row twice in a single batch.
+    seen: dict[str, tuple] = {}
+    for row in rows:
+        seen[row[1]] = row
+    rows = list(seen.values())
+
     _SQL_BATCH_UPSERT = """
         INSERT INTO mem_mrr_commits
             (project_id, commit_hash, commit_msg, session_id, committed_at, tags)


### `commit` — 2026-04-06

diff --git a/MEMORY.md b/MEMORY.md
index 239a71a..2526e88 100644
--- a/MEMORY.md
+++ b/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-06 02:25 UTC by aicli /memory_
+_Generated: 2026-04-06 09:50 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform integrating Claude, OpenAI, and other LLM providers with a PostgreSQL backend featuring dual-layer memory synthesis via Claude Haiku, semantic search using pgvector embeddings, and an Electron desktop UI with workflow visualization via Cytoscape.js. The project recently resolved history display issues by verifying dual-hook architecture (hook-response for LLM responses, session-summary for synthesis), with current focus on comprehensive memory architecture documentation and enabling memory_items/project_facts table population to activate core memory functionality.
+aicli is a shared AI memory platform integrating Claude, OpenAI, and other LLM providers with PostgreSQL + pgvector for semantic search, dual-layer memory synthesis, and an Electron desktop UI featuring async DAG workflow visualization. Currently in active development focused on fixing PostgreSQL batch upsert JSONB type casting, completing memory layer implementation (mem_ai_* table population), and comprehensive memory architecture documentation to enable core memory functionality.
 
 ## Project Facts
 
@@ -73,7 +73,7 @@ Reviewer: ```json
 - **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
 - **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
-- **database**: PostgreSQL 15+
+- **database**: PostgreSQL 15+ with JSONB UNION batch upsert queries
 - **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
 - **database_version**: PostgreSQL 15+
 - **build_tooling**: npm 8+ with Electron-builder; Vite dev server
@@ -104,12 +104,12 @@ Reviewer: ```json
 
 ## In Progress
 
-- History display fix: resolved dual-hook architecture ensuring both prompt and LLM response display in history panel via hook-response (saves to mem_mrr_prompts.response) and session-summary hooks
-- Hook verification and consolidation: confirmed all four background hooks (hook-response, session-summary, memory, auto-detect-bugs) are properly defined and triggering correct memory synthesis workflows
-- UI history panel enhancement: expanded prompt/LLM response visibility to show full text instead of truncated summaries in history display
-- Memory items and project_facts population: prepare update logic to enable proper memory functionality as designed with event-based triggering
-- Copy-to-clipboard functionality: implement text selection and copying capability in history UI interface for better usability
-- Memory architecture documentation: comprehensive aicli_memory.md covering all layers, mirroring mechanism, event triggers, and specific prompts at each processing step
+- PostgreSQL batch upsert JSONB type casting fix: resolved execute_values error on line 466 where tags || EXCLUDED.tags required explicit ::jsonb cast; UNION query consolidation for commit deduplication across multiple sources
+- History display fix: dual-hook architecture ensuring both prompt and LLM response display via hook-response (saves to mem_mrr_prompts.response) and session-summary hooks
+- Hook verification and consolidation: confirmed all four background hooks (hook-response, session-summary, memory, auto-detect-bugs) properly defined and triggering correct memory synthesis workflows
+- Memory items and project_facts population: enable event-based triggering for core memory functionality with proper differentiated process_item/messages handling
+- Copy-to-clipboard functionality: implement text selection and copying capability in history UI for improved usability
+- Memory architecture documentation: comprehensive aicli_memory.md covering all layers, mirroring mechanism, event triggers, and processing prompts at each step
 
 ## Active Features / Bugs / Tasks
 
@@ -160,6 +160,15 @@ Reviewer: ```json
 
 > Distilled summaries (Trycycle-reviewed). Feature summaries shown first.
 
+### `prompt_batch: b9e39fae-45bf-482c-a3e9-fa65ed840b6c` — 2026-04-06
+
+The history display was updated to capture both LLM responses and prompts by ensuring the `hook-response` background hook is properly configured to save responses to the database, and all four session-stop hooks (response logging, session summary, memory regeneration, and bug detection) are now synchronized and functional across both template locations.
+
+### `session_summary: b9e39fae-45bf-482c-a3e9-fa65ed840b6c` — 2026-04-06
+
+Summary:
+• History view was showing only prompt text instead of full prompt + LLM response • User needs expanded view in history to see complete prompt and response text • User requested ability to copy text from history UI for easier access • History previously displayed both prompt and full LLM response but regressed to showing only prompt
+
 ### `commit` — 2026-04-06
 
 diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
@@ -305,56 +314,6 @@ index 4059973..af290a5 100644
 \ No newline at end of file
 +**[2026-04-05]** `session_request` — Comprehensive memory architecture documentation requested for aicli_memory.md covering all memory layers, mirroring mechanisms, event triggers, and specific prompts at each processing step to clarify data flow and work_item linkage relationships. **[2026-04-05]** `feature_request` — LLM model identifier visibility enhancement to expose model identifier as visible tag in UI interface for transparency and cross-session tracking. **[2026-04-05]

### `commit` — 2026-04-06

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index ed24197..2273fa1 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-06 02:25 UTC
+> Generated by aicli 2026-04-06 09:50 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -33,7 +33,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - billing_storage: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
 - backend_modules: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - dev_environment: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
-- database: PostgreSQL 15+
+- database: PostgreSQL 15+ with JSONB UNION batch upsert queries
 - node_modules_build: npm 8+ with Electron-builder; Vite dev server
 - database_version: PostgreSQL 15+
 - build_tooling: npm 8+ with Electron-builder; Vite dev server


### `commit` — 2026-04-06

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index 3cd5033..fcafc8f 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-06 02:25 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-06 09:50 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -33,7 +33,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
 - **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
-- **database**: PostgreSQL 15+
+- **database**: PostgreSQL 15+ with JSONB UNION batch upsert queries
 - **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
 - **database_version**: PostgreSQL 15+
 - **build_tooling**: npm 8+ with Electron-builder; Vite dev server
@@ -64,8 +64,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-06] I would like to add mng_projects table that will be used for project data. currenlty there all table use project (text) 
 - [2026-04-06] verify prompt after client_id fix
 - [2026-04-06] final verify prompt
 - [2026-04-06] Now I started to see prompts, but I do see in history just small text instead of all prompt and llm response . also can 
-- [2026-04-06] Histroy used to show promp and llm response . I currently see only prompt
\ No newline at end of file
+- [2026-04-06] Histroy used to show promp and llm response . I currently see only prompt
+- [2026-04-06] I have  got the following error -  cur.execute(b''.join(parts)) started  route_history line 470 - execute_values(cur, _S
\ No newline at end of file


### `commit` — 2026-04-06

diff --git a/.ai/rules.md b/.ai/rules.md
index 3cd5033..fcafc8f 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-06 02:25 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-06 09:50 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -33,7 +33,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
 - **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
-- **database**: PostgreSQL 15+
+- **database**: PostgreSQL 15+ with JSONB UNION batch upsert queries
 - **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
 - **database_version**: PostgreSQL 15+
 - **build_tooling**: npm 8+ with Electron-builder; Vite dev server
@@ -64,8 +64,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-06] I would like to add mng_projects table that will be used for project data. currenlty there all table use project (text) 
 - [2026-04-06] verify prompt after client_id fix
 - [2026-04-06] final verify prompt
 - [2026-04-06] Now I started to see prompts, but I do see in history just small text instead of all prompt and llm response . also can 
-- [2026-04-06] Histroy used to show promp and llm response . I currently see only prompt
\ No newline at end of file
+- [2026-04-06] Histroy used to show promp and llm response . I currently see only prompt
+- [2026-04-06] I have  got the following error -  cur.execute(b''.join(parts)) started  route_history line 470 - execute_values(cur, _S
\ No newline at end of file


### `commit` — 2026-04-06

Commit: docs: update AI system context and memory files post-session
Hash: 39500d7a
Files changed (14):
  - .ai/rules.md
  - .cursor/rules/aicli.mdrules
  - .github/copilot-instructions.md
  - MEMORY.md
  - backend/routers/route_history.py
  - workspace/aicli/PROJECT.md
  - workspace/aicli/_system/CONTEXT.md
  - workspace/aicli/_system/aicli/context.md
  - workspace/aicli/_system/aicli/copilot.md
  - workspace/aicli/_system/claude/MEMORY.md
  - workspace/aicli/_system/commit_log.jsonl
  - workspace/aicli/_system/cursor/rules.md
  - workspace/aicli/_system/dev_runtime_state.json
  - workspace/aicli/_system/project_state.json

## AI Synthesis

**[2026-04-06]** `commit` — Commit deduplication logic implemented in /history/commits/sync endpoint using seen dict by commit_hash to prevent PostgreSQL ON CONFLICT DO UPDATE from processing the same row twice in batch upsert; resolves duplicate insertion issues.
**[2026-04-06]** `fix` — PostgreSQL batch upsert JSONB type casting resolved by adding explicit ::jsonb cast to tags || EXCLUDED.tags operation on line 466; enables proper UNION consolidation of commits across multiple sources.
**[2026-04-06]** `memory_synthesis` — History display dual-hook architecture verified: hook-response background hook saves LLM responses to mem_mrr_prompts.response table; session-summary hook consolidates prompt/response pairs for downstream synthesis.
**[2026-04-06]** `documentation` — MEMORY.md updated to reflect current unified table schema (mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features) and comprehensive memory architecture documentation in progress for aicli_memory.md.
**[2026-04-05]** `feature_request` — Memory items and project_facts table population requires event-based triggering with differentiated process_item/messages handling to activate core memory functionality as designed.
**[2026-04-05]** `feature_request` — Copy-to-clipboard functionality needed in history UI to enable text selection and content export for improved user accessibility and session reference capabilities.