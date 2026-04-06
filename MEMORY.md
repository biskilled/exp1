# Project Memory — aicli
_Generated: 2026-04-06 01:32 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI + FastAPI backend with a desktop Electron UI to manage project context, memory synthesis, and workflow automation. It uses PostgreSQL with pgvector for semantic search, multiple LLM providers (Claude/OpenAI/DeepSeek), and an async DAG workflow engine. Current focus is on completing memory layer implementation (database population for memory_items/project_facts), documenting the full memory architecture, and unifying feature snapshot structures with proper work_item linkage.

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
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local bash/npm
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
- Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling
- Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking
- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↪ link) showing only that prompt's commits
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
- Feature snapshot consolidation: rename plannet_tags to feature_snapshot and establish unified linkage to work_items and memory structures

## In Progress

- Memory items and project_facts table population: implement missing update logic to enable proper memory functionality as designed
- Memory architecture documentation: comprehensive aicli_memory.md covering all layers, mirroring mechanism, event triggers, and specific prompts at each step
- LLM model identifier visibility: expose model identifier as visible tag in UI interface for transparency and tracking across sessions
- Feature snapshot unification: merge plannet_tags into properly named feature_snapshot structure with complete work_item relationship mapping
- Work item linking: clarify and implement complete linkage between work_item entities and memory/snapshot layers across database and API
- Memory endpoint variable scoping: verify code_dir variable fix at line 1120 remains stable and document pattern

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

### `memory_item` — 2026-04-05

# Development Session Summary (2026-03-18)

• **Fixed `_Database` attribute error** — removed stale `db.ensure_project_schema()` call from `main.py`

• **Fixed CLAUDE.md memory endpoint error** — resolved undefined `code_dir` variable in line 1120

• **Improved backend startup resilience** — added retry logic in `_continueToApp()` to handle race conditions when projects load returns empty

• **Fixed project visibility issue** — AiCli project now displays correctly in project list (not just Recent), addressing missing current project indicator

• **Clarified data model structure** — confirmed users are nested under clients (one client → multiple users)

• **Identified memory mechanism gap** — `memory_items` and `project_facts` tables are **not being updated** as designed; needs implementation to enable proper memory functionality

### `prompt_batch: 8f29a8d3-13a3-42ed-9219-de7bfe53e3d2` — 2026-04-05

# Development Session Summary (2026-03-18)

• **Fixed `_Database` attribute error** — removed stale `db.ensure_project_schema()` call from `main.py`

• **Fixed CLAUDE.md memory endpoint error** — resolved undefined `code_dir` variable in line 1120

• **Improved backend startup resilience** — added retry logic in `_continueToApp()` to handle race conditions when projects load returns empty

• **Fixed project visibility issue** — AiCli project now displays correctly in project list (not just Recent), addressing missing current project indicator

• **Clarified data model structure** — confirmed users are nested under clients (one client → multiple users)

• **Identified memory mechanism gap** — `memory_items` and `project_facts` tables are **not being updated** as designed; needs implementation to enable proper memory functionality

### `memory_item` — 2026-04-05

# Development Session Summary (2026-04-05)

## UI Enhancement
• Make the LLM model identifier visible as a tag in the UI interface

## Memory Architecture Documentation
Requested comprehensive `aicli_memory.md` documentation including:
- All memory layer descriptions and their responsibilities
- Mirroring layer mechanism and how it propagates state
- Event triggering logic and trigger points for each layer
- Specific prompts used at each processing step
- Integration considerations for work_item and project_fa structures

## Data Structure Consolidation
• **Feature Snapshot Unification**: Merge `plannet_tags` (currently serving as feature snapshot holder) into a properly named `feature_snapshot` structure for semantic clarity
• **Process Item/Messages Trigger**: Consolidate trigger logic in `/memory` pathway to uniformly handle all new items with event-based triggering
• **Work Item Linking**: Establish and clarify proper linkage between work_item entities and memory/snapshot layers (relationship definition incomplete)

## Outstanding Questions
- Exact trigger conditions and data flow for each memory layer step
- How process_item and messages differentiate in the memory layer
- Complete work_item relationship mapping to memory structures

### `prompt_batch: 8b91f9d9-7632-4c3d-a386-d1bf3d48c864` — 2026-04-05

# Development Session Summary (2026-04-05)

## UI Enhancement
• Make the LLM model identifier visible as a tag in the UI interface

## Memory Architecture Documentation
Requested comprehensive `aicli_memory.md` documentation including:
- All memory layer descriptions and their responsibilities
- Mirroring layer mechanism and how it propagates state
- Event triggering logic and trigger points for each layer
- Specific prompts used at each processing step
- Integration considerations for work_item and project_fa structures

## Data Structure Consolidation
• **Feature Snapshot Unification**: Merge `plannet_tags` (currently serving as feature snapshot holder) into a properly named `feature_snapshot` structure for semantic clarity
• **Process Item/Messages Trigger**: Consolidate trigger logic in `/memory` pathway to uniformly handle all new items with event-based triggering
• **Work Item Linking**: Establish and clarify proper linkage between work_item entities and memory/snapshot layers (relationship definition incomplete)

## Outstanding Questions
- Exact trigger conditions and data flow for each memory layer step
- How process_item and messages differentiate in the memory layer
- Complete work_item relationship mapping to memory structures

### `memory_item` — 2026-04-05

# Development Session Summary (Apr 3-5, 2026)

• **Fixed database schema errors**: Removed non-existent `lifecycle` column from `route_entities` (line 359) and `work_item_id` column reference from `route_work_items` (line 351); removed unused `PHASE` column from commits table

• **Tag UI/API issues**: Fixed 422 Unprocessable Entity errors causing "[object object]" display; database schema misalignment prevented tag-prompt/commit associations from persisting

• **Broke tag loading functionality**: After schema fixes, existing tags stopped loading in tag picker and previously attached tags to prompts/commits became inaccessible—requires tag relationship query debugging

• **Commit sync API error**: `/history/commits/sync` endpoint failing at `execute_values()` (route_history line 441) during batch upsert operation—SQL generation issue needs investigation

• **Planned mem_ai_events refactor**: Restructure column order (move `llm_source` after `project`), audit data population sources, and reconcile `tags` (MRR) vs `metadata` (events) columns for consistency across system

### `prompt_batch: 6ffb562b-40dd-4aea-80a1-408ce5204f03` — 2026-04-05

# Development Session Summary (Apr 3-5, 2026)

• **Fixed database schema errors**: Removed non-existent `lifecycle` column from `route_entities` (line 359) and `work_item_id` column reference from `route_work_items` (line 351); removed unused `PHASE` column from commits table

• **Tag UI/API issues**: Fixed 422 Unprocessable Entity errors causing "[object object]" display; database schema misalignment prevented tag-prompt/commit associations from persisting

• **Broke tag loading functionality**: After schema fixes, existing tags stopped loading in tag picker and previously attached tags to prompts/commits became inaccessible—requires tag relationship query debugging

• **Commit sync API error**: `/history/commits/sync` endpoint failing at `execute_values()` (route_history line 441) during batch upsert operation—SQL generation issue needs investigation

• **Planned mem_ai_events refactor**: Restructure column order (move `llm_source` after `project`), audit data population sources, and reconcile `tags` (MRR) vs `metadata` (events) columns for consistency across system

## AI Synthesis

**[2026-04-05]** `session` — Identified critical gap: memory_items and project_facts tables are not being updated; memory synthesis generates 5 files but database integration incomplete.
**[2026-04-05]** `session` — Requested comprehensive aicli_memory.md documentation covering all memory layers, mirroring mechanism, event triggers, and specific prompts used at each processing step.
**[2026-04-05]** `session` — Prioritized LLM model identifier visibility as UI tag for transparency; users need to see which model processed each interaction.
**[2026-04-05]** `session` — Feature snapshot consolidation task: plannet_tags should be renamed to feature_snapshot with proper work_item relationship mapping throughout database schema.
**[2026-04-05]** `session` — Work item linking requires clarification: incomplete relationship mapping between work_item entities and memory/snapshot layers in both DB and API.
**[2026-03-18]** `session` — Removed stale db.ensure_project_schema() call from main.py; fixed undefined code_dir variable in CLAUDE.md memory endpoint (line 1120).
**[2026-03-18]** `session` — Improved backend startup resilience by adding retry logic in _continueToApp() to handle race conditions when projects list returns empty on initialization.
**[2026-03-18]** `session` — Fixed project visibility: AiCli project now displays correctly in project list (not just Recent), addressing missing current project indicator.
**[2026-03-18]** `session` — Clarified data model hierarchy: users are nested under clients (one client → multiple users) per login_as_first_level_hierarchy pattern.
**[2026-03-14]** `config` — Established unified database schema with mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features tables for consolidated event tracking and memory management.