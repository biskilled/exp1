# Project Memory — aicli
_Generated: 2026-04-05 17:06 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python 3.12 CLI, FastAPI backend, and Electron desktop UI with PostgreSQL + pgvector for semantic search. The project provides unified session/tag management, LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok), workflow automation via async DAG execution, and comprehensive memory synthesis—currently focused on UI consolidation (Planner tab), session persistence, and memory response summarization.

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
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
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
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables replace per-project fragmentation
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Claude Haiku dual-layer memory synthesis generating 5 files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md with timestamp tracking
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list preventing startup race conditions
- Data persistence: load_once_on_access, update_on_save pattern; tags in mem_ai_tags_relations with row ID linking
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Backend: FastAPI + uvicorn; routers/ for API, core/ for infrastructure, data/ (dl_ prefix) for access, agents/ for tools and MCP
- UI unified: Planner tab for all tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created tags
- Session ordering by created_at (not updated_at) to prevent tag/phase updates from reordering session list
- Memory synthesis: summaries of LLM responses instead of full output; suggested tags auto-saved to session via _acceptSuggestedTag
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash start_backend.sh + npm run dev

## In Progress

- Session ordering fixed: sessions now order by created_at instead of updated_at to prevent phase/tag updates from reordering list
- Phase persistence enhanced: loads from DB on init, PATCH /chat/sessions/{id}/tags saves phase, red ⚠ badge for missing phase across UI/CLI/WF
- Commit-per-prompt inline display: replaced session-level strip with commits at bottom of each prompt entry (accent left-border, hash ↗ link showing only that prompt's commits)
- Tag deduplication and cross-view sync: 149 tags total (0 duplicates); removal via ✕ buttons propagates across Chat/History/Commits simultaneously
- AI suggestion auto-save with tag management: suggestions create tags in proper category via _acceptSuggestedTag; suggested tags marked with distinct color/mark; tags appear immediately in Planner
- Planner tab unified redesign: consolidated tag management into single tags view with category, active/inactive status, short description, created date; removed Feature/Bugs/Tags split

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index bec083e..a43e69d 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -65,12 +65,12 @@
     "config.py reads ~/.aicli/config.json for WORKSPACE_DIR at startup"
   ],
   "in_progress": [
-    "Phase synchronization across Chat tabs \u2014 fixed: phase now updates current session (not forcing new one); PATCH /chat/sessions/{id}/tags endpoint writes phase to session JSON; phase persists on session switch and loads correctly on app init for both UI and CLI sessions (2026-03-15)",
-    "Commit-per-prompt display in Chat tab \u2014 replaced session-level commit strip with inline commits at bottom of each prompt entry (accent left-border, hash \u2197 link); shows linked commits only for that prompt (2026-03-15)",
-    "Tag deduplication and cross-view synchronization \u2014 149 tags total (0 duplicates); tag removal via \u2715 buttons propagates across Chat/History/Commits simultaneously (2026-03-15)",
-    "Pagination for Chat/History/Commits \u2014 displays offset ranges (e.g., '1\u2013100 / 204') with \u25c0 \u25b6 navigation; unified history loads all archives on startup; 204 total entries including Feb 23 archive (2026-03-15)",
-    "AI suggestions auto-save to session \u2014 suggestions immediately create tags in proper category via _acceptSuggestedTag async call; tags appear in Planner; phase filter fully functional (2026-03-15)",
-    "Commit phase filtering \u2014 added phase column to Commits table; filter by phase same as Chat tab; phase persists per commit in database; red \u26a0 badge on sessions without phase (UI/CLI/WF all supported) (2026-03-15)"
+    "Phase persistence per session \u2014 fixed on init to load from DB; PATCH /chat/sessions/{id}/tags saves phase; UI/CLI/WF all supported with red \u26a0 badge for missing phase (2026-03-15)",
+    "Session ordering by created_at instead of updated_at \u2014 prevents phase/tag updates from reordering session list; sessions stay in chronological order (2026-03-15)",
+    "Commit-per-prompt display in Chat \u2014 inline commits at bottom of each prompt entry with accent left-border, hash \u2197 link; shows only commits for that specific prompt (2026-03-15)",
+    "Tag deduplication and cross-view synchronization \u2014 149 tags total (0 duplicates); removal via \u2715 buttons propagates across Chat/History/Commits simultaneously (2026-03-15)",
+    "Pagination for Chat/History/Commits \u2014 displays offset ranges (e.g., '1\u2013100 / 204') with \u25c0 \u25b6 navigation; unified history loads all archives on startup (2026-03-15)",
+    "AI suggestions auto-save to session \u2014 suggestions create tags in proper category via _acceptSuggestedTag; tags appear in Planner; phase filter fully functional (2026-03-15)"
   ],
   "next_phase_plan": {
     "project_management_page": [
@@ -102,5 +102,5 @@
     "cloud": "Railway (Dockerfile + railway.toml)",
     "desktop": "Electron-builder: Mac dmg (arm64+x64), Windows nsis, Linux AppImage+deb"
   },
-  "last_memory_run": "2026-03-15T22:44:53Z"
+  "last_memory_run": "2026-03-15T22:52:14Z"
 }
\ No newline at end of file


### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/history.jsonl b/workspace/aicli/_system/history.jsonl
index 1393316..71abf86 100644
--- a/workspace/aicli/_system/history.jsonl
+++ b/workspace/aicli/_system/history.jsonl
@@ -1,39 +1,40 @@
-{"ts": "2026-03-09T04:08:09Z", "source": "claude_cli", "session_id": "cc70394f-9674-433a-88ce-489c9759ccf4", "provider": "claude", "user_input": "Assuming I will improve the project management page, workflow processes. can you update /memory - so it can be used for the next steps ? also please update all project summery , current feature and on going features", "output": "`/memory` ran with LLM synthesis and all files copied to `code_dir`. Let me verify the MEMORY.md output:", "user": null, "feature": null, "tags": [], "stop_reason": "end_turn"}
-{"ts": "2026-03-09T17:56:29Z", "source": "claude_cli", "session_id": "cc70394f-9674-433a-88ce-489c9759ccf4", "provider": "claude", "user_input": "The last prompts was asking for a new feature (clinet install/ support multiple projects) - it was made by this console. I do suppose to see that in history, but expceted to see that in session - where my prompt is wrutten as it is, and your response is summerised (the prevoius one was a big feature - which make you write huge oputput that is hard to understand). is it possible tha you will suggest tag if needed and summerise the response in chat history as part of /memory function ? also there is some UI confusion - History tab manage/show history as it is (chat, commit, run, workflow..) currently chat work, but commit are not showing at all, and event is empty (there is only claudde cli and aicli for now) .also I do see that you added active tag/tag management in history - which I am not sure is the place..  also you have added tag management into history which is not needed - as it will be managed by project manager  tab. there are 2 projects tab- one showing all project and the new one - projects which is dedicated to managing this project. please change the name of the new tab where all project management tabs will be to planner (as this will be dedicated to the project planning) . I liked more the way tag tab is managing new categories and tags then the way you did under prject manager. please add with the same layout (ability to add category, tag) to the planned tab under dedicated tab - tags. also extend that to support active/not active, add short desc, and created date. to summmerise the request : UI updated (tags management under planner tab), history fixing. improve /memory by summmerising llm response and using that instead of whole responses, suggesting relevant tags (based on what exists, or new one) and giving better ability to user - to use sujjested tag or create new one . i think that all tag management (sujjested, user update) will have to be from chat tab only. when you adding sujjested tag please use anpothe color/ mark - so user will understand it is something llm suggested ", "output": "", "user": null, "feature": null, "tags": []}
-{"ts": "2026-03-09T23:51:43Z", "source": "claude_cli", "session_id": "05e9af57-76f6-4aef-bb28-8347693f4099", "provider": "claude", "user_input": "I dont think your update works. lets start from Planer - there is not need to have 4 tabs - Feture, tag, Bugs and Tags. all can be managed only from tags. you can add category, for each cateogry add tags and for each tag - manage status, add desc and more properties related to tag (user created, due date... ) can you update Planer to have only one place to manage all tags ? the only other place that you can extend that is from chat (+) - is it possilbe to have a listbox that show active tags and option to add (the same listbox) ? when user add tag - he select which category, and based on that he choose existing or adding new tag", "output": "", "user": null, "feature": null, "tags": []}
-{"ts": "2026-03-10T00:11:26Z", "source": "claude_cli", "session_id": "03f774e9-ad60-4cf3-8c0c-0191ba9a78d0", "provider": "claude", "user_

### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index 6e4f056..b45a259 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-03-15T22:51:48Z",
+  "last_updated": "2026-03-15T23:08:41Z",
   "last_session_id": "03f774e9-ad60-4cf3-8c0c-0191ba9a78d0",
-  "last_session_ts": "2026-03-15T22:51:48Z",
-  "session_count": 98,
+  "last_session_ts": "2026-03-15T23:08:41Z",
+  "session_count": 99,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 7542f62..450f281 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-15 22:44 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-15 22:51 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -46,8 +46,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-03-15] There is still UI issue with updateting/ showing the correct phase per session. when ever app is loaded - phase in on re
 - [2026-03-15] The error still exists - When I change the phase (on chats) - I am not able to save. also when I switch between diffrent
 - [2026-03-15] Issue is not fixed - In Chat - I cannot change/update phase. also most chat session do not have the right phase now. and
 - [2026-03-15] Lets try to fix the first bug in the Chat session as it is not fixed. when I upload a session - I do not see the correct
-- [2026-03-15] I still do not see that fixed. the session that mandtory fields are not updates suppose to be maked with red. currently 
\ No newline at end of file
+- [2026-03-15] I still do not see that fixed. the session that mandtory fields are not updates suppose to be maked with red. currently 
+- [2026-03-15] That looks better. the problem now is that on any change of the phase the session order is changed as well . is it possi
\ No newline at end of file


### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 49b8948..d383a6b 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -149,3 +149,5 @@
 {"ts": "2026-03-15T22:30:50Z", "action": "commit_push", "source": "claude_cli", "session_id": "03f774e9-ad60-4cf3-8c0c-0191ba9a78d0", "hash": "bafd251c", "message": "chore: update system context and memory after claude session", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "03f774e9-ad60-4cf3-8c0c-0191ba9a78d0", "hash": "15ae3356", "message": "chore: sync workspace state after claude cli session 03f774e9", "files_count": 35, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-15T22:44:29Z"}
 {"ts": "2026-03-15T22:44:25Z", "action": "commit_push", "source": "claude_cli", "session_id": "03f774e9-ad60-4cf3-8c0c-0191ba9a78d0", "hash": "15ae3356", "message": "chore: sync workspace state after claude cli session 03f774e9", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "03f774e9-ad60-4cf3-8c0c-0191ba9a78d0", "hash": "2eaa14c2", "message": "chore: update system docs and memory after claude session 03f774e9", "files_count": 34, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-15T22:51:51Z"}
+{"ts": "2026-03-15T22:51:48Z", "action": "commit_push", "source": "claude_cli", "session_id": "03f774e9-ad60-4cf3-8c0c-0191ba9a78d0", "hash": "2eaa14c2", "message": "chore: update system docs and memory after claude session 03f774e9", "pushed": true, "push_error": ""}


### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index 76f95c7..069268d 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-03-15 22:44 UTC by aicli /memory_
+_Generated: 2026-03-15 22:51 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform that unifies prompts, responses, and project state across multiple AI tools (Claude CLI, Cursor, ChatGPT, etc.) so they all operate with the same context. The current state (v2.2.0) includes a fully functional Electron + FastAPI desktop app with per-session phase tracking, commit linking, nested tagging, semantic search via PostgreSQL+pgvector, and MCP integration for external agents. Recent work focused on fixing phase persistence across chat sessions, adding commit-per-prompt display in the UI, and ensuring tag synchronization across all views.
+aicli is a shared AI memory platform for developers that unifies conversation history, embeddings, commits, and semantic tagging across multiple AI tools (Claude CLI, Cursor, ChatGPT, etc.). Currently at v2.2.0, the system features session-phase tracking, commit-to-prompt linking, nested tagging with zero-DB-call caching, and LLM-synthesized memory rotation. The most recent work (2026-03-15) focused on stabilizing phase persistence, fixing session ordering, implementing per-prompt commit display, and ensuring tag deduplication across all UI views.
 
 ## Tech Stack
 
@@ -46,12 +46,12 @@ aicli is a shared AI memory platform that unifies prompts, responses, and projec
 
 ## In Progress
 
-- Phase synchronization across Chat tabs — fixed: phase now updates current session (not forcing new one); PATCH /chat/sessions/{id}/tags endpoint writes phase to session JSON; phase persists on session switch and loads correctly on app init for both UI and CLI sessions (2026-03-15)
-- Commit-per-prompt display in Chat tab — replaced session-level commit strip with inline commits at bottom of each prompt entry (accent left-border, hash ↗ link); shows linked commits only for that prompt (2026-03-15)
-- Tag deduplication and cross-view synchronization — 149 tags total (0 duplicates); tag removal via ✕ buttons propagates across Chat/History/Commits simultaneously (2026-03-15)
-- Pagination for Chat/History/Commits — displays offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation; unified history loads all archives on startup; 204 total entries including Feb 23 archive (2026-03-15)
-- AI suggestions auto-save to session — suggestions immediately create tags in proper category via _acceptSuggestedTag async call; tags appear in Planner; phase filter fully functional (2026-03-15)
-- Commit phase filtering — added phase column to Commits table; filter by phase same as Chat tab; phase persists per commit in database; red ⚠ badge on sessions without phase (UI/CLI/WF all supported) (2026-03-15)
+- Phase persistence per session — fixed on init to load from DB; PATCH /chat/sessions/{id}/tags saves phase; UI/CLI/WF all supported with red ⚠ badge for missing phase (2026-03-15)
+- Session ordering by created_at instead of updated_at — prevents phase/tag updates from reordering session list; sessions stay in chronological order (2026-03-15)
+- Commit-per-prompt display in Chat — inline commits at bottom of each prompt entry with accent left-border, hash ↗ link; shows only commits for that specific prompt (2026-03-15)
+- Tag deduplication and cross-view synchronization — 149 tags total (0 duplicates); removal via ✕ buttons propagates across Chat/History/Commits simultaneously (2026-03-15)
+- Pagination for Chat/History/Commits — displays offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation; unified history loads all archives on startup (2026-03-15)
+- AI suggestions auto-save to session — suggestions create

## AI Synthesis

**[2026-03-15]** `claude_cli` — Session ordering fixed: sessions now order by created_at instead of updated_at to prevent phase/tag updates from reordering the list while maintaining chronological integrity. **[2026-03-15]** `claude_cli` — Phase persistence enhanced: phase loads from database on initialization, persists via PATCH /chat/sessions/{id}/tags endpoint, and displays red ⚠ badge on sessions without phase across UI/CLI/workflow. **[2026-03-15]** `claude_cli` — Commit-per-prompt display redesigned: replaced session-level commit strip with inline commits at bottom of each prompt entry, featuring accent left-border and hash ↗ link showing only that specific prompt's commits. **[2026-03-15]** `claude_cli` — Tag deduplication completed: 149 total tags with 0 duplicates; removal via ✕ buttons now propagates changes across Chat/History/Commits tabs simultaneously. **[2026-03-09]** `claude_cli` — Planner tab unified: consolidated all tag management into single tags view supporting category, active/inactive status, short description, and created date; removed Feature/Bugs/Tags split. **[2026-03-09]** `claude_cli` — AI suggestion auto-save implemented: suggestions now create tags in proper category via _acceptSuggestedTag, marked with distinct color/mark, and appear immediately in Planner; tag management unified to Chat tab only.