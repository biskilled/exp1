# Backlog

> Review each use case group. Approve `[+]` items, reject `[-]`.
> Run `POST /memory/{project}/work-items` to merge approved items into use cases.

## **discovery** · 26/03/10-03:14 [ ] (claude)
> Type: existing
> Total: 8 prompts
> User tags:
> AI existing:
> AI new:

  PROMPTS P100607 [ ] [task] [completed] [4] — Clarify MCP server usage and chat view features
    Requirements: Explain if MCP server is used for project information; Clarify why no suggestions appear in sessions; Explain chat view footer details and commit tracking
    Deliveries: Confirmed Claude Code reads files directly via Read/Grep/Bash tools, not MCP server; Commit 0c3a9cb applied: feat: improve project routing and chat view updates

  PROMPTS P100610 [ ] [task] [completed] [4] — Explain aicli system concept to non-technical audience
    Requirements: Provide concise explanation of aicli system
    Deliveries: Explained aicli as shared AI memory platform solving context loss across AI tools; Commit df7f682 applied: chore: update system docs and hooks after claude cli session

  PROMPTS P100637 [ ] [task] [in-progress] [2] — Research alternative solutions for memory capabilities
    Requirements: Analyze trycycle (danshapiro/trycycle) and specrails solutions; Reshape memory capabilities based on raw materials discovered
    Deliveries: Assistant response incomplete - recommendation to restructure memory layer implied but not detailed

  PROMPTS P100640 [ ] [task] [completed] [4] — Run /memory command and audit memory layer architecture
    Requirements: Execute /memory command and review output; Analyze data storage and MCP usage in memory layer; Verify tagging system for embedding/retrieval by Claude CLI; Confirm MCP usage in current session
    Deliveries: Successfully ran /memory command generating 5 files; Assessed memory layer architecture with synthesized:false status; Provided honest assessment of current memory capabilities

  PROMPTS P100642 [ ] [task] [completed] [4] — Clarify MCP tool usage and .mcp.json configuration
    Requirements: Confirm if MCP is being used in session; Explain changes to .mcp.json configuration
    Deliveries: Confirmed not using MCP in session - using direct HTTP calls via curl and Python urllib instead; Documented .mcp.json location and configuration status

  PROMPTS P100647 [ ] [task] [in-progress] [1] — Use MCP tool to explain aicli project
    Requirements: Use MCP tool to retrieve project information; Explain aicli functionality via MCP
    Deliveries: User request noted but assistant response incomplete

  PROMPTS P100650 [ ] [task] [completed] [4] — Use MCP tool to explain codebase functionality
    Requirements: Use MCP tool to analyze code; Explain aicli codebase functionality
    Deliveries: Provided explanation of aicli shared AI memory platform concept and core functionality; Described context preservation across multiple AI tools (Claude CLI, Cursor, ChatGPT)

  PROMPTS P100651 [ ] [task] [completed] [4] — Evaluate Claude Agent SDK for multi-agent system
    Requirements: Explain Claude Agent SDK purpose; Assess SDK suitability for multi-agent roles (project manager, developer, tester, reviewer)
    Deliveries: Analyzed Claude Agent SDK capabilities and framework design; Evaluated applicability to user's multi-agent use case

---

## **ui-ux-improvements** · 26/03/10-00:11 [ ] (claude)
> Type: new
> Total: 36 prompts · 1 commits
> User tags:
> AI existing:
> AI new:

  PROMPTS P100601 [ ] [feature] [in-progress] [2] — Improve planner UI action visibility and archive re-activation
    Requirements: Make action buttons more visible; Add 3-dot menu button for archived items; Allow re-activation of archived items
    Deliveries: Identified import resolution errors in planner views

  PROMPTS P100720 [ ] [feature] [in-progress] [2] — Improve history view to show prompts and LLM responses with copy
    Requirements: Show full prompt and LLM response in history; Enable text selection and copy
    Deliveries: Updated system context files

  PROMPTS P100750 [ ] [feature] [completed] [4] — Add work_items table with name, desc, prompts, commits, date columns
    Requirements: Show work_items as table with columns: name, desc, prompts count, commits count, updated date; Enable sorting
    Deliveries: Added _renderWiPanel with draggable rows in ui/frontend/views/entities.js; fmtDate and hdr functions

  PROMPTS P100752 [ ] [feature] [completed] [4] — Implement work_items table in planner lower panel
    Requirements: Display work_items in lower planner tab
    Deliveries: Updated route_work_items.py get_unlinked_work_items; rewrote _renderWiPanel with table structure in entities.js (+94/-45)

  PROMPTS P100755 [ ] [feature] [in-progress] [3] — Implement work_items row delete button with confirmation
    Requirements: Add × dismiss button per work_item row
    Deliveries: HTML × button added to each work_item row in entities.js _renderWiPanel

  PROMPTS P100756 [ ] [feature] [completed] [4] — Add sticky header and AI tag suggestions for work_items
    Requirements: Make table header sticky on scroll; Show AI tag suggestions per work_item; Update memory with /memory command
    Deliveries: Added position:sticky;top:0;z-index:1 to all header <th> cells; wired AI tag suggestion display in _renderWiPanel

  PROMPTS P100757 [ ] [feature] [completed] [4] — Enhance memory tagging matching and improve tag suggestions
    Requirements: Show AI tag suggestions on each work_item row; Improve tag matching logic
    Deliveries: Enhanced MemoryTagging class with better matching (+55/-17); updated match_work_item_to_tags (+15/-2) and _load_all_tags (+14/-1)

  PROMPTS P100759 [ ] [feature] [completed] [4] — Implement AI tag suggestions with category:name format
    Requirements: Show ai_tags as category:name (e.g., bug:auth, feature:dropbox); Distinguish existing vs new tags with colors
    Deliveries: Updated route_work_items.py get_unlinked_work_items; refactored _renderWiPanel tag display with category:name format

  PROMPTS P100803 [ ] [feature] [completed] [4] — Add timestamp to prompts and session ID display with tag management
    Requirements: Show timestamp next to YOU in chat; Display session ID (last 5 chars); Add tag option per prompt
    Deliveries: Updated history.js to show sid.slice(-5) in left panel; added timestamp next to prompt author in chat view

  PROMPTS P100804 [ ] [feature] [completed] [4] — Update session header to show source, phase, session ID and prompt count
    Requirements: Show CLI phase (session number) in header; Display session ID in top right; Show all session metadata
    Deliveries: Updated chat.js header format to 'CLI · development · (ab3f9) · 3 prompts · 26/04/15-19:31'

  PROMPTS P100806 [ ] [feature] [completed] [4] — Add session visibility in Chat tab matching History detail level
    Requirements: Show session metadata in Chat left sidebar; Add YY/MM/DD-HH:MM timestamp to prompts
    Deliveries: Updated Chat left sidebar to show 'CLI · development · (ab3f9)' per session; added timestamps in message rows

  PROMPTS P100595 [ ] [bug] [completed] [4] — Backend bind error on port 8000 from stale uvicorn instance
    Requirements: Fix UI loading issue and bind address 127.0.0.1:8000 error
    Deliveries: Identified stale uvicorn process (PID 86671) blocking port 8000

  PROMPTS P100625 [ ] [bug] [in-progress] [3] — Fix phase display not persisting across sessions and app load
    Requirements: Load last phase from DB on app startup; Update phase properly on session switch
    Deliveries: Identified root causes: no DB load on startup, session switch doesn't sync phase state

  PROMPTS P100626 [ ] [bug] [in-progress] [3] — Fix phase save, session switch sync, and commit phase filtering
    Requirements: Allow phase save in chat; Sync phases on session switch; Add phase filter to commits view
    Deliveries: Removed _sessionId = null that was preventing phase save; identified session metadata issues

  PROMPTS P100627 [ ] [bug] [in-progress] [3] — Restore phase change functionality and fix default filters
    Requirements: Restore phase change in Chat; Fix session phase display; Set history default to all phases; Fix commit phase filter
    Deliveries: Restored _sessionId = null for phase isolation; restored api.putSessionTags call

  PROMPTS P100628 [ ] [bug] [completed] [4] — Fix phase display per session and enable phase updates
    Requirements: Show correct phase per session on load; Enable phase change on session switch
    Deliveries: Phase change listener in chat.js restored; session metadata now tracks phase correctly

  PROMPTS P100629 [ ] [bug] [completed] [4] — Mark sessions with missing mandatory fields in red warning
    Requirements: Red warning indicator for incomplete mandatory fields per phase
    Deliveries: Removed source-filtering condition; now ALL sessions (UI, CLI, WF) without required tags show ⚠ indicator

  PROMPTS P100630 [ ] [bug] [completed] [4] — Prevent session reordering on phase change
    Requirements: Keep session order stable when changing phase
    Deliveries: Backend: patch_session_tags no longer updates updated_at; Frontend: _loadSessions preserves sort order

  PROMPTS P100665 [ ] [bug] [in-progress] [3] — Fix missing recent projects and backend startup logging
    Requirements: Show recent projects as 'as project'; Improve backend load time visibility
    Deliveries: Identified race condition in project load; added retry logic to _continueToApp

  PROMPTS P100721 [ ] [bug] [in-progress] [3] — Fix history view to display LLM responses alongside prompts
    Requirements: Show LLM response column in history
    Deliveries: Verified hook-response saves to mem_mrr_prompts.response; all four background hooks present

  PROMPTS P100753 [ ] [bug] [completed] [4] — Improve work_items table header clarity and column spacing
    Requirements: Make header visually distinct; Add padding and widen columns; Clearer labels
    Deliveries: Updated entities.js _renderWiPanel header with background, padding; widened columns from 38px in hdr function

  PROMPTS P100754 [ ] [bug] [completed] [4] — Format date to yy/mm/dd-hh:mm and filter non-work_items tags
    Requirements: Change date format to yy/mm/dd-hh:mm; Hide non-work_item tags like Shared-memory, billing
    Deliveries: Updated fmtDate in entities.js; verified api.workItems.delete exists; wired _wiPanelDelete handler

  PROMPTS P100758 [ ] [bug] [completed] [4] — Fix work_item detail loading and improve UI spacing and font size
    Requirements: Load work_item details on click; Move tags and approve/remove buttons closer; Increase font size for Electron
    Deliveries: Added GET /work-items/{id} endpoint in route_work_items.py; _openWorkItemDrawer now calls direct API

  PROMPTS P100760 [ ] [bug] [in-progress] [3] — Fix tag display and description column layout in work_items table
    Requirements: Display user and AI tags on rows; Use full row width for description column
    Deliveries: Restructured _renderWiPanel to show tags; removed table-layout:fixed to allow flexible columns

  PROMPTS P100761 [ ] [bug] [completed] [4] — Restore table layout and add labeled tag sections
    Requirements: Show all columns including rightmost; Add labels for tag types: AI (exists/new), User
    Deliveries: Restored table-layout:fixed; added labeled sections in _renderWiPanel showing AI, User tag rows

  PROMPTS P100762 [ ] [bug] [completed] [4] — Add left padding and fix date formatting to full yy/mm/dd-hh:mm
    Requirements: Add left padding to table; Show full date format yy/mm/dd-hh:mm; Label AI tags as existing vs new
    Deliveries: Fixed missing json import in route_work_items.py; enhanced tag label display with distinction for AI(EXISTS) and AI(NEW)

  PROMPTS P100794 [ ] [bug] [in-progress] [3] — Fix planner UI category display and work_item disappearance on tag accept
    Requirements: Show bug/category filters in planner; Keep work_item visible after accepting AI tag
    Deliveries: Fixed duplicate const cats declaration in _wiPanelCreateTag; cleaned up agent context

  PROMPTS P100795 [ ] [bug] [completed] [4] — Fix Electron empty load and variable naming conflicts
    Requirements: Fix Electron loading empty page
    Deliveries: Removed duplicate const cats declaration; cleaned up _system legacy files; added m031_commits_cleanup migration

  PROMPTS P100802 [ ] [bug] [completed] [4] — Fix latest prompts not displaying and add auto-update for new prompts
    Requirements: Show latest Claude CLI prompts in UI; Auto-update chat when new prompts arrive
    Deliveries: Migration m050 fixed silent DB error; restructured context files; prompts now appearing in chat view

  PROMPTS P100807 [ ] [bug] [completed] [4] — Move session ID to tag bar and reduce redundant phase display
    Requirements: Show session ID in tag bar only; Remove redundant phase display; Hide session ID from message area
    Deliveries: Added monospace (ab3f9) badge in tag bar between entity chips; removed duplicate phase from message headers

  PROMPTS P100808 [ ] [bug] [completed] [4] — Fix initial prompt loading showing partial history instead of full
    Requirements: Load all prompts from DB on startup, not from _system session files; Stop using stale session files
    Deliveries: Added limit=500 to chat_history endpoint; fixed _normalize_jsonl_entry to handle DB entries properly

  PROMPTS P100809 [ ] [bug] [completed] [4] — Fix stale session ID loading on app startup
    Requirements: Load current session on startup instead of old session; Prevent stale _sessionId persistence
    Deliveries: Fixed module-level _sessionId variable persisting across tabs; now resets on renderChat() in chat.js

  PROMPTS P100810 [ ] [bug] [completed] [5] — Load current session immediately on Chat view startup
    Requirements: Load correct session on startup without 15-second delay
    Deliveries: Modified _loadSessions to read state.currentProject.dev_runtime_state.last_session_id immediately and set correct _sessionId in chat.js (+7/-3)

  PROMPTS P100596 [ ] [task] [completed] [4] — Clean backend restart and Vite dev server setup
    Requirements: Restart UI with fresh backend, fix blank UI loading
    Deliveries: Confirmed port 8000 free; instructed clean restart from ui/ with dev script setting NODE_ENV=development

  PROMPTS P100604 [ ] [task] [completed] [4] — Clarify accept button location in Chat tag bar UI
    Requirements: Show where accept button is located
    Deliveries: Tag bar identified as thin bar at top of chat area below title; chips display after /memory command

  PROMPTS P100751 [ ] [task] [completed] [4] — UI changes not visible after rebuild
    Requirements: Make UI changes visible after update
    Deliveries: Confirmed Vite is serving updated files; instructed hard refresh (Cmd+Shift+R)

  COMMITS C200457 [+] [task] [completed] [5] — Update system docs and refactor work items after CLI session
    Deliveries: Updated system documentation files to reflect current architecture and processes; Refactored work items structure following CLI session outcomes

---

## **database-schema-refactor** · 26/03/10-00:52 [ ] (claude)
> Type: new
> Total: 38 prompts · 1 commits
> User tags:
> AI existing:
> AI new:

  PROMPTS P100597 [ ] [feature] [completed] [4] — Optimize database calls by caching tags in memory on project load
    Requirements: Reduce SQL calls by loading tags once on project access; Update DB only on save, not on every operation
    Deliveries: chat.js: _pickerPopulateCats() reads from cache instead of DB; Tag picker populated with counts from memory cache

  PROMPTS P100598 [ ] [feature] [completed] [2] — Design nested tags hierarchy and optimize SQL query loading strategy
    Requirements: Optimize SQL queries to load once per project lifecycle; Add nested tags support (beyond current 2-level category/tag hierarchy
    Deliveries: Designed database change: parent_id column addition to entity_values for nested tags; Proposed loading strategy: cache on project load, update on save only

  PROMPTS P100669 [ ] [feature] [completed] [3] — Implement tagging functionality with mem_ai_tags_relations table
    Requirements: Verify tagging system fully implements design; Create mem_ai_tags_relations for event tagging; Ensure tags populate from MRR (Memory Reflection Record)
    Deliveries: mem_ai_tags_relations table created for linking tags to events; Tagging system captures maximum info per event for MRR population

  PROMPTS P100699 [ ] [feature] [in-progress] [2] — Add tags text column to MRR tables matching work_items phase
    Requirements: Replace ai_tags with tags [text] column in mem_mrr_* tables; Allow UI and claude-cli to update tags in history; Force user tagging per session
    Deliveries: Designed tags column as text array for user-editable and claude-generated tags

  PROMPTS P100670 [ ] [bug] [completed] [4] — Fix table naming error: mng_ai_tags_relations → mem_ai_tags_relations
    Requirements: Correct mng_ prefix to mem_ for AI event tables
    Deliveries: mem_ai_tags_relations table name corrected in schema

  PROMPTS P100701 [ ] [bug] [completed] [4] — Fix undefined column errors in route_entities and route_work_items
    Requirements: Fix UndefinedColumn error: t.lifecycle in route_entities line 359; Remove PHASE column if unused in tables
    Deliveries: route_entities.py: lifecycle column reference removed; PHASE column audit completed

  PROMPTS P100702 [ ] [bug] [completed] [4] — Fix undefined column error in work_items loading
    Requirements: Fix UndefinedColumn error: p.work_item_id in route_work_items line 351
    Deliveries: route_work_items.py: work_item_id column reference corrected

  PROMPTS P100655 [ ] [task] [in-progress] [2] — Remove unused tables and restructure naming convention with mng_/cl_ prefixes
    Requirements: Remove stale unused tables; Rename tables: mng_TABLE_NAME for global/client-level, cl_TABLE_NAME for client-specific
    Deliveries: Identified unused tables for removal; Verified work_item_pipeline.py core file structure

  PROMPTS P100656 [ ] [task] [completed] [4] — Drop 5 stale legacy tables and reorganize schema from 29 to 24 tables
    Requirements: Remove old unused tables from database; Verify schema changes apply
    Deliveries: Dropped tables: commits, embeddings, and 3 other bare legacy tables; Reorganized naming: 24 tables with consistent mng_/cl_ prefixes

  PROMPTS P100668 [ ] [task] [completed] [3] — Merge pr_embeddings and pr_memory_events into mem_ai_events with event tracking
    Requirements: Merge pr_embeddings and pr_memory_events into single mem_ai_events table; Add event_type column and track session_id, session_desc (claude_cli etc)
    Deliveries: mem_ai_events table designed with id, project_id, session_id, session_desc, event_type columns

  PROMPTS P100671 [ ] [task] [in-progress] [1] — Define relation management strategy for manual and system-detected relationships
    Requirements: Support manual relations (developer-declared) via CLI/admin/SQL; Support auto-detected relations between work items
    Deliveries: Documented manual relation workflow and examples (smart-combobox depends_on)

  PROMPTS P100672 [ ] [task] [completed] [3] — Rename project tables and add feature snapshots layer to memory structure
    Requirements: Rename pr_project_facts to mem_ai_project_facts; Rename pr_work_items to mem_ai_work_items; Create mem_ai_features table; Add Work Items/Feature Snapshots/Project Facts layer with triggers
    Deliveries: mem_ai_project_facts table created; mem_ai_work_items table created; mem_ai_features table structure defined with snapshot tracking

  PROMPTS P100673 [ ] [task] [completed] [3] — Auto-regenerate memory files from project facts and work items
    Requirements: Auto-regenerate CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md and LLM system prompts; Populate from mem_ai_project_facts, mem_ai_work_items, session data
    Deliveries: Memory file generation implemented; System prompts updated from project facts and work items

  PROMPTS P100674 [ ] [task] [completed] [3] — Update aicli_memory structure with new layer relationships and tagging
    Requirements: Document updated memory structure in aicli_memory; Explain layer relationships and tagging mechanism
    Deliveries: aicli_memory.md updated with new memory layer structure and relationships

  PROMPTS P100675 [ ] [task] [completed] [3] — Merge session summaries into mem_ai_events with event_type tracking
    Requirements: Merge pr_session_summeries into mem_ai_events; Add event_type column for session_summary event tracking
    Deliveries: mem_ai_events extended with session_summary event_type support

  PROMPTS P100676 [ ] [task] [in-progress] [2] — Add llm_source to mem_ai_events and audit unused columns
    Requirements: Add llm_source column to mem_ai_events; Remove or validate language and file_path columns
    Deliveries: llm_source column identified as missing; Audit of unused columns (language, file_path) initiated

  PROMPTS P100677 [ ] [task] [completed] [4] — Apply DDL changes to live database
    Requirements: Execute DDL migrations to apply schema changes to database
    Deliveries: database.py refactored and DDL applied successfully

  PROMPTS P100678 [ ] [task] [completed] [3] — Remove summary_tags array and move tags to mem_ai_tags via MRR routing
    Requirements: Remove summary_tags[] from mem_ai_events; Move tags to separate mem_ai_tags table; Tags sourced from MRR when applicable
    Deliveries: Removed summary_tags[] array from mem_ai_events; Tags now routed through mem_ai_tags linked by event id

  PROMPTS P100679 [ ] [task] [completed] [3] — Refactor mem_mrr_* tables: remove unused columns, change commit ID to integer
    Requirements: Refactor mem_mrr_* tables removing unused columns (session_src_desc, session_src_id, tags[]); Change commit table to use integer ID instead of hash; Consolidate tags in mem_mrr_prompts
    Deliveries: mem_mrr_* tables refactored with unused columns removed; Commit ID changed to integer type

  PROMPTS P100681 [ ] [task] [completed] [3] — Refactor mem_ai_* tables to remove unused columns and consolidate structure
    Requirements: Apply same refactoring to mem_ai_* tables as mem_mrr_*
    Deliveries: mem_ai_* tables refactored with consolidated column structure

  PROMPTS P100683 [ ] [task] [completed] [3] — Reduce database.py size by removing old migrations and boilerplate
    Requirements: Remove old migrations from database.py; Trim boilerplate code to reduce file size
    Deliveries: database.py: old migrations removed and boilerplate trimmed

  PROMPTS P100689 [ ] [task] [completed] [3] — Review and remove references to deleted tables in Database class
    Requirements: Audit Database class for references to stale/deleted tables; Remove method calls and references to non-existent tables
    Deliveries: Database.py reviewed and cleaned of references to old tables

  PROMPTS P100698 [ ] [task] [completed] [4] — Verify table structure changes applied and drop _old tables
    Requirements: Confirm table structure changes in live database; Remove legacy _old backup tables to save space
    Deliveries: Table structure verified in schema; Legacy _old tables identified and cleaned up

  PROMPTS P100705 [ ] [task] [in-progress] [2] — Audit mem_ai_events for llm_source population and tag/metadata alignment
    Requirements: Move llm_source column after project_id; Identify where/when mem_ai_events is populated; Align tags (MRR) vs metadata (events) columns; Ensure all MRR tags migrate to events
    Deliveries: mem_ai_events structure analyzed for population points; Tags vs metadata column alignment identified

  PROMPTS P100706 [ ] [task] [in-progress] [2] — Reorganize mem_ai_events columns: llm_source after project, embedding last
    Requirements: Move llm_source column to position after project_id; Move embedding column to end of all tables containing it; Update database.py (trim old tables and code)
    Deliveries: Column order changes designed for mem_ai_events and all embedding tables

  PROMPTS P100707 [ ] [task] [completed] [3] — Verify mem_ai_events column order changes applied to database
    Requirements: Confirm llm_source moved after project_id; Confirm embedding column at end of table
    Deliveries: mem_ai_events schema verified with correct column ordering

  PROMPTS P100708 [ ] [task] [completed] [4] — Migrate mem_ai_events: rename old to _old, create new, copy data
    Requirements: Rename current mem_ai_events to mem_ai_events_old; Create new mem_ai_events with correct schema; Migrate data from old to new table
    Deliveries: mem_ai_events_old backup created; New mem_ai_events table created with final schema; Data migration completed

  PROMPTS P100709 [ ] [task] [completed] [2] — Audit usage of doc_type, language, file_path, and session_action_item columns
    Requirements: Clarify usage of doc_type, language, file_path columns; Determine if session_action_item can apply to other sources (items, prompts)
    Deliveries: Column usage analysis completed; session_action_item flexibility assessed

  PROMPTS P100710 [ ] [task] [in-progress] [2] — Convert language/file_path columns to tags in appropriate tables
    Requirements: Add language as tag on commit update (add to MRR tags); Add language as tag on event creation (add to events table, remove column); Remove file_change data if insufficient
    Deliveries: Strategy designed: language tag routing based on creation point

  PROMPTS P100711 [ ] [task] [in-progress] [1] — Consolidate chunk and chunk_type data into tags dictionary
    Requirements: Assess chunk and chunk_type column utility; Migrate chunk data to tags dictionary for work_items
    Deliveries: chunk/chunk_type usage analyzed as potential tag candidates

  PROMPTS P100712 [ ] [task] [completed] [3] — Clean stale history events and verify llm_source population
    Requirements: Remove nonsensical history events from table; Verify llm_source is properly populated across all events; Run /memory update command
    Deliveries: Stale history events cleaned from mem_ai_events; llm_source population verified and updated; Memory system refreshed

  PROMPTS P100714 [ ] [task] [in-progress] [1] — Build comprehensive aicli_memory.md describing all memory layers and mirroring
    Requirements: Document all memory layers from scratch; Explain MRR (mirroring layer) and event layer mechanics; List triggers, prompts, and workflows per step; Provide improvement suggestions for work_item/project_facts phases
    Deliveries: aicli_memory.md structure and layer descriptions drafted

  PROMPTS P100717 [ ] [task] [in-progress] [1] — Create mng_projects table and migrate project_id from text to FK relationship
    Requirements: Create mng_projects table with id, name, desc, and project defaults; Replace text project column with project_id (FK) across all tables; Migrate existing project data
    Deliveries: mng_projects table design created with default settings support

  PROMPTS P100725 [ ] [task] [completed] [2] — Audit mem_ai_work_items columns and clarify purpose of content/summary/requirements
    Requirements: Clarify source_session_id usage in work_items; Define purpose of content, summary, requirements columns (vs tags from mem_ai_events); Document main work_items table structure
    Deliveries: 20-column mem_ai_work_items audit completed with column purpose analysis; content/summary/requirements column functions documented

  PROMPTS P100746 [ ] [task] [completed] [4] — Create db_schema.sql with canonical CREATE TABLE statements and indexes
    Requirements: Extract all CREATE TABLE statements to db_schema.sql; Include IF NOT EXISTS, remarks, indexes, foreign keys; Make db_schema.sql source of truth for schema changes
    Deliveries: backend/core/db_schema.sql created (~350 lines) with all final table schemas; All ALTER TABLE statements consolidated with remarks and indexes

  PROMPTS P100797 [ ] [task] [completed] [4] — Migrate mem_ai_events with correct column ordering and drop _old table
    Requirements: Re-migrate mem_ai_events using corrected column order from user specification; Drop mem_ai_events_old after successful migration
    Deliveries: m035_reorder_mem_mrr_commits (+80/-0) migration applied; m036_reorder_mem_ai_events (+70/-0) migration applied; backend/routers/route_admin.py: trim_events (+63/-0) cleanup utility added; _old tables dropped to save space

  PROMPTS P100811 [ ] [task] [completed] [4] — Refactor user_id from UUID string to SERIAL INT and add updated_at timestamps
    Requirements: Change user_id type from UUID text to SERIAL INT (matching project_id/client_id); Add updated_at timestamp to all mirror tables; Add user_id after project_id in mirror tables
    Deliveries: m051_schema_refactor_user_id_updated_at migration (+359/-0) completed; mng_users.id: UUID → SERIAL INT; All mirror tables: user_id and updated_at columns added; backend/core/auth.py: _resolve_user_id refactored for INT lookup

  PROMPTS P100812 [ ] [task] [completed] [4] — Reorder table columns per standard: id/client_id/project_id/user_id, timestamps at end
    Requirements: Reorder columns in 18 tables: id → client_id → project_id → user_id (or id → project_id → user_id); Move created_at/updated_at to end of tables; Remove committed_at (duplicate of created_at/updated_at)
    Deliveries: m052 migration: 18 tables rebuilt with correct column order; mem_mrr_* tables: user_id after project_id, timestamps at end; All tables now follow id → client/project → user → data → timestamps pattern

  COMMITS C200454 [+] [task] [completed] [5] — Update system state and simplify database core module
    Deliveries: Updated system state configuration in core module initialization; Simplified database core module structure and dependencies

---

## **tagging-system** · 26/03/14-13:04 [ ] (claude)
> Type: new
> Total: 30 prompts
> User tags:
> AI existing:
> AI new:

  PROMPTS P100612 [ ] [feature] [completed] [4] — Cache tags in memory once on history tab open to reduce DB calls
    Requirements: Load all tags only once into memory; Save selected tag with original color from combolist
    Deliveries: ui/frontend/views/history.js: _renderChat now includes listCategories cache on tab open

  PROMPTS P100614 [ ] [feature] [completed] [4] — Link commits/pushes to prompt IDs instead of just session IDs
    Requirements: Create link between commit/push and prompt ID (multiple commits per session)
    Deliveries: Created 5 real links mapping commits to prompts; sample: d0f14c21 → prompt 'It is lookls like hooks are not working now...'

  PROMPTS P100615 [ ] [feature] [completed] [4] — Rotate history.jsonl logs when reaching 500 rows with YYMMDDHHSS timestamp
    Requirements: Check if session_tags.json is used; Rotate history.jsonl to history_YYMMDDHHSS when reaching 500 rows
    Deliveries: projects.py: _rotate_history() implemented with logging; history rotation confirmed working

  PROMPTS P100618 [ ] [feature] [completed] [4] — Ensure tag alignment across History/Commit/Chat screens with duplicate removal
    Requirements: Align tags across History, Commit, and Chat; Remove duplicate tags; Add option to delete (×) tags affecting all screens
    Deliveries: Verified 149 event tags with 0 duplicates; backend uses ON CONFLICT DO NOTHING on tag inserts

  PROMPTS P100620 [ ] [feature] [completed] [4] — Link each commit to specific prompt instead of session-level tagging
    Requirements: Link commit tags to prompts (per-prompt instead of per-session)
    Deliveries: GET /history/commits endpoint returns prompt_source_id in every commit row; frontend _commitData.commits updated

  PROMPTS P100688 [ ] [feature] [in-progress] [2] — Implement drag-and-drop feature merge in Planner tab UI
    Requirements: Add drag-and-drop merge features in Planner tab; Merge dragged feature into target feature

  PROMPTS P100699 [ ] [feature] [in-progress] [2] — Refactor tagging mechanism to mirror work_items phase with user-editable tags column
    Requirements: Replace ai_tags with tags [text] column; Enable tag updates via History UI or Claude CLI

  PROMPTS P100713 [ ] [feature] [in-progress] [2] — Make tag suggestions visible in UI with proper formatting
    Requirements: Display tag suggestions visibly in UI

  PROMPTS P100759 [ ] [feature] [completed] [4] — Update AI tag format to category:name with color-coded suggestions
    Requirements: AI tags use format bug:auth or feature:dropbox; Show suggestions from existing tags with new tag indicator
    Deliveries: ui/frontend/views/entities.js: _renderWiPanel updated with category:name format (+27/-12); backend/routers/route_work_items.py: get_unlinked_work_items implemented (+4/-0)

  PROMPTS P100763 [ ] [feature] [completed] [4] — Implement smart AI tag suggestion prioritizing task/bug/feature categories
    Requirements: Suggest tags from task/bug/feature first; Fall back to doc_type/phase tags; Suggest new tag if no match found
    Deliveries: AI suggestion categorization: 103 AI(EXISTS), 15 AI(NEW) with proper category matching in background

  PROMPTS P100775 [ ] [feature] [completed] [4] — Move confirmed work items from list into tag and update all links
    Requirements: Remove confirm button for accepted AI tags; Move work item to tag when confirming existing tag; Create proper DB links
    Deliveries: entities.js: _wiPanelApproveTag refactored; existing tag confirmation removes work item from list and creates DB links

  PROMPTS P100776 [ ] [feature] [completed] [4] — Enable /tag command for prompts in same session without restart
    Requirements: Allow /tag command to add tags to current prompts
    Deliveries: /tag updates .agent-context and calls PUT /history/session-tags; log_user_prompt_tags hook logs tags

  PROMPTS P100785 [ ] [feature] [completed] [4] — Clean planner_tag schema: set creator with defaults, add updater, reorder columns
    Requirements: Creator must have value (username or 'ai'); Add updater column tracking last modifier; Reorder columns: client_id, project_id, created_at, updated_at
    Deliveries: db_migrations.py: m026_planner_tags_cleanup with 85 lines; schema columns reordered and creator/updater added

  PROMPTS P100693 [ ] [bug] [in-progress] [3] — Fix Planner tab lifecycle tags and update bug counter with AI suggestion tags
    Requirements: Clarify Lifecycle tagging purpose; Update bug counter display; Show AI-suggested bug tags under ai_suggestion column

  PROMPTS P100696 [ ] [bug] [in-progress] [2] — Remove Lifecycle tags from bug, feature, and task items
    Requirements: Remove Lifecycle tags appearing on bugs, features, and tasks

  PROMPTS P100700 [ ] [bug] [in-progress] [3] — Fix '[object object]' UI error and 422 backend error when adding tags
    Requirements: Fix UI tag display error; Fix 422 Unprocessable Entity backend error; Link commit/prompt tags properly

  PROMPTS P100703 [ ] [bug] [in-progress] [3] — Restore tag connection in UI and enable existing tag selection from combobox
    Requirements: Connect UI tag display to backend; Load existing tags in combobox; Show previously added tags on prompts/commits

  PROMPTS P100777 [ ] [bug] [completed] [4] — Resolve 'unknown skill tag' error and use /ac alternative
    Requirements: Fix 'tag' reserved name conflict in skill loader
    Deliveries: Session tagged with phase:development feature:work_items; /ac command works as alternative to /tag

  PROMPTS P100778 [ ] [bug] [completed] [4] — Fix secondary AI tags not disappearing when added to work items
    Requirements: Keep work items when accepting secondary tags (doc_type, phase); Only remove when confirming primary tag
    Deliveries: db_migrations.py: m022_backfill_event_work_item_ids, m021_rename_work_item_columns; _wiSecApprove fixed; memory_extraction.py updated

  PROMPTS P100619 [ ] [task] [completed] [4] — Verify tagging logic alignment: session/prompt tags and commit-prompt linking
    Requirements: Verify tags (per session), tags (per prompts), and commit-prompt linking logic
    Deliveries: history.py: _load_unified_history reads archives; history.js: data-ts attribute on entries; commit tagging confirmed

  PROMPTS P100632 [ ] [task] [completed] [4] — Verify database schema, saving mechanism, and tag linking optimization
    Requirements: Check tag linking and mapping in DB schema; Optimize DB structure and saving mechanism for tagging
    Deliveries: core/database.py: Added phase, feature, session_id as real columns; schema optimized for tag retrieval

  PROMPTS P100638 [ ] [task] [completed] [4] — Audit tag usage, memory improvement, and MCP data workflows
    Requirements: Check if tags are well used; Verify memory improvement from summarization; Assess MCP tool improvements
    Deliveries: event_tags_{project} system verified as fully wired in chat/history; tag usage optimized for memory efficiency

  PROMPTS P100653 [ ] [task] [completed] [4] — Review all features and plan Planner/Workflow tabs with tag mapping
    Requirements: Map features to Planner and Workflow tabs; Enable AI suggestion and user approval of tags
    Deliveries: main.js: Renamed Workflow→Pipelines and Prompts→Roles in PROJECT_TABS and sidebar navigation

  PROMPTS P100658 [ ] [task] [completed] [3] — Clarify purpose of session_tags.json file and mng_session_tags table
    Requirements: Explain session_tags.json usage; Clarify mng_session_tags table relationship
    Deliveries: Confirmed 24 database tables with clean split; mng_ prefix = 14 global config tables including mng_session_tags

  PROMPTS P100660 [ ] [task] [in-progress] [2] — Align client tables and verify multi-client schema design
    Requirements: Align client tables with mng_session_tags; Support multiple projects per client

  PROMPTS P100662 [ ] [task] [in-progress] [2] — Review client naming pattern and large table optimization strategy
    Requirements: Replace client name usage with mng_users table; Optimize large tables (history, commits)

  PROMPTS P100695 [ ] [task] [in-progress] [1] — Determine if Lifecycle tags are relevant and needed
    Requirements: Evaluate necessity of Lifecycle tags

  PROMPTS P100783 [ ] [task] [completed] [5] — Update session tag to feature:planner for planner tab work
    Requirements: Set session tag to feature:planner
    Deliveries: Session tags set to phase:development feature:planner

  PROMPTS P100784 [ ] [task] [completed] [4] — Audit planner_tag table schema and identify unused/duplicate columns
    Requirements: Review planner_tag table columns (seq_num, source, creator, status, code_summary)
    Deliveries: Identified unused columns: seq_num (never populated), duplicate status columns (status_user/status_ai), unnecessary code_summary

  PROMPTS P100789 [ ] [task] [completed] [5] — Add feature:feature_snapshot tag to current session
    Requirements: Set feature:feature_snapshot tag
    Deliveries: Session tag set to feature:feature_snapshot

---

## **memory-layers-events** · 26/03/14-13:11 [ ] (claude)
> Type: new
> Total: 48 prompts
> User tags:
> AI existing:
> AI new:

  PROMPTS P100613 [ ] [task] [in-progress] [0] — can you run /memory, to make sure all updated. also can you check that system is

  PROMPTS P100616 [ ] [task] [in-progress] [0] — Something wit hooks is not working now, as I do not see any new prompts / llm re

  PROMPTS P100621 [ ] [task] [in-progress] [0] — let me summerise not. first run /memroy to update all sumeeries, db tagging and 

  PROMPTS P100623 [ ] [task] [in-progress] [0] — The last commit was b255366 which suppose to be linked to the last prompt. it di

  PROMPTS P100624 [ ] [task] [in-progress] [0] — When I run memory through the aiCli - I did see some usefull suggestion that app

  PROMPTS P100631 [ ] [task] [in-progress] [0] — It looks good and working as expected. the issue now is how it is linked to Hist

  PROMPTS P100633 [ ] [task] [in-progress] [0] — is it align to the 5 steps memory? is there is any addiotnal requirement in orde

  PROMPTS P100634 [ ] [task] [in-progress] [0] — Is there is any addiotnal improvement that I can implemet for having full memroy

  PROMPTS P100635 [ ] [task] [in-progress] [0] — 1,2,3,4,5 and 8. I would like to add also anotehr mng table to check how many pr

  PROMPTS P100639 [ ] [task] [in-progress] [0] — Can you summersie all improvement - would that make the systme better perfromed 

  PROMPTS P100643 [ ] [task] [in-progress] [0] — I would like to start working on the workflows - the goal is to be able to be si

  PROMPTS P100644 [ ] [task] [in-progress] [0] — I do see you have crete a defualt pipe line in the Planner tab that run defualt 

  PROMPTS P100645 [ ] [task] [in-progress] [0] — I do mention to sotre the prompts in database, would there be a way to change th

  PROMPTS P100652 [ ] [task] [in-progress] [0] — I dont see nay changes from the last improvement - current planner do not suppos

  PROMPTS P100654 [ ] [task] [in-progress] [0] — Planner works partial - I do see the nested work on some category like doc_type 

  PROMPTS P100659 [ ] [task] [in-progress] [0] — clean that up . also I do remember there was graph support for memroy usage, but

  PROMPTS P100667 [ ] [task] [in-progress] [0] — Is it makes more sense, before I continue to the secopnd phase (refactor embeddi

  PROMPTS P100686 [ ] [task] [in-progress] [0] — Not sure if you remember the previous memory config. if you do (you can check ai

  PROMPTS P100715 [ ] [task] [in-progress] [0] — About orocess_item / messeges - trigger in /memroy (for all new items at the mom

  PROMPTS P100724 [ ] [task] [in-progress] [0] — I am checking the aiCli_memory - and it is looks likje it is not updated at all.

  PROMPTS P100731 [ ] [task] [in-progress] [0] — can you update all memory_items (maybe run /memory) to have an uodated data 

  PROMPTS P100733 [ ] [task] [in-progress] [0] — Can you use aiCli_memeory to describe the followng : how flow works from mirror.

  PROMPTS P100734 [ ] [task] [in-progress] [0] — Can you use aiCli_memeory to describe the followng : how flow works from mirror.

  PROMPTS P100735 [ ] [task] [in-progress] [0] — In addtion to your reccomendation, I would like to check the following -  mem_ai

  PROMPTS P100737 [ ] [task] [in-progress] [0] — I still see the columns in commit table - diif_summery and diff_details . is it 

  PROMPTS P100738 [ ] [task] [in-progress] [0] — I would like to understand the commit table - do you have my previous comment? m

  PROMPTS P100739 [ ] [task] [in-progress] [0] — Where simple extraction flow can be something like that:  pr_tags_map   WHERE re

  PROMPTS P100742 [ ] [task] [in-progress] [0] — can you explain where are the  prompts that used for update new commit ? 

  PROMPTS P100743 [ ] [task] [in-progress] [0] — Can you explain how commit data statitics are connected to work_items ? Is there

  PROMPTS P100744 [ ] [task] [in-progress] [0] — three is link from prompts to commits. each five prompts summeries to event, whi

  PROMPTS P100749 [ ] [task] [in-progress] [0] — I would like to understand how work_item are populated. work_item suppose to be 

  PROMPTS P100764 [ ] [task] [in-progress] [0] — Can you explain how do I see work_item #20006 as the one that was last updated ?

  PROMPTS P100766 [ ] [task] [in-progress] [0] — Where are all the rpompts for ai_tags and work_item are ?

  PROMPTS P100767 [ ] [task] [in-progress] [0] — I do see same work item working on mention document summery and update ai memory

  PROMPTS P100768 [ ] [task] [in-progress] [0] — Can you share the quesry you are suing the get all promotps, commit, event per w

  PROMPTS P100769 [ ] [task] [in-progress] [0] — before you desing. is it possible to add some mechanism to our converstion. for 

  PROMPTS P100774 [ ] [task] [in-progress] [0] — I still dont understand how there are work_items without any linked prompts. can

  PROMPTS P100779 [ ] [task] [in-progress] [0] — I am not sre what is start_id used for . Also code_summenry - what is it for ? t

  PROMPTS P100780 [ ] [task] [in-progress] [0] — I still dont understand what is summery column used for . also tags - I do see t

  PROMPTS P100781 [ ] [task] [in-progress] [0] — What is summery used for, I do see ai_desc, what is summery for ?

  PROMPTS P100782 [ ] [task] [in-progress] [0] — I think summery suppose to be part of ai_desc as there are alreadt 3 column for 

  PROMPTS P100786 [ ] [task] [in-progress] [0] — I am planning to add a layer that will merge planner_tags with wor_item - this l

  PROMPTS P100790 [ ] [task] [in-progress] [0] — Feature_snapshot  I would like to create the final stage - mem_ai_feature_snapsh

  PROMPTS P100791 [ ] [task] [in-progress] [0] — Assuming all will work properly. having a way to store all project history using

  PROMPTS P100796 [ ] [task] [in-progress] [0] — Events - I would like to make sure events are working properly in order to have 

  PROMPTS P100798 [ ] [task] [in-progress] [0] — In events table is there is any point to have importance ? I think its more rele

  PROMPTS P100799 [ ] [task] [in-progress] [0] — yes

  PROMPTS P100800 [ ] [task] [in-progress] [0] — I still see old tags in event is that intenional? it suppose to show only users

---

## **planner-workflow** · 26/03/09-04:08 [ ] (claude)
> Type: new
> Total: 72 prompts · 1 commits
> User tags:
> AI existing:
> AI new:

  PROMPTS P100594 [ ] [feature] [in-progress] [0] — I dont think your update works. lets start from Planer - there is not need to ha

  PROMPTS P100599 [ ] [feature] [in-progress] [0] — yes. just to clarify when I add login - it will be first level only ? 

  PROMPTS P100600 [ ] [feature] [in-progress] [0] — yes

  PROMPTS P100617 [ ] [feature] [in-progress] [0] — Pagination - I do see now in the chat only 24 prompts (there are much more) can 

  PROMPTS P100622 [ ] [feature] [in-progress] [0] — I would like to set that up , and also add that to new prokect as autoamted set 

  PROMPTS P100636 [ ] [feature] [in-progress] [0] — I would like to optimise the code : check each file, make sure code is in used a

  PROMPTS P100643 [ ] [feature] [in-progress] [0] — I would like to start working on the workflows - the goal is to be able to be si

  PROMPTS P100644 [ ] [feature] [in-progress] [0] — I do see you have crete a defualt pipe line in the Planner tab that run defualt 

  PROMPTS P100646 [ ] [feature] [in-progress] [0] — yes

  PROMPTS P100648 [ ] [feature] [in-progress] [0] — Somehow, I cannot see the prject now in order at me lat project.. also when I op

  PROMPTS P100649 [ ] [feature] [in-progress] [0] — In the project I used to see the aiCli project, and I do not see that now. also 

  PROMPTS P100652 [ ] [feature] [in-progress] [0] — I dont see nay changes from the last improvement - current planner do not suppos

  PROMPTS P100654 [ ] [feature] [in-progress] [0] — Planner works partial - I do see the nested work on some category like doc_type 

  PROMPTS P100657 [ ] [feature] [in-progress] [0] — looks better. why memory_items and project_facts are under systeme managament ta

  PROMPTS P100661 [ ] [feature] [in-progress] [0] — I would like to know what do you think about the architecure ? Assuming there mi

  PROMPTS P100662 [ ] [feature] [in-progress] [0] — That is correct. it is bed pattern to use clinet name. there is already mng_user

  PROMPTS P100663 [ ] [feature] [in-progress] [0] — it looks like it is a bit broken, I have got an error - '_Database' object has n

  PROMPTS P100664 [ ] [feature] [in-progress] [0] — There are some error - on the first load, it lookls like Backend is failing (aft

  PROMPTS P100693 [ ] [feature] [in-progress] [0] — I would like to work on the planer tab - I do see Lifecucle tagging which I am n

  PROMPTS P100694 [ ] [feature] [in-progress] [0] — I dont think the drag and drop is working. also counter - dont see any  change

  PROMPTS P100695 [ ] [feature] [in-progress] [0] — There is lifecycle tags which I am not sure are relevant. is it needed ?

  PROMPTS P100696 [ ] [feature] [in-progress] [0] — I do see Lifecycle tags on any bug, feature and task - which I dont think is rel

  PROMPTS P100697 [ ] [feature] [in-progress] [0] — I do see lots of bug under the bug category which I did not opend. should that b

  PROMPTS P100727 [ ] [feature] [in-progress] [0] — is it possilbe to actual move the work_item (drag) and drop that under the item 

  PROMPTS P100728 [ ] [feature] [in-progress] [0] — There are some issue - when I drag all tabs that I hoover on top are marked (not

  PROMPTS P100729 [ ] [feature] [in-progress] [0] — Looks better, still when I drag work_item - I do not see that droped under the i

  PROMPTS P100730 [ ] [feature] [in-progress] [0] — I would like to be able to move work_item back to work_item or to another items.

  PROMPTS P100747 [ ] [feature] [in-progress] [0] — In the ui when I press any tag, I do not the property on the left (I do see that

  PROMPTS P100750 [ ] [feature] [in-progress] [0] — In the UI - work_items shows as a row. I would each row to have name - desc colu

  PROMPTS P100771 [ ] [feature] [in-progress] [0] — can you check why it takes to long to  load planner tabs and work items? it look

  PROMPTS P100772 [ ] [feature] [in-progress] [0] — I am more confused noew. query - looks like it take longer. why there is DIGEST 

  PROMPTS P100773 [ ] [feature] [in-progress] [0] — now I dont see the counter or the promts. also, I still see work item   that  ar

  PROMPTS P100792 [ ] [feature] [in-progress] [0] — How can I improve points 4 and 5 ? for point 4 - I did make prompts in sappasret

  PROMPTS P100793 [ ] [feature] [in-progress] [0] — ok. can you implement that. make sure dashboard is a new tab. pipeline will be a

  PROMPTS P100592 [ ] [feature] [in-progress] [0] — Assuming I will improve the project management page, workflow processes. can you

  PROMPTS P100593 [ ] [feature] [in-progress] [0] — The last prompts was asking for a new feature (clinet install/ support multiple 

  PROMPTS P100602 [ ] [feature] [in-progress] [0] — why there is sometime problem to restart the app (I do see that beckend is exite

  PROMPTS P100603 [ ] [feature] [in-progress] [0] — I do see the save button - and when I save I do see the tag, when I am checking 

  PROMPTS P100605 [ ] [feature] [in-progress] [0] — can you run /memory, and make the UI more clear. add your sujjestion in a clear 

  PROMPTS P100606 [ ] [feature] [in-progress] [0] — can you run /memory and run some tests? I do not see any sujjestion on all the e

  PROMPTS P100608 [ ] [feature] [in-progress] [0] — hellow, how are you ?

  PROMPTS P100609 [ ] [feature] [in-progress] [0] — I understand the issue. I am using your claude cli and hooks to store propts and

  PROMPTS P100611 [ ] [feature] [in-progress] [0] — I do have some concern how commit/hash are linked to prompts/llm answers. also a

  PROMPTS P100641 [ ] [feature] [in-progress] [0] — Keys are stored at my .env file which you can load - for claude api the key is u

  PROMPTS P100666 [ ] [feature] [in-progress] [0] — Few more strucure - users are also part of client (client can have mutiple users

  PROMPTS P100680 [ ] [feature] [in-progress] [0] — test prompt after migration

  PROMPTS P100682 [ ] [feature] [in-progress] [0] — test after mem_ai cleanup

  PROMPTS P100684 [ ] [feature] [in-progress] [0] — Implement 1 and 2. pipeline is trigerred from the planer tab. for example there 

  PROMPTS P100685 [ ] [feature] [in-progress] [0] — Why there is no embedding in project_facts and work_items ? this is not suppose 

  PROMPTS P100687 [ ] [feature] [in-progress] [0] — yes . fix that all 

  PROMPTS P100690 [ ] [feature] [in-progress] [0] — Under backend folder, I do see a workspace foldr. is it used ? 

  PROMPTS P100691 [ ] [feature] [in-progress] [0] — plese delete that 

  PROMPTS P100692 [ ] [feature] [in-progress] [0] — I do see some errors in the ui - column "event_type" does not exist - line 228 i

  PROMPTS P100704 [ ] [feature] [in-progress] [0] — I have got an error on /history/commits/sync?project=aicli rest api in     execu

  PROMPTS P100716 [ ] [feature] [in-progress] [0] — test prompt after fix

  PROMPTS P100718 [ ] [feature] [in-progress] [0] — verify prompt after client_id fix

  PROMPTS P100719 [ ] [feature] [in-progress] [0] — final verify prompt

  PROMPTS P100722 [ ] [feature] [in-progress] [0] — I have  got the following error -  cur.execute(b''.join(parts)) started  route_h

  PROMPTS P100723 [ ] [feature] [in-progress] [0] — I still dont see the same issue in route_history line 470. cur.execute(b''.join(

  PROMPTS P100726 [ ] [feature] [in-progress] [0] — I do see an issue - Uncaught ReferenceError: _plannerSelectAiSubtype is not defi

  PROMPTS P100732 [ ] [feature] [in-progress] [0] — I do have some errors loading data - route_work_items line 249 - cur.execute(_SQ

  PROMPTS P100736 [ ] [feature] [in-progress] [0] — dont you have any moemry, did you see the previous file you din - aicli_memoy.md

  PROMPTS P100740 [ ] [feature] [in-progress] [0] — I do not see any update at the database 

  PROMPTS P100741 [ ] [feature] [in-progress] [0] — yes please

  PROMPTS P100745 [ ] [feature] [in-progress] [0] — There is a problem to load work_items - line 331 in route_work_items -column w.a

  PROMPTS P100748 [ ] [feature] [in-progress] [0] — I do not see mem_mrr_commits_code populated on every commit. is that suppose to 

  PROMPTS P100765 [ ] [feature] [in-progress] [0] — Can you recheck that ai_tags as I do see new work_item, bit cannot see any sujje

  PROMPTS P100770 [ ] [feature] [in-progress] [0] — I have just tried that, got unknow skill /tag. do I have to open a new session ?

  PROMPTS P100787 [ ] [feature] [in-progress] [0] — yes

  PROMPTS P100788 [ ] [feature] [in-progress] [0] — This start to look good. I would like to add one more column - deliveries that w

  PROMPTS P100801 [ ] [feature] [in-progress] [0] — yes drop that. also change mem_mrr_prompts column order - after client_id add pr

  PROMPTS P100805 [ ] [feature] [in-progress] [0] — test: is hook-log working now after m050?

  COMMITS C200445 [+] [feature] [completed] [5] — Enhance memory files, MCP server, and entities UI
    Deliveries: Memory files system enhanced with improved storage/retrieval mechanisms; MCP server configuration and protocol handling upgraded; Entities UI components refined for better user interaction and display

---

COMMITS 26/04/18-00:00 C200514 [x] [general] [task] (auto) — Update system files and refactor backend routes

  Completed:
  - System files updated; backend routes refactored (code)

---

COMMITS 26/04/18-00:00 C200515 [x] [general] [task] (auto) — Update AI session state and memory after session 17cd46bd

  Completed:
  - AI session state and memory files synchronized post-session (code)

---

COMMITS 26/04/18-00:00 C200516 [x] [general] [task] (auto) — Update AI session state and memory files

  Completed:
  - AI session state and memory files updated (code)

---

COMMITS 26/04/18-00:00 C200517 [x] [general] [task] (auto) — Update system state and memory after claude session d7be5539

  Completed:
  - System state and memory files synchronized post-session (code)

---

COMMITS 26/04/18-00:00 C200518 [x] [general] [task] (auto) — Update memory, rules, and session state files

  Completed:
  - Memory, rules, and session state files updated (code)

---

COMMITS 26/04/18-00:00 C200524 [x] [general] [task] (auto) — Update MEMORY.md and project docs after claude session

  Requirements:
  - maintain documentation currency
  - reflect session outcomes in memory

  Completed:
  - Updated MEMORY.md and project documentation (docs)

---

COMMITS 26/04/18-00:00 C200525 [x] [general] [task] (auto) — Update memory and rules files after claude session

  Requirements:
  - synchronize memory state
  - refresh rules documentation

  Completed:
  - Updated memory and rules files (docs)

---

COMMITS 26/04/18-00:00 C200526 [x] [general] [task] (auto) — Update memory, rules, and project docs after claude session

  Requirements:
  - consolidate session updates
  - maintain documentation consistency

  Completed:
  - Updated memory, rules, and project documentation files (docs)

---

COMMITS 26/04/18-00:00 C200527 [x] [general] [task] (auto) — Clean up system files after claude cli session

  Requirements:
  - remove temporary session artifacts

  Completed:
  - Cleaned up system files from cli session d7be5539 (code)

---

COMMITS 26/04/18-00:00 C200528 [x] [general] [task] (auto) — Update AI context files and trim MEMORY.md after session

  Requirements:
  - optimize memory file size
  - refresh AI context

  Completed:
  - Updated AI context files and trimmed MEMORY.md (docs)

---

COMMITS 26/04/18-00:00 C200519 [x] [general] [task] (auto) — Update MEMORY.md and project docs after claude session

  Requirements:
  - Maintain accurate project memory state
  - Keep documentation synchronized with session outcomes

  Completed:
  - Updated MEMORY.md and project documentation files (docs)

---

COMMITS 26/04/18-00:00 C200520 [x] [general] [task] (auto) — Update memory and rules files after claude session

  Requirements:
  - Keep memory files current with session state
  - Maintain consistent rules documentation

  Completed:
  - Updated memory and rules files (docs)

---

COMMITS 26/04/18-00:00 C200521 [x] [general] [task] (auto) — Update memory, rules, and project docs after claude session

  Requirements:
  - Synchronize memory state across documentation
  - Update rules and project structure documentation

  Completed:
  - Updated memory, rules, and project documentation (docs)

---

COMMITS 26/04/18-00:00 C200522 [x] [general] [task] (auto) — Clean up system files after claude cli session d7be5539

  Requirements:
  - Remove temporary or stale system files
  - Maintain clean repository state

  Completed:
  - Cleaned up system files from CLI session (code)

---

COMMITS 26/04/18-00:00 C200523 [x] [general] [task] (auto) — Update AI context files and trim MEMORY.md after session

  Requirements:
  - Keep AI context files current
  - Optimize MEMORY.md file size and relevance

  Completed:
  - Updated AI context files and trimmed MEMORY.md (docs)

---

COMMITS 26/04/18-00:00 C200529 [x] [general] [task] (auto) — Sync system files and update memory/chat after claude session

  Requirements:
  - Maintain system file consistency
  - Update session memory

  Completed:
  - System files and chat memory synchronized (code)

---

COMMITS 26/04/18-00:00 C200530 [x] [general] [task] (auto) — Update system files and memory after claude session 6ffb562b

  Requirements:
  - Maintain system file consistency
  - Update session memory

  Completed:
  - System files and memory updated post-session (code)

---

COMMITS 26/04/18-00:00 C200531 [x] [general] [task] (auto) — Update system files and memory after claude session 04d3b8ba

  Requirements:
  - Maintain system file consistency
  - Update session memory

  Completed:
  - System files and memory updated post-session (code)

---

COMMITS 26/04/18-00:00 C200532 [x] [general] [task] (auto) — Update system context and CLAUDE.md files post-session

  Requirements:
  - Update system context documentation
  - Update CLAUDE.md

  Completed:
  - System context and CLAUDE.md files updated (docs)

---

COMMITS 26/04/18-00:00 C200533 [x] [general] [task] (auto) — Update system context and memory files after claude session

  Requirements:
  - Update system context
  - Update memory files

  Completed:
  - System context and memory files updated (docs)

---

COMMITS 26/04/18-00:00 C200534 [x] [general] [task] (auto) — Sync system files and update memory/chat after claude session

  Completed:
  - Updated system files and memory/chat configuration files post-session (code)

---

COMMITS 26/04/18-00:00 C200535 [x] [general] [task] (auto) — Update system files and memory after claude session 6ffb562b

  Completed:
  - Updated system files and memory state following session 6ffb562b (code)

---

COMMITS 26/04/18-00:00 C200536 [x] [general] [task] (auto) — Update system files and memory after claude session 04d3b8ba

  Completed:
  - Updated system files and memory state following session 04d3b8ba (code)

---

COMMITS 26/04/18-00:00 C200537 [x] [general] [task] (auto) — Update system context and CLAUDE.md files post-session

  Completed:
  - Updated CLAUDE.md and system context documentation files (docs)

---

COMMITS 26/04/18-00:00 C200538 [x] [general] [task] (auto) — Update system context and memory files after claude session

  Completed:
  - Updated system context and memory documentation files (docs)

---

COMMITS 26/04/18-00:00 C200539 [x] [general] [task] (auto) — Update system context and memory files after claude session

  Completed:
  - Updated system context and memory documentation files (docs)

---

COMMITS 26/04/18-00:00 C200540 [x] [general] [task] (auto) — Remove aicli system context and claude session files

  Completed:
  - Removed stale aicli system context and claude session files (code)

---

COMMITS 26/04/18-00:00 C200541 [x] [general] [task] (auto) — Update system prompts and memory after claude session

  Completed:
  - Updated system prompts and memory documentation (docs)

---

COMMITS 26/04/18-00:00 C200542 [x] [general] [task] (auto) — Update system prompts and memory after CLI session 14a417f0

  Completed:
  - Updated system prompts and memory files following CLI session (docs)

---

COMMITS 26/04/18-00:00 C200543 [x] [general] [task] (auto) — Remove stale system context and claude session files

  Completed:
  - Removed stale system context and claude session files (code)

---

COMMITS 26/04/18-00:00 C200544 [x] [general] [task] (auto) — Update system context and memory files after claude session

  Completed:
  - Updated system context and memory documentation files (docs)

---

COMMITS 26/04/18-00:00 C200545 [x] [general] [task] (auto) — Remove aicli system context and claude session files

  Completed:
  - Removed stale aicli system context and claude session files (code)

---

COMMITS 26/04/18-00:00 C200546 [x] [general] [task] (auto) — Update system prompts and memory after claude session

  Completed:
  - Updated system prompts and memory files (docs)

---

COMMITS 26/04/18-00:00 C200547 [x] [general] [task] (auto) — Update system prompts and memory after CLI session 14a417f0

  Completed:
  - Updated system prompts and memory documentation (docs)

---

COMMITS 26/04/18-00:00 C200548 [x] [general] [task] (auto) — Remove stale system context and claude session files

  Completed:
  - Removed stale system context and claude session files (code)

---

COMMITS 26/04/18-00:00 C200549 [x] [general] [task] (auto) — Update system context and memory files after CLI session

  Completed:
  - System context and memory files updated post-session (docs)

---

COMMITS 26/04/18-00:00 C200550 [x] [general] [task] (auto) — Refactor work item columns and memory promotion system

  Requirements:
  - Rename AI-related work item columns in database
  - Streamline memory planner message building
  - Enhance memory promotion logic with batch operations
  - Update work item routing to use renamed columns

  Completed:
  - Database migration m025 renaming work item AI columns (code)
  - MemoryPromotion class refactored with promote_all_work_items method (code)
  - Work item routes updated to reflect column name changes (code)

---

COMMITS 26/04/18-00:00 C200551 [x] [memory-search-and-embedding] [feature] (auto) — Add memory search and embedding support to promotion system

  Requirements:
  - Implement memory search in tool handlers
  - Add work item embedding capability to promotion
  - Extract work items from events during promotion

  Completed:
  - tool_memory._handle_search_memory function with search logic (code)
  - MemoryPromotion._embed_work_item and event extraction methods (code)

---

COMMITS 26/04/18-00:00 C200552 [x] [deliveries-tracking] [feature] (auto) — Add deliveries table and feature snapshot endpoints

  Requirements:
  - Create deliveries table and CRUD operations
  - Add delivery tracking to tag management
  - Implement feature snapshot database migration
  - Extend tag routes with delivery endpoints

  Completed:
  - Database migration m028 adding deliveries table (code)
  - DeliveryCreate model and CRUD functions in route_tags (code)
  - Tag update endpoints enhanced with delivery support (code)

---

COMMITS 26/04/18-00:00 C200553 [x] [feature-snapshot-generation] [feature] (auto) — Implement feature snapshot generation and promotion

  Requirements:
  - Create MemoryFeatureSnapshot class for snapshot generation
  - Add baseline loading and recent events tracking
  - Implement markdown snapshot writing with structured data
  - Add snapshot promotion and user-facing APIs

  Completed:
  - New MemoryFeatureSnapshot class (435 LOC) with full snapshot pipeline (code)
  - Database migration m029 for feature snapshot support (code)
  - Feature snapshot endpoints: create, get, promote in route_tags (code)

---

COMMITS 26/04/18-00:00 C200554 [x] [general] [task] (auto) — Update system context and memory files after CLI session

  Completed:
  - Updated system context and memory documentation files (docs)

---

COMMITS 26/04/18-00:00 C200555 [x] [general] [task] (auto) — Refactor work item columns and memory promotion system

  Requirements:
  - Rename work item AI columns in database migration
  - Update memory planner message building logic
  - Refactor memory promotion to extract and promote work items
  - Update work item API endpoints to use new column names

  Completed:
  - Database migration m025_rename_work_item_ai_columns added (code)
  - MemoryPlanner methods refactored for message building (code)
  - MemoryPromotion class refactored with promote_all_work_items method (code)
  - Work item API endpoints updated (search, list, create, patch, merge) (code)

---

COMMITS 26/04/18-00:00 C200556 [x] [discovery] [feature] (auto) — Add memory search tool and embeddings to work item promotion

  Requirements:
  - Implement memory search handler in tool_memory
  - Add embedding generation for work item promotion
  - Add event extraction to work item promotion

  Completed:
  - tool_memory._handle_search_memory function implemented (code)
  - memory_promotion._embed_work_item function added (code)
  - MemoryPromotion.extract_work_items_from_events method enhanced (code)

---

COMMITS 26/04/18-00:00 C200557 [x] [discovery] [feature] (auto) — Add deliveries table and update tag management API

  Requirements:
  - Create database migration for deliveries table
  - Add DeliveryCreate model to tags router
  - Implement list_deliveries, create_delivery, delete_delivery endpoints
  - Update tag detail retrieval to include deliveries

  Completed:
  - Database migration m028_add_deliveries created (code)
  - DeliveryCreate class added to route_tags (code)
  - Deliveries CRUD endpoints implemented (code)
  - Tag detail retrieval updated to include deliveries (code)

---

COMMITS 26/04/18-00:00 C200558 [x] [feature-snapshot] [feature] (auto) — Implement feature snapshot generation and promotion system

  Requirements:
  - Create database migration for feature snapshot table
  - Build MemoryFeatureSnapshot class with snapshot generation logic
  - Implement snapshot markdown generation from work items
  - Add feature snapshot API endpoints (create, get, promote)

  Completed:
  - Database migration m029_feature_snapshot created (code)
  - New MemoryFeatureSnapshot class (435 lines) with full implementation (code)
  - Snapshot markdown writing and event loading functionality (code)
  - API endpoints: create_feature_snapshot, get_feature_snapshot, promote_feature_snapshot (code)

---

COMMITS 26/04/18-00:00 C200564 [x] [general] [task] (auto) — Clean up legacy system context files and add pipeline run logging

  Requirements:
  - Remove stale agent context files from session 603
  - Add pipeline run logging and synchronization
  - Enhance workflow template and pipeline status endpoints
  - Improve work item matching and embedding

  Completed:
  - Added pipeline_run_sync, _insert_run, _finish_run, pipeline_run functions in pipeline_log.py (code)
  - Enhanced route_memory.py with get_workflow_templates, create_session_summary, get_pipeline_status (code)
  - Added workflow picker UI component and document viewer improvements (code)
  - Refactored commit extraction and embedding background tasks in route_git.py (code)

---

COMMITS 26/04/18-00:00 C200565 [x] [general] [task] (auto) — Clean up stale agent context and legacy system files

  Requirements:
  - Remove obsolete agent context files

  Completed:
  - Removed stale agent context and legacy system files (code)

---

COMMITS 26/04/18-00:00 C200566 [x] [general] [task] (auto) — Add database maintenance utilities and consolidate system context

  Requirements:
  - Add database cleanup and vacuum functionality
  - Create maintenance utilities for PostgreSQL
  - Consolidate system context and memory files

  Completed:
  - Added clean_pg_db.py with _raw_conn, _bytes_to_mb, run_maintenance, run_maintenance_async, _cli functions (code)
  - Enhanced route_admin.py with db_vacuum endpoint (code)

---

COMMITS 26/04/18-00:00 C200567 [x] [general] [task] (auto) — Remove stale agent context and system documentation files

  Requirements:
  - Remove obsolete agent context files
  - Remove generated system documentation

  Completed:
  - Removed stale agent context and generated system documentation files (code)

---

COMMITS 26/04/18-00:00 C200568 [x] [general] [task] (auto) — Clean up stale agent context and generated system files

  Requirements:
  - Remove obsolete agent context files
  - Remove generated system files

  Completed:
  - Removed stale agent context and generated system files (code)

---

COMMITS 26/04/18-00:00 C200559 [x] [general] [task] (auto) — Clean up legacy system context files and refactor pipeline/workflow routing

  Requirements:
  - Remove obsolete agent context files from Claude CLI session 603
  - Refactor pipeline logging and run tracking
  - Update git and work item routing with improved background processing
  - Add workflow picker UI component

  Completed:
  - Added pipeline_run_sync, _insert_run, _finish_run functions to pipeline_log.py (code)
  - Updated route_git.py background processing functions with improved code/commit handling (code)
  - Enhanced route_memory.py with workflow templates and pipeline status endpoints (code)
  - Added showWorkflowPicker UI component and document viewer improvements (code)
  - Modified db_migrations.py with m030_pipeline_runs migration (code)

---

COMMITS 26/04/18-00:00 C200560 [x] [general] [task] (auto) — Clean up stale agent context and legacy system files

  Requirements:
  - Remove obsolete agent context files

  Completed:
  - Removed stale agent context files from repository (code)

---

COMMITS 26/04/18-00:00 C200561 [x] [general] [task] (auto) — Consolidate system context/memory files and add database maintenance utilities

  Requirements:
  - Consolidate and restructure system context files
  - Add database maintenance and cleanup utilities
  - Implement database vacuum functionality in admin routes

  Completed:
  - Added clean_pg_db.py with _raw_conn, _bytes_to_mb, run_maintenance, run_maintenance_async functions (code)
  - Added CLI interface for database maintenance operations (code)
  - Enhanced route_admin.py with db_vacuum endpoint (code)

---

COMMITS 26/04/18-00:00 C200562 [x] [general] [task] (auto) — Remove stale agent context and system documentation files

  Requirements:
  - Remove obsolete agent context files
  - Clean up generated system documentation

  Completed:
  - Removed stale agent context and documentation files (code)

---

COMMITS 26/04/18-00:00 C200563 [x] [general] [task] (auto) — Clean up stale agent context and generated system files after Claude session

  Requirements:
  - Remove obsolete agent context files
  - Clean up generated system files from Claude CLI session

  Completed:
  - Removed stale agent context and generated system files (code)

