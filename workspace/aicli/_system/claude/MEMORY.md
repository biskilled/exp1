# Project Memory — aicli
_Generated: 2026-04-01 12:37 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python 3.12 CLI (prompt_toolkit + rich), FastAPI backend, PostgreSQL 15+ with pgvector semantic search, and Electron desktop UI (Vanilla JS + xterm.js + Monaco + Cytoscape). It orchestrates multi-LLM workflows (Claude/OpenAI/DeepSeek) through async DAG execution, manages hierarchical user data (Clients → Users), and auto-generates 5 memory synthesis files using Claude Haiku from unified mem_ai_* tables. Current state: unified event schema fully validated, data persistence bugs fixed, backend startup race condition resolved, and UI/documentation aligned.

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

- Memory file auto-generation fully completed: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md regenerated from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
- Unified event table validation: mem_ai_events consolidates embeddings and memory events; removed deprecated event_summary_tags array and metadata columns; schema migration applied
- Data persistence bug fix: tags disappearing on session switch traced to cache invalidation during DB reload; fixed via mem_ai_tags_relations persistence with proper row ID linking
- Backend startup race condition resolved: AiCli project appearing in Recent but unselectable on first load fixed with retry logic for empty project list handling
- Schema documentation cleanup: project_state.json and rules.md updated to reflect mem_ai_* unified naming; removed conflicting legacy database_schema field
- Frontend UI refinement: removed lifecycle button section from entities.js drawer to align with current feature scope and reduce UI clutter

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/CONTEXT.md b/workspace/aicli/_system/CONTEXT.md
index ef6c768..848b034 100644
--- a/workspace/aicli/_system/CONTEXT.md
+++ b/workspace/aicli/_system/CONTEXT.md
@@ -1,14 +1,14 @@
 # Project Context: aicli
 
-> Auto-generated 2026-04-01 08:58 UTC — do not edit manually.
+> Auto-generated 2026-04-01 12:22 UTC — do not edit manually.
 
 ## Quick Stats
 
 - **Provider**: claude
 - **GitHub**: https://github.com/biskilled/exp1.git
 - **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
-- **Sessions**: 324
-- **Last active**: 2026-04-01T08:56:35Z
+- **Sessions**: 325
+- **Last active**: 2026-04-01T09:06:25Z
 - **Last provider**: claude
 - **Version**: 2.1.0
 


### `commit` — 2026-04-01

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index 723dd2f..d01e234 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -881,25 +881,6 @@ function _renderDrawer() {
         </div>
       </div>
 
-      <!-- Lifecycle -->
-      <div>
-        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
-                    letter-spacing:.06em;margin-bottom:0.35rem">Lifecycle</div>
-        <div style="display:flex;gap:5px;flex-wrap:wrap">
-          ${_LIFECYCLE_ORDER.map(lc => {
-            const col = _LIFECYCLE_COLORS[lc] || '#888';
-            const active = (v.lifecycle_status || 'idea') === lc;
-            return `<button
-              onclick="window._plannerCycleLifecycle('${v.id}','${(v.lifecycle_status || 'idea')}')"
-              style="font-size:0.6rem;padding:0.18rem 0.5rem;border-radius:10px;cursor:pointer;
-                     font-family:var(--font);outline:none;white-space:nowrap;border:1px solid ${col};
-                     background:${active ? col : 'transparent'};color:${active ? '#fff' : col};
-                     transition:all 0.12s"
-              title="Advance lifecycle">${lc}</button>`;
-          }).join('')}
-        </div>
-      </div>
-
       <!-- Remarks -->
       <div>
         <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);


### `role` — 2026-04-01

## Minor Issues (note but don't block)
- Style inconsistencies with the existing codebase
- Missing type hints on new code
- Missing docstrings on public functions
- Overly verbose variable names


### `commit` — 2026-04-01

diff --git a/MEMORY.md b/MEMORY.md
index be95dd8..56d5794 100644
--- a/MEMORY.md
+++ b/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-01 08:56 UTC by aicli /memory_
+_Generated: 2026-04-01 09:06 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform that unifies development context across Claude CLI, LLM assistants, and web/desktop UIs through PostgreSQL semantic storage (pgvector), async DAG workflows, and Claude Haiku-powered memory synthesis. The desktop application combines Electron with Vanilla JS, xterm.js, Monaco editor, and Cytoscape.js for workflow visualization and terminal interaction; the backend is FastAPI-based with multi-provider LLM adapter support and MCP server integration. Current focus is stabilizing the unified mem_ai_* event/fact/work-item table schema, resolving data persistence across session switches, and automating memory file generation with proper cache management.
+aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to enable collaborative AI-assisted development with persistent context across multiple LLM tools. It features dual-storage (PostgreSQL 15+ + pgvector for semantic search), unified memory tables, async DAG workflow execution with Cytoscape visualization, and multi-provider LLM support (Claude, OpenAI, DeepSeek, Gemini, Grok) with server-side key management. Current focus is stabilizing schema consistency, validating data persistence across sessions, automating memory synthesis via Claude Haiku dual-layer processing, and resolving backend startup race conditions.
 
 ## Project Facts
 
@@ -115,61 +115,152 @@ Reviewer: ```json
 
 > Distilled summaries (Trycycle-reviewed). Feature summaries shown first.
 
-### `role` — 2026-04-01
-
-## Output
-
-Always output structured JSON with score (1-10), approved (bool), issues (list), summary.
-Score >= 8 → approved. No critical issues → approved regardless of minor issues.
-
-
-### `role` — 2026-04-01
-
-## Minor Issues (note but don't block)
-- Style inconsistencies with the existing codebase
-- Missing type hints on new code
-- Missing docstrings on public functions
-- Overly verbose variable names
-
-
-### `role` — 2026-04-01
-
-## Critical Issues (block approval)
-- Logic bugs that will cause incorrect behaviour
-- Security vulnerabilities (shell injection, path traversal, secret exposure)
-- Unhandled exceptions that will crash the program
-- Breaking changes to existing interfaces
-
-
-### `role` — 2026-04-01
-
-## Your Review Process
-
-1. Read the full code before commenting — understand intent before critiquing
-2. Distinguish critical issues (bugs, security) from minor suggestions (style)
-3. Be specific: "line 45 uses str() instead of Path()" not "use Path objects"
-4. Suggest fixes, not just problems
-5. Acknowledge strengths — good code deserves recognition
-
-
-### `role` — 2026-04-01
-
-# Expert Code Reviewer
-
-You are an expert Python code reviewer with a focus on production-quality software.
-
-
-### `role` — 2026-04-01
-
-## Code Quality Standards
-
-- All functions have type hints
-- All file paths use `Path` objects
-- No raw `print()` in library code — use `console.print()` or `logger`
-- Exception messages tell the user what to do, not just what went wrong
-- New modules get a one-paragraph docstring explaining why they exist
+### `commit` — 2026-04-01
+
+diff --git a/workspace/aicli/_system/session_phases.json b/workspace/aicli/_system/session_phases.json
+index 673bdfb..399a3ce 100644
+--- a/workspace/aicli/_system/session_phases.json
++++ b/workspace/aicli/_system/session_phases.json
+@@ -25,5 +25,14 @@
+   },
+   "484c8545-5032-4d6f-a27d-b31f285d6993": {
+     "phase": "discovery"
++  },
++  "7d89c79f-b6f1-4bd4-a93f-09f2603fd1b1": {
++    "phase": "discovery"
++  },
++  "fa5883c1-6516-4c07-9124-67308c8aa1af": {
++    "phase": "disc

### `role` — 2026-04-01

## Critical Issues (block approval)
- Logic bugs that will cause incorrect behaviour
- Security vulnerabilities (shell injection, path traversal, secret exposure)
- Unhandled exceptions that will crash the program
- Breaking changes to existing interfaces


### `role` — 2026-04-01

## Your Review Process

1. Read the full code before commenting — understand intent before critiquing
2. Distinguish critical issues (bugs, security) from minor suggestions (style)
3. Be specific: "line 45 uses str() instead of Path()" not "use Path objects"
4. Suggest fixes, not just problems
5. Acknowledge strengths — good code deserves recognition


## AI Synthesis

**2026-04-01** `CONTEXT.md` — Session count incremented to 325; last activity timestamp updated to 2026-04-01T09:06:25Z reflecting ongoing development activity. **2026-04-01** `entities.js` — Removed lifecycle button section from entities drawer UI (_LIFECYCLE_ORDER, _LIFECYCLE_COLORS, _plannerCycleLifecycle) to simplify frontend and align with current feature scope. **Recent cycle** `schema` — Completed unified mem_ai_* event table validation; deprecated event_summary_tags array and metadata columns; applied schema migration and validated data persistence across session switches. **Recent cycle** `backend startup` — Resolved race condition where AiCli project appeared in Recent but was unselectable on first load by implementing retry logic for empty project list handling during initialization. **Recent cycle** `tag persistence** — Fixed tags disappearing on session switch via proper row ID linking in mem_ai_tags_relations table and cache invalidation handling during DB reload. **Recent cycle** `documentation` — Updated project_state.json and rules.md to reflect mem_ai_* unified naming conventions; removed conflicting legacy database_schema fields.