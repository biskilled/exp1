# Backlog

> Review each use case group. Approve `[+]` items, reject `[-]`.
> Run `POST /memory/{project}/work-items/sync` to merge approved items into use cases.

## **ui-rendering-bugs** · 26/03/10-00:11 [ ] (claude)
> Type: new
> Total: 30 prompts
> User tags: phase:bugfix
> AI existing:
> Requirements: Archive feature prevents reactivation of items; Request to add 3-dot menu for task details (remark, due date, created, archived status); Request to add tags to new chats for association; History should display full prompt and LLM response, not truncated text


  PROMPTS P102267 [ ] [feature] [in-progress] [1] — User reports history shows only small text instead of full prompt/LLM response and requests copy fun
    Requirements: H; i; s; t; o
    Deliveries: A; c; k; n; o

  PROMPTS P102299 [ ] [feature] [completed] [4] — Added work items UI panel with date formatting and visual improvements after backend SQL restart.
    Requirements: U; s; e; r;  
    Deliveries: I; m; p; l; e

  PROMPTS P102304 [ ] [feature] [completed] [4] — Implemented sticky headers, AI tag suggestions per row with approve/reject actions, and improved tag
    Requirements: U; s; e; r;  
    Deliveries: M; a; d; e;  

  PROMPTS P102309 [ ] [feature] [in-progress] [3] — Add table padding, fix date display, implement tag color coding (green/red/blue), and debug missing
    Requirements: A; d; d;  ; l
    Deliveries: A; d; d; e; d

  PROMPTS P102349 [ ] [feature] [in-progress] [3] — Fix UI not updating, restore latest prompts display, add tag option to user prompts, and investigate
    Requirements: U; I;  ; c; h
    Deliveries: F; i; x; e; d

  PROMPTS P102350 [ ] [feature] [in-progress] [3] — Add timestamp next to YOU, display session ID in left/top panels, and add per-prompt tag functionali
    Requirements: E; a; c; h;  
    Deliveries: S; e; s; s; i

  PROMPTS P102351 [ ] [feature] [in-progress] [3] — Update session header display, add session ID banner, and implement per-prompt tags in chat tab.
    Requirements: S; e; s; s; i
    Deliveries: S; e; s; s; i

  PROMPTS P102142 [ ] [bug] [completed] [4] — Diagnosed bind error on port 8000 caused by stale uvicorn instance; verified backend is healthy.
    Requirements: U; I;  ; n; o
    Deliveries: I; d; e; n; t

  PROMPTS P102172 [ ] [bug] [completed] [4] — Fixed phase persistence issue where app load showed 'required' and phase didn't update on session sw
    Requirements: P; h; a; s; e
    Deliveries: R; o; o; t;  

  PROMPTS P102173 [ ] [bug] [completed] [4] — Implemented phase persistence across sessions and added phase filtering to Commit history view.
    Requirements: C; a; n; n; o
    Deliveries: R; e; m; o; v

  PROMPTS P102174 [ ] [bug] [completed] [4] — Restored session-specific phase handling and fixed phase visibility across Chat, History, and Commit
    Requirements: C; a; n; n; o
    Deliveries: R; e; s; t; o

  PROMPTS P102175 [ ] [bug] [completed] [4] — Verified phase change persistence and session metadata updates for both new and existing sessions.
    Requirements: U; p; l; o; a
    Deliveries: C; o; n; f; i

  PROMPTS P102176 [ ] [bug] [completed] [4] — Fixed red warning badge display for all sessions without phase and phase persistence for CLI/WF sess
    Requirements: R; e; d;  ; f
    Deliveries: R; e; m; o; v

  PROMPTS P102196 [ ] [bug] [in-progress] [1] — User reports missing aiCli project and slow PROJECT.md loading (>1min), suspects DB query issue.
    Requirements: a; i; C; l; i
    Deliveries: A; c; k; n; o

  PROMPTS P102212 [ ] [bug] [completed] [4] — Fixed project loading retry logic to handle empty results and backend startup delays.
    Requirements: a; i; C; l; i
    Deliveries: U; p; d; a; t

  PROMPTS P102268 [ ] [bug] [completed] [4] — Fixed history display to show both prompt and LLM response using consistent hooks and backend calls.
    Requirements: H; i; s; t; o
    Deliveries: V; e; r; i; f

  PROMPTS P102300 [ ] [bug] [completed] [4] — Improved work items panel header clarity with wider columns, better padding, and visual separation.
    Requirements: W; o; r; k;  
    Deliveries: W; i; d; e; n

  PROMPTS P102301 [ ] [bug] [in-progress] [3] — Fixed date formatting to yy/mm/dd-hh:mm and removed non-work-item tags (Shared-memory, billing) from
    Requirements: D; a; t; e;  
    Deliveries: U; p; d; a; t

  PROMPTS P102307 [ ] [bug] [in-progress] [3] — Fixed work items panel layout to display tags properly and expand description to full row width.
    Requirements: T; a; g; s;  
    Deliveries: U; p; d; a; t

  PROMPTS P102308 [ ] [bug] [completed] [4] — Restore table layout and add labeled tag rows (AI/User) with descriptions.
    Requirements: L; a; s; t;  
    Deliveries: R; e; s; t; o

  PROMPTS P102341 [ ] [bug] [in-progress] [2] — Fix UI category/bug display issue and work_item disappearance after tag acceptance.
    Requirements: P; l; a; n; n
    Deliveries: V; e; r; i; f

  PROMPTS P102342 [ ] [bug] [completed] [4] — Fix duplicate const declaration causing Electron empty load.
    Requirements: E; l; e; c; t
    Deliveries: I; d; e; n; t

  PROMPTS P102355 [ ] [bug] [completed] [4] — Fix incomplete prompt loading by merging DB entries with JSONL file data and correct sorting.
    Requirements: O; n;  ; s; y
    Deliveries: I; m; p; l; e

  PROMPTS P102356 [ ] [bug] [in-progress] [3] — Fix stale session ID loading by resetting module variables and implementing auto-select for current
    Requirements: L; o; a; d; s
    Deliveries: R; e; s; e; t

  PROMPTS P102357 [ ] [bug] [completed] [5] — Load current session on startup by synchronously reading last_session_id from runtime state.
    Requirements: O; n;  ; s; t
    Deliveries: M; o; d; i; f

  PROMPTS P102143 [ ] [task] [completed] [4] — Provided clean restart procedure using dev script with NODE_ENV=development after killing stale back
    Requirements: C; a; n; n; o
    Deliveries: C; o; n; f; i

  PROMPTS P102151 [ ] [task] [completed] [4] — Explained tag bar location and accept workflow; fixed overflow clipping issue.
    Requirements: U; s; e; r;  
    Deliveries: L; o; c; a; t

  PROMPTS P102195 [ ] [task] [in-progress] [1] — Investigated project loading performance issues and requested details on slow Summary and History lo
    Requirements: P; r; o; j; e
    Deliveries: I; n; i; t; i

  PROMPTS P102298 [ ] [task] [completed] [4] — Instructed user to perform hard refresh to see UI changes (Cmd+Shift+R or Ctrl+Shift+R).
    Requirements: U; s; e; r;  
    Deliveries: P; r; o; v; i

---

## **database-schema-refactor** · 26/03/09-04:08 [ ] (claude)
> Type: new
> Total: 47 prompts
> User tags:
> AI existing:
> Requirements: Merge pr_embeddings and pr_memory_events into mem_ai_events table; Include fields: id (uuid), project_id, session_id, session_desc, chunk, content, created_at; Implement smart embedding with chunking mechanism; Support code understanding for commits; Implement mng_ai_tags_relations table for tagging relationships

  PROMPTS P102215 [ ] [feature] [in-progress] [3] — Merged pr_embeddings and pr_memory_events into single mem_ai_events table.
    Requirements: M; e; r; g; e
    Deliveries: C; o; m; m; i

  PROMPTS P102216 [ ] [feature] [in-progress] [3] — Enhanced memory tagging system with mem_ai_tags_relations and tag management.
    Requirements: I; m; p; l; e
    Deliveries: C; o; m; m; i

  PROMPTS P102218 [ ] [feature] [in-progress] [3] — Implemented manual tag relations management via developer CLI commands.
    Requirements: S; u; p; p; o
    Deliveries: C; o; m; m; i

  PROMPTS P102246 [ ] [feature] [in-progress] [0] — Implement tagging mechanism with user-editable tags column in work items.
    Requirements: R; e; p; l; a

  PROMPTS P102257 [ ] [feature] [in-progress] [1] — Add language tags, improve file_change data structure with file paths and row counts.
    Requirements: A; d; d;  ; l

  PROMPTS P102264 [ ] [feature] [in-progress] [0] — Create mng_projects table and migrate project references from text to foreign key.
    Requirements: C; r; e; a; t

  PROMPTS P102217 [ ] [bug] [completed] [4] — Fixed table naming error: mng_ai_tags_relations corrected to mem_ai_tags_relations.
    Requirements: F; i; x;  ; i
    Deliveries: C; o; m; m; i

  PROMPTS P102224 [ ] [bug] [completed] [4] — Fix database DDL changes not visible in database; refactor database.py for persistence.
    Requirements: E; n; s; u; r
    Deliveries: C; o; m; m; i

  PROMPTS P102248 [ ] [bug] [in-progress] [1] — Fix undefined column error (lifecycle) and optimize slow commit loading queries.
    Requirements: F; i; x;  ; p
    Deliveries: S; y; s; t; e

  PROMPTS P102249 [ ] [bug] [in-progress] [1] — Fix undefined column error (work_item_id) in work items route query.
    Requirements: F; i; x;  ; p
    Deliveries: S; y; s; t; e

  PROMPTS P102254 [ ] [bug] [in-progress] [1] — Verify column reordering in mem_ai_events table—llm_source and embedding not updated.
    Requirements: C; o; n; f; i
    Deliveries: A; I;  ; s; y

  PROMPTS P102139 [ ] [task] [completed] [4] — Updated /memory context files and project documentation for next steps.
    Requirements: U; p; d; a; t
    Deliveries: M; E; M; O; R

  PROMPTS P102202 [ ] [task] [in-progress] [3] — Restructured database tables with mng_, cl_, pr_ naming convention.
    Requirements: R; e; m; o; v
    Deliveries: D; a; t; a; b

  PROMPTS P102203 [ ] [task] [completed] [4] — Executed database migration removing 5 stale tables, consolidated to 24 tables.
    Requirements: R; u; n;  ; d
    Deliveries: D; r; o; p; p

  PROMPTS P102204 [ ] [task] [in-progress] [2] — Clarified table categorization: memory_items and project_facts belong in project tables.
    Requirements: E; x; p; l; a
    Deliveries: M; E; M; O; R

  PROMPTS P102205 [ ] [task] [completed] [4] — Verified mng_session_tags usage and clarified project table structure.
    Requirements: V; e; r; i; f
    Deliveries: C; o; n; f; i

  PROMPTS P102207 [ ] [task] [in-progress] [2] — Implemented 3-layer table structure: mng_ (general), cl_ (client), pr_ (project).
    Requirements: A; l; i; g; n
    Deliveries: 3; -; l; a; y

  PROMPTS P102219 [ ] [task] [completed] [4] — Rename project facts and work items tables, add features table with upsert triggers.
    Requirements: R; e; n; a; m
    Deliveries: C; o; m; m; i

  PROMPTS P102220 [ ] [task] [completed] [4] — Auto-regenerate memory files (CLAUDE.md, MEMORY.md, etc.) based on project facts and work items upse
    Requirements: A; u; t; o; -
    Deliveries: C; o; m; m; i

  PROMPTS P102221 [ ] [task] [completed] [4] — Provide updated aicli_memory structure and document new memory layers and tagging relationships.
    Requirements: U; p; d; a; t
    Deliveries: C; o; m; m; i

  PROMPTS P102222 [ ] [task] [completed] [4] — Merge pr_session_summaries into mem_ai_events with event_type column for session summary events.
    Requirements: M; e; r; g; e
    Deliveries: C; o; m; m; i

  PROMPTS P102223 [ ] [task] [completed] [4] — Add missing llm_source column to mem_ai_events and audit unused columns like language and file_path.
    Requirements: A; d; d;  ; l
    Deliveries: C; o; m; m; i

  PROMPTS P102225 [ ] [task] [completed] [4] — Remove unused columns from mem_ai_events; move summary_tags to mem_ai_tags linked by row ID with AI-
    Requirements: R; e; m; o; v
    Deliveries: C; o; m; m; i

  PROMPTS P102226 [ ] [task] [completed] [4] — Refactor mem_mrr_* tables: remove unused columns, consolidate tags, change commit ID to integer, fix
    Requirements: R; e; m; o; v
    Deliveries: C; o; m; m; i

  PROMPTS P102228 [ ] [task] [completed] [4] — Apply same refactoring (remove unused columns, fix keys) to all mem_ai_* tables.
    Requirements: A; u; d; i; t
    Deliveries: C; o; m; m; i

  PROMPTS P102230 [ ] [task] [completed] [4] — Reduce database.py file size by removing old migrations and boilerplate code.
    Requirements: R; e; m; o; v
    Deliveries: C; o; m; m; i

  PROMPTS P102236 [ ] [task] [in-progress] [1] — Review database files and remove obsolete tables from codebase.
    Requirements: R; e; v; i; e
    Deliveries: S; y; s; t; e

  PROMPTS P102245 [ ] [task] [in-progress] [1] — Address incomplete table structure cleanup—old tables still present.
    Requirements: R; e; m; o; v
    Deliveries: S; y; s; t; e

  PROMPTS P102252 [ ] [task] [in-progress] [1] — Restructure mem_ai_events table: move llm_source, consolidate tags/metadata, use JSONB.
    Requirements: M; o; v; e;  
    Deliveries: S; y; s; t; e

  PROMPTS P102253 [ ] [task] [in-progress] [0] — Reorder table columns (llm_source after project, embedding at end) and clean database.py.
    Requirements: M; o; v; e;  

  PROMPTS P102255 [ ] [task] [completed] [4] — Rename mem_ai_events to old, create new table, and migrate data.
    Requirements: R; e; n; a; m
    Deliveries: S; y; s; t; e

  PROMPTS P102256 [ ] [task] [in-progress] [1] — Clarify usage of doc_type, language, file_path columns and session_action_item reusability.
    Requirements: E; x; p; l; a
    Deliveries: S; y; s; t; e

  PROMPTS P102258 [ ] [task] [completed] [2] — Investigate chunk and chunk_type fields; consider moving to tags dictionary.
    Requirements: C; l; a; r; i
    Deliveries: S; y; s; t; e

  PROMPTS P102259 [ ] [task] [in-progress] [2] — Clean invalid historical events, verify llm_source population, update memory table.
    Requirements: R; e; m; o; v
    Deliveries: S; y; s; t; e

  PROMPTS P102265 [ ] [task] [completed] [2] — Verify prompt structure after client_id fix.
    Requirements: V; e; r; i; f
    Deliveries: S; y; s; t; e

  PROMPTS P102272 [ ] [task] [completed] [4] — Audit work_items columns: clarify source_session_id, content, summary, requirements usage.
    Requirements: C; l; a; r; i
    Deliveries: C; o; m; p; l

  PROMPTS P102284 [ ] [task] [completed] [4] — Verify diff_summary and diff_details columns in commits table are necessary.
    Requirements: C; o; n; f; i
    Deliveries: C; l; a; r; i

  PROMPTS P102285 [ ] [task] [in-progress] [3] — Investigate commit table data capture: verify hook functionality, row change counts, files tag usage
    Requirements: V; e; r; i; f
    Deliveries: I; d; e; n; t

  PROMPTS P102286 [ ] [task] [in-progress] [0] — Design extraction flow for aggregating commits linked via pr_tags_map.
    Requirements: D; e; s; i; g

  PROMPTS P102287 [ ] [task] [completed] [4] — Verify database updates: confirm commit_short_hash and generated columns applied.
    Requirements: V; e; r; i; f
    Deliveries: c; o; m; m; i

  PROMPTS P102293 [ ] [task] [completed] [4] — Created db_schema.sql canonical schema file with all tables, indexes, and FK constraints.
    Requirements: S; e; p; a; r
    Deliveries: C; r; e; a; t

  PROMPTS P102344 [ ] [task] [completed] [4] — Implemented table migrations m035-m036 with column reordering and cleanup of old tables.
    Requirements: R; e; t; r; y
    Deliveries: C; r; e; a; t

  PROMPTS P102345 [ ] [task] [completed] [3] — Analyzed importance column usage in events table.
    Requirements: E; v; a; l; u
    Deliveries: C; o; d; e;  

  PROMPTS P102346 [ ] [task] [completed] [5] — Applied migration m037 to drop importance column from mem_ai_events table.
    Requirements: D; r; o; p;  
    Deliveries: C; r; e; a; t

  PROMPTS P102348 [ ] [task] [completed] [5] — Applied migrations m037-m047 including column drops, reordering, and system event tracking.
    Requirements: D; r; o; p;  
    Deliveries: C; r; e; a; t

  PROMPTS P102358 [ ] [task] [completed] [5] — Created migration m051 to convert user_id from string to int and add updated_at to all tables.
    Requirements: C; h; a; n; g
    Deliveries: C; r; e; a; t

  PROMPTS P102359 [ ] [task] [completed] [5] — Created migration m052 to reorder all table columns with standard column ordering rules.
    Requirements: R; e; o; r; d
    Deliveries: C; r; e; a; t

---

## **memory-layer-implementation** · 26/03/09-17:56 [ ] (claude)
> Type: new
> Total: 62 prompts
> User tags:
> AI existing:
> AI new: [feature:memory-layers]
> Requirements: Consolidate Planner tabs (Feature, Tags, Bugs, Tags) into one tag management interface; Support category-based tag hierarchy with properties (status, description, due date, user created); Add tag listbox in chat (+) menu showing active tags with add option; Make AI suggestions more visible with clear approval mechanism; Clarify which session suggestions apply to

  PROMPTS P102141 [ ] [feature] [in-progress] [2] — User proposes redesigning Planner from 4 tabs to single tag management interface with category hiera
    Requirements: C; o; n; s; o

  PROMPTS P102152 [ ] [feature] [completed] [4] — AI suggestions banner added to chat UI, Phase selector clarified, and session context improved.
    Requirements: M; a; k; e;  
    Deliveries: P; h; a; s; e

  PROMPTS P102153 [ ] [feature] [completed] [4] — Fixed /memory suggestions to work offline, added history router, and enabled session-to-commit linki
    Requirements: R; u; n;  ; /
    Deliveries: /; m; e; m; o

  PROMPTS P102159 [ ] [feature] [completed] [4] — Optimized tag loading with caching, persisted tag colors, and unified tag save mechanism for commits
    Requirements: C; a; c; h; e
    Deliveries: T; a; g;  ; c

  PROMPTS P102161 [ ] [feature] [completed] [4] — Added prompt-to-commit linking, showing which specific prompts triggered which commits in sessions.
    Requirements: C; r; e; a; t
    Deliveries: C; o; m; m; i

  PROMPTS P102165 [ ] [feature] [completed] [4] — Deduplicated 149 tags across History/Chat/Commits and added DELETE endpoints for tag removal.
    Requirements: E; n; s; u; r
    Deliveries: C; o; n; f; i

  PROMPTS P102167 [ ] [feature] [completed] [4] — Linked commits to specific prompts in History/Chat view using prompt_source_id matching.
    Requirements: L; i; n; k;  
    Deliveries: `; /; h; i; s

  PROMPTS P102171 [ ] [feature] [completed] [4] — Auto-save AI suggestions as tags to session with proper category, filter by phase, and remove featur
    Requirements: S; a; v; e;  
    Deliveries: `; _; a; c; c

  PROMPTS P102180 [ ] [feature] [completed] [4] — Implemented `GET /entities/summary` endpoint and enhanced `/memory` command to retrieve and synthesi
    Requirements: V; e; r; i; f
    Deliveries: N; e; w;  ; `

  PROMPTS P102182 [ ] [feature] [in-progress] [0] — User requested adding mng table to track prompt count and notify via aicli when /memory runs.
    Requirements: A; d; d;  ; a

  PROMPTS P102190 [ ] [feature] [in-progress] [3] — Designed workflow system comparing specrails and paperclip, proposed role-based architecture with ag
    Requirements: D; e; s; i; g
    Deliveries: C; o; m; p; r

  PROMPTS P102192 [ ] [feature] [completed] [4] — Designed database schema for agent roles with versioning, supporting prompt editing by admins/super-
    Requirements: S; t; o; r; e
    Deliveries: D; e; s; i; g

  PROMPTS P102200 [ ] [feature] [completed] [4] — Implemented nested tag hierarchy and mapped tagging to Planner, including inline child tag creation.
    Requirements: V; e; r; i; f
    Deliveries: R; e; n; a; m

  PROMPTS P102232 [ ] [feature] [in-progress] [2] — User questioned lack of embeddings in project_facts and work_items, requested MCP server update for
    Requirements: A; d; d;  ; e
    Deliveries: C; o; m; m; i

  PROMPTS P102247 [ ] [feature] [completed] [4] — Implemented tag bidirectional linking and referencing between commits and prompts.
    Requirements: F; i; x;  ; U
    Deliveries: C; o; m; m; i

  PROMPTS P102252 [ ] [feature] [completed] [4] — Refactored mem_ai_events table schema to consolidate tags/metadata and use JSONB columns.
    Requirements: M; o; v; e;  
    Deliveries: C; o; m; m; i

  PROMPTS P102262 [ ] [feature] [in-progress] [1] — Consolidated feature_snapshot into tags, linked work_items to events, and aligned three-layer archit
    Requirements: M; e; r; g; e

  PROMPTS P102291 [ ] [feature] [completed] [4] — Implemented prompt-to-event-to-commit linking and work item event aggregation
    Requirements: L; i; n; k;  
    Deliveries: O; p; t; i; m

  PROMPTS P102296 [ ] [feature] [completed] [4] — Implemented FK-based work item to event/commit linking via migrations
    Requirements: C; r; e; a; t
    Deliveries: D; e; s; i; g

  PROMPTS P102303 [ ] [feature] [completed] [4] — Implemented sticky header and AI tag suggestion approval workflow in UI
    Requirements: K; e; e; p;  
    Deliveries: A; d; d; e; d

  PROMPTS P102310 [ ] [feature] [in-progress] [3] — Implemented category-aware AI tag suggestion prioritizing task/bug/feature
    Requirements: U; p; d; a; t
    Deliveries: U; p; d; a; t

  PROMPTS P102312 [ ] [feature] [in-progress] [3] — Fixed AI tag suggestion visibility and added event counter to work items
    Requirements: D; e; b; u; g
    Deliveries: U; p; d; a; t

  PROMPTS P102319 [ ] [feature] [completed] [4] — Addressed query performance, DIGEST column confusion, and enabled user approval for AI tags.
    Requirements: E; x; p; l; a
    Deliveries: A; d; d; e; d

  PROMPTS P102326 [ ] [feature] [completed] [5] — Populated work_item tags from mirror events and enabled code_summary and AI criteria fields.
    Requirements: E; x; p; l; a
    Deliveries: s; t; a; r; t

  PROMPTS P102163 [ ] [bug] [completed] [4] — Fixed hook noise filtering, corrected task-notification logging errors, added pagination and prompt-
    Requirements: F; i; x;  ; h
    Deliveries: H; o; o; k;  

  PROMPTS P102170 [ ] [bug] [completed] [4] — Fixed git hook to properly link last 9 commits to prompts via session_id and Phase 5 sync.
    Requirements: L; a; s; t;  
    Deliveries: R; o; o; t;  

  PROMPTS P102178 [ ] [bug] [completed] [4] — Fixed session tag propagation to History/Commits: backfilled phase field and populated commit phase
    Requirements: T; a; g; s;  
    Deliveries: `; _; b; a; c

  PROMPTS P102239 [ ] [bug] [completed] [4] — Fixed database column and naming errors in chat history loading routes.
    Requirements: F; i; x;  ; '
    Deliveries: C; o; m; m; i

  PROMPTS P102250 [ ] [bug] [completed] [4] — Restored tag attachment functionality and tag selection UI with search and creation.
    Requirements: F; i; x;  ; m
    Deliveries: C; o; m; m; i

  PROMPTS P102251 [ ] [bug] [completed] [3] — Fixed commit sync error in /history/commits/sync API batch upsert operation.
    Requirements: F; i; x;  ; e
    Deliveries: C; o; m; m; i

  PROMPTS P102282 [ ] [bug] [completed] [4] — Removed non-existent diff_summary column and fixed commit code extraction logic
    Requirements: C; h; e; c; k
    Deliveries: R; e; m; o; v

  PROMPTS P102292 [ ] [bug] [completed] [4] — Fixed missing ai_tags JSONB column in mem_ai_work_items table
    Requirements: F; i; x;  ; w
    Deliveries: A; d; d; e; d

  PROMPTS P102294 [ ] [bug] [completed] [4] — Fixed tag drawer rendering crash and field name mismatch in UI
    Requirements: F; i; x;  ; m
    Deliveries: F; i; x; e; d

  PROMPTS P102314 [ ] [bug] [completed] [4] — Fixed over-extraction of internal memory sync work items by adding exclusion rules to prompt.
    Requirements: E; x; p; l; a
    Deliveries: R; o; o; t;  

  PROMPTS P102315 [ ] [bug] [completed] [4] — Fixed event counter query to show only digest events and fixed UI column naming.
    Requirements: S; h; a; r; e
    Deliveries: F; i; x; e; d

  PROMPTS P102320 [ ] [bug] [completed] [4] — Fixed work item-to-commit linking by correcting source_id join logic in database query.
    Requirements: M; a; k; e;  
    Deliveries: I; d; e; n; t

  PROMPTS P102327 [ ] [bug] [completed] [4] — Fixed migration to correctly map ai_phase and ai_feature tags from session/commit sources.
    Requirements: C; l; a; r; i
    Deliveries: F; i; x; e; d

  PROMPTS P102347 [ ] [bug] [completed] [4] — Cleaned up event tags by removing system metadata and backfilling from mirror tables
    Requirements: S; h; o; w;  
    Deliveries: F; i; x; e; d

  PROMPTS P102140 [ ] [task] [in-progress] [1] — User requests AI to summarize large feature responses and improve /memory function with tagging sugg
    Requirements: S; u; m; m; a

  PROMPTS P102154 [ ] [task] [completed] [4] — Clarified MCP server usage (not directly used by Claude Code) and improved project context routing.
    Requirements: E; x; p; l; a
    Deliveries: E; x; p; l; a

  PROMPTS P102160 [ ] [task] [completed] [5] — System aligned to CLAUDE.md memory layers, /memory verification run successful, and project features
    Requirements: R; u; n;  ; /
    Deliveries: /; m; e; m; o

  PROMPTS P102162 [ ] [task] [completed] [5] — Implemented history.jsonl rotation, verified session_tags.json usage, and performed full codebase cl
    Requirements: C; h; e; c; k
    Deliveries: H; i; s; t; o

  PROMPTS P102166 [ ] [task] [completed] [4] — Verified tag logic alignment: session tags via Chat, prompt tags via History, commit tags linked to
    Requirements: V; e; r; i; f
    Deliveries: C; o; n; f; i

  PROMPTS P102168 [ ] [task] [completed] [4] — Updated memory/docs for all sessions and explained MCP accessibility for new CLI/LLM sessions.
    Requirements: R; u; n;  ; /
    Deliveries: R; a; n;  ; `

  PROMPTS P102179 [ ] [task] [completed] [4] — Optimized database schema with real columns, indexes, and improved tag/phase retrieval for MCP effic
    Requirements: E; n; s; u; r
    Deliveries: A; d; d; e; d

  PROMPTS P102181 [ ] [task] [in-progress] [4] — Provided prioritized roadmap for full memory and project management lifecycle with quick wins and lo
    Requirements: I; d; e; n; t
    Deliveries: P; r; i; o; r

  PROMPTS P102185 [ ] [task] [in-progress] [3] — Audited tag usage, fixed gaps in interaction_tags pipeline and session_bulk_tag function.
    Requirements: C; h; e; c; k
    Deliveries: I; d; e; n; t

  PROMPTS P102186 [ ] [task] [completed] [4] — Provided comprehensive summary of 7-part system improvements including memory stack, distillation la
    Requirements: S; u; m; m; a
    Deliveries: D; e; s; c; r

  PROMPTS P102206 [ ] [task] [completed] [4] — Eliminated all mng_graph_* references, refactored to use dynamic project_table() calls across 4 file
    Requirements: C; l; e; a; n
    Deliveries: R; e; m; o; v

  PROMPTS P102214 [ ] [task] [in-progress] [2] — User requested review of system state before phase 2 refactor; commit made with AI context and sessi
    Requirements: A; s; s; e; s
    Deliveries: C; o; m; m; i

  PROMPTS P102233 [ ] [task] [in-progress] [2] — User requested comparison of current memory config vs previous version to assess improvement in proj
    Requirements: C; o; m; p; a
    Deliveries: C; o; m; m; i

  PROMPTS P102260 [ ] [task] [in-progress] [0] — Mark 'llm_source' tag as visible in UI.
    Requirements: M; a; k; e;  

  PROMPTS P102261 [ ] [task] [in-progress] [0] — Create comprehensive memory layer documentation describing all layers and data flow.
    Requirements: B; u; i; l; d

  PROMPTS P102271 [ ] [task] [in-progress] [3] — Updated memory documentation and assessed need for session memory layer in infrastructure.
    Requirements: U; p; d; a; t
    Deliveries: C; o; m; m; i

  PROMPTS P102278 [ ] [task] [completed] [5] — Synced and updated all memory files with incremental data from 211 history rows.
    Requirements: R; u; n;  ; /
    Deliveries: G; e; n; e; r

  PROMPTS P102289 [ ] [task] [completed] [4] — Traced and documented full commit pipeline showing prompt usage locations
    Requirements: E; x; p; l; a
    Deliveries: I; d; e; n; t

  PROMPTS P102295 [ ] [task] [completed] [4] — Assessed cost and completeness of mem_mrr_commits_code population
    Requirements: V; e; r; i; f
    Deliveries: C; o; s; t;  

  PROMPTS P102313 [ ] [task] [completed] [4] — Located and documented all prompts for ai_tags and work_item extraction across memory system.
    Requirements: F; i; n; d;  
    Deliveries: P; r; o; v; i

  PROMPTS P102321 [ ] [task] [completed] [4] — Explained why commit-sourced work items have no linked prompts and ran memory update.
    Requirements: C; l; a; r; i
    Deliveries: E; x; t; r; a

  PROMPTS P102328 [ ] [task] [completed] [4] — Clarified distinction between ai_desc (extracted) and summary (generated by promotion).
    Requirements: E; x; p; l; a
    Deliveries: s; u; m; m; a

  PROMPTS P102343 [ ] [task] [in-progress] [1] — Structured events table schema redesign and clarified source_id linking for multi-event items.
    Requirements: R; e; o; r; g

  PROMPTS P102352 [ ] [task] [in-progress] [0] — User asked to verify hook-log functionality after m050 migration
    Requirements: V; e; r; i; f

---

## **performance-optimization** · 26/03/10-00:52 [ ] (claude)
> Type: new
> Total: 11 prompts
> User tags:
> AI existing:
> AI new: [task:perf-optimization]
> Requirements: Reduce multiple database calls by loading data once on project access; Cache tags in memory for chat and tag tab usage; Implement smart dropdown with category filter and add new value option; Update memory and database in background on save; Fix nested work partial display (works in doc_type, broken in bug/feature UI)

  PROMPTS P102144 [ ] [feature] [completed] [4] — Optimized database calls by caching tags in memory and implementing smart category-value dropdown wi
    Requirements: R; e; d; u; c
    Deliveries: N; e; w;  ; p

  PROMPTS P102201 [ ] [bug] [completed] [4] — Fixed nested work item rendering inconsistency across categories and clarified lifecycle and pipelin
    Requirements: F; i; x;  ; n
    Deliveries: F; i; x; e; d

  PROMPTS P102210 [ ] [bug] [completed] [4] — Fixed database schema errors, missing project loading, and removed duplicate tables.
    Requirements: F; i; x;  ; '
    Deliveries: R; e; m; o; v

  PROMPTS P102211 [ ] [bug] [completed] [3] — Fixed backend startup failures, memory endpoint code_dir variable error, and project selection displ
    Requirements: F; i; x;  ; b
    Deliveries: M; e; m; o; r

  PROMPTS P102241 [ ] [bug] [in-progress] [1] — No response provided to drag-and-drop and counter visibility issues.
    Requirements: F; i; x;  ; d
    Deliveries: C; o; m; m; i

  PROMPTS P102145 [ ] [task] [completed] [4] — Designed nested tags architecture with unlimited depth using parent_id and answered feasibility befo
    Requirements: O; p; t; i; m
    Deliveries: F; e; a; s; i

  PROMPTS P102183 [ ] [task] [completed] [4] — Cleaned up codebase by removing hardcoded values, moving config to dedicated config file, and optimi
    Requirements: C; h; e; c; k
    Deliveries: A; d; d; e; d

  PROMPTS P102184 [ ] [task] [in-progress] [0] — No response provided to restructure memory capabilities with compressed layers.
    Requirements: R; e; s; e; a

  PROMPTS P102191 [ ] [task] [completed] [4] — Explained hardcoded pipeline in work_item_pipeline.py and identified path to merge with workflow eng
    Requirements: L; o; c; a; t
    Deliveries: I; d; e; n; t

  PROMPTS P102318 [ ] [task] [completed] [4] — Optimized Planner and work items loading with 5 composite database indexes and followed query docume
    Requirements: O; p; t; i; m
    Deliveries: M; i; g; r; a

  PROMPTS P102319 [ ] [task] [in-progress] [2] — Addressed query performance, DIGEST column purpose, orphaned work items, and AI tag permissions.
    Requirements: E; x; p; l; a
    Deliveries: I; m; p; l; e

---

## **planner-tagging-workflow** · 26/03/10-01:14 [ ] (claude)
> Type: new
> Total: 49 prompts
> User tags:
> AI existing:
> AI new: [feature:planner-workflow]
> Requirements: User confirmed completion of parent-child tag relationship implementation; Concern about commit/hash linking to prompts and LLM answers; Need to use /memory to update summarized and embedded data; Confusion between History (summary + prompt) and Chat (all responses) display; Desire to store full history (prompts + LLM answers) while Chat shows short responses

  PROMPTS P102147 [ ] [feature] [completed] [5] — Confirmed hierarchical tag support (parent_id) implemented in database and frontend cache helpers.
    Requirements: U; s; e; r;  
    Deliveries: B; a; c; k; e

  PROMPTS P102158 [ ] [feature] [in-progress] [3] — Implemented tag-by-source-id endpoint to link history entries to entity tags for /memory updates.
    Requirements: C; o; n; c; e
    Deliveries: B; a; c; k; e

  PROMPTS P102164 [ ] [feature] [completed] [5] — Implemented pagination (◀ [page] / total ▶) for Chat, History, and Commits tabs.
    Requirements: A; d; d;  ; p
    Deliveries: B; a; c; k; e

  PROMPTS P102169 [ ] [feature] [completed] [4] — Fixed MCP config for current project and created automated MCP setup for new projects with IDE suppo
    Requirements: S; e; t;  ; u
    Deliveries: F; i; x; e; d

  PROMPTS P102200 [ ] [feature] [in-progress] [4] — Documented tagging mechanism with nested hierarchy and planner integration plan.
    Requirements: I; m; p; l; e
    Deliveries: T; a; b;  ; r

  PROMPTS P102240 [ ] [feature] [in-progress] [2] — Addressed Planner issues: lifecycle tags, bug counter, drag-drop nesting, and ai_suggestion placemen
    Requirements: C; l; a; r; i
    Deliveries: S; y; s; t; e

  PROMPTS P102244 [ ] [feature] [in-progress] [3] — Reorganized AI suggestions into separate section and enhanced drag-drop tag nesting.
    Requirements: M; o; v; e;  
    Deliveries: T; a; g;  ; r

  PROMPTS P102274 [ ] [feature] [in-progress] [2] — System documentation updated; drag-drop work item movement and panel resizing addressed.
    Requirements: I; m; p; l; e
    Deliveries: S; y; s; t; e

  PROMPTS P102277 [ ] [feature] [completed] [4] — Implemented work_item move/merge functionality with tag cleanup and side panel UI.
    Requirements: M; o; v; e;  
    Deliveries: M; o; d; i; f

  PROMPTS P102297 [ ] [feature] [in-progress] [2] — Added multi-column work_item table with name, desc, prompts, commits, date and sorting.
    Requirements: D; i; s; p; l
    Deliveries: S; a; n; i; t

  PROMPTS P102303 [ ] [feature] [completed] [4] — Made header sticky, added AI tag suggestions with approve/remove, and prepared memory update.
    Requirements: K; e; e; p;  
    Deliveries: A; d; d; e; d

  PROMPTS P102306 [ ] [feature] [completed] [4] — Implemented category:name AI tags (bug/feature/task), user tags display, and new tag suggestions wit
    Requirements: A; I;  ; t; a
    Deliveries: M; o; d; i; f

  PROMPTS P102310 [ ] [feature] [completed] [4] — Implemented hierarchical AI tag suggestion prioritizing task/bug/feature, then suggesting new catego
    Requirements: A; I;  ; s; u
    Deliveries: M; o; d; i; f

  PROMPTS P102332 [ ] [feature] [completed] [4] — Applied migration to clean planner_tags table with creator/updater fields and reordered columns.
    Requirements: C; r; e; a; t
    Deliveries: C; r; e; a; t

  PROMPTS P102334 [ ] [feature] [completed] [5] — Applied m027 migration removing AI-generated columns from planner_tags table.
    Requirements: R; e; m; o; v
    Deliveries: M; i; g; r; a

  PROMPTS P102335 [ ] [feature] [in-progress] [1] — Planning to add deliveries column to planner_tags with category/type taxonomy from mng_deliveries ta
    Requirements: A; d; d;  ; d

  PROMPTS P102337 [ ] [feature] [in-progress] [2] — Design specification for mem_ai_feature_snapshot table with use cases and delivery types.
    Requirements: C; r; e; a; t
    Deliveries: D; e; s; i; g

  PROMPTS P102338 [ ] [feature] [completed] [4] — Implemented feature_snapshot table with migration, schema, and Haiku prompt for use-case generation.
    Requirements: S; t; o; r; e
    Deliveries: A; d; d; e; d

  PROMPTS P102340 [ ] [feature] [in-progress] [1] — Implementation request for dashboard tab and pipeline execution from multiple entry points.
    Requirements: C; r; e; a; t

  PROMPTS P102353 [ ] [feature] [completed] [4] — Enhanced chat history view with session sidebar, full session IDs, timestamps (YY/MM/DD-HH:MM), and
    Requirements: A; d; d;  ; s
    Deliveries: L; e; f; t;  

  PROMPTS P102149 [ ] [bug] [completed] [5] — Fixed port binding restart issue by implementing freePort() to kill orphan uvicorn processes.
    Requirements: U; s; e; r;  
    Deliveries: I; m; p; l; e

  PROMPTS P102150 [ ] [bug] [in-progress] [3] — Added session-level tag persistence and GET endpoint to retrieve tagged entities per session.
    Requirements: T; a; g; s;  
    Deliveries: B; a; c; k; e

  PROMPTS P102201 [ ] [bug] [completed] [4] — Fixed Planner inconsistency by unifying tag renderers across all categories.
    Requirements: F; i; x;  ; n
    Deliveries: R; e; m; o; v

  PROMPTS P102275 [ ] [bug] [in-progress] [0] — Multiple drag-drop and work item management issues identified: hover highlighting, persistence, deta
    Requirements: F; i; x;  ; h

  PROMPTS P102276 [ ] [bug] [completed] [4] — Fixed work item link persistence bug in tag view by removing category filter.
    Requirements: F; i; x;  ; w
    Deliveries: R; o; o; t;  

  PROMPTS P102302 [ ] [bug] [completed] [4] — Completed missing delete handler for work_item rows in bottom panel.
    Requirements: W; i; r; e;  
    Deliveries: D; e; f; i; n

  PROMPTS P102311 [ ] [bug] [completed] [5] — Debugged work_item ordering by fixing seq_num NULL handling and ensuring prompts/commits link to wor
    Requirements: E; x; p; l; a
    Deliveries: I; d; e; n; t

  PROMPTS P102322 [ ] [bug] [completed] [4] — Fixed UI behavior for AI tag acceptance and existing tag confirmation in work item planner.
    Requirements: W; h; e; n;  
    Deliveries: M; o; d; i; f

  PROMPTS P102324 [ ] [bug] [completed] [4] — Resolved tag command conflict by creating /stag alias and tagged session with development and work_i
    Requirements: U; s; e; r;  
    Deliveries: I; d; e; n; t

  PROMPTS P102325 [ ] [bug] [completed] [4] — Fixed bug where adding AI tags caused work_items to disappear; metadata tags now stay in list.
    Requirements: W; h; e; n;  
    Deliveries: F; i; x; e; d

  PROMPTS P102341 [ ] [bug] [completed] [4] — Fixed UI bug where planner doesn't display bug/category categories and work items disappear on tag a
    Requirements: F; i; x;  ; p
    Deliveries: F; i; x; e; d

  PROMPTS P102146 [ ] [task] [completed] [4] — Clarified that new tags in chat picker are created at root level; nested tags require Planner.
    Requirements: U; s; e; r;  
    Deliveries: E; x; p; l; a

  PROMPTS P102166 [ ] [task] [completed] [4] — Verified tag logic alignment: session-level tags (Chat), prompt-level tags (History), commit linkage
    Requirements: V; e; r; i; f
    Deliveries: C; o; n; f; i

  PROMPTS P102191 [ ] [task] [in-progress] [3] — Identified hardcoded Pipeline in work_item_pipeline.py; explained merge path with workflow engine.
    Requirements: L; o; c; a; t
    Deliveries: L; o; c; a; t

  PROMPTS P102198 [ ] [task] [in-progress] [3] — Explained Claude Agent SDK capabilities and assessment of fit for multi-agent PM/Dev/Tester/Reviewer
    Requirements: E; x; p; l; a
    Deliveries: E; x; p; l; a

  PROMPTS P102199 [ ] [task] [completed] [4] — Verified parent_id field added to work items for nested tag support.
    Requirements: C; h; e; c; k
    Deliveries: C; o; n; f; i

  PROMPTS P102242 [ ] [task] [in-progress] [1] — System files updated after session (no specific delivery details provided).
    Requirements: C; l; a; r; i
    Deliveries: S; y; s; t; e

  PROMPTS P102243 [ ] [task] [in-progress] [1] — System context and AI rules updated after session.
    Requirements: A; d; d; r; e
    Deliveries: S; y; s; t; e

  PROMPTS P102301 [ ] [task] [completed] [4] — Fixed date format to yy/mm/dd-hh:mm and removed non-work_item tags from display.
    Requirements: C; h; a; n; g
    Deliveries: I; m; p; l; e

  PROMPTS P102316 [ ] [task] [in-progress] [3] — Explained session management, context compression, and provided architectural overview of tag tracki
    Requirements: A; d; d;  ; m
    Deliveries: E; x; p; l; a

  PROMPTS P102323 [ ] [task] [completed] [4] — Clarified that /tag command works in current session without needing new session.
    Requirements: U; s; e; r;  
    Deliveries: E; x; p; l; a

  PROMPTS P102330 [ ] [task] [completed] [4] — Changed session tags from work_items to planner feature tag.
    Requirements: C; h; a; n; g
    Deliveries: S; e; s; s; i

  PROMPTS P102331 [ ] [task] [completed] [4] — Analyzed planner_tag table schema and proposed cleanup of redundant/unused columns.
    Requirements: A; n; a; l; y
    Deliveries: R; e; c; o; m

  PROMPTS P102333 [ ] [task] [completed] [3] — Planned removal of AI-generated columns from planner_tags and clarified extra column usage.
    Requirements: P; l; a; n;  
    Deliveries: P; r; o; p; o

  PROMPTS P102336 [ ] [task] [completed] [4] — Session tag 'feature: feature_snapshot' set for development tracking.
    Requirements: A; d; d;  ; t
    Deliveries: S; e; s; s; i

  PROMPTS P102339 [ ] [task] [completed] [4] — Analyzed aicli product architecture and provided recommendations for improving flow visibility and p
    Requirements: I; m; p; r; o
    Deliveries: P; r; o; d; u

  PROMPTS P102347 [ ] [task] [completed] [4] — Cleaned up event tags to show only user-managed tags, removed system metadata from 1441 events and b
    Requirements: R; e; m; o; v
    Deliveries: P; a; s; s;  

  PROMPTS P102354 [ ] [task] [completed] [4] — Moved session ID display to tag bar and fixed chat loading to sync latest chats from local JSON file
    Requirements: S; h; o; w;  
    Deliveries: M; o; v; e; d

  PROMPTS P102305 [ ] [bug|feature] [completed] [5] — Fixed work_item detail loading, improved tag suggestion layout, increased fonts, styled × button, an
    Requirements: F; i; x;  ; w
    Deliveries: F; i; x; e; d

---

## **mcp-integration-setup** · 26/03/10-03:14 [ ] (claude)
> Type: new
> Total: 24 prompts
> User tags:
> AI existing:
> AI new: [task:mcp-setup]
> Requirements: Agent Roles implementation in graph_workflow.js with role selection and config auto-population; Implement pipeline triggered from planner tab; Project manager agent merges tag info with ai table (mem_ai_tags) and MRR tables (mem_mrr_tags); Create new feature to merge tags in UI via drag-and-drop; Extend planner tab with drag-and-drop functionality

  PROMPTS P102193 [ ] [feature] [completed] [4] — Completed Agent Roles implementation with auto-population and UI updates
    Requirements: A; g; e; n; t
    Deliveries: _; g; w; O; n

  PROMPTS P102231 [ ] [feature] [completed] [3] — Implement tag pipeline from planner merging AI and MRR data sources
    Requirements: I; m; p; l; e
    Deliveries: B; a; c; k; e

  PROMPTS P102235 [ ] [feature] [in-progress] [1] — Design drag-and-drop merge feature for planner tab with parent-child support
    Requirements: C; r; e; a; t

  PROMPTS P102188 [ ] [bug] [completed] [4] — Fixed database array parsing bug and confirmed end-to-end memory pipeline working.
    Requirements: V; e; r; i; f
    Deliveries: F; i; x; e; d

  PROMPTS P102317 [ ] [bug] [completed] [4] — Resolved /tag skill unknown error and explained session restart requirement.
    Requirements: F; i; x;  ; u
    Deliveries: E; x; p; l; a

  PROMPTS P102177 [ ] [bug] [completed] [4] — Fixed session ordering to use creation date instead of update timestamp
    Requirements: S; e; s; s; i
    Deliveries: B; a; c; k; e

  PROMPTS P102269 [ ] [bug] [completed] [4] — Fixed JSONB type casting error in route_history upsert query
    Requirements: F; i; x;  ; P
    Deliveries: F; i; x; e; d

  PROMPTS P102270 [ ] [bug] [completed] [4] — Fixed ON CONFLICT DO UPDATE duplicate constraint error in sync_commits route
    Requirements: F; i; x;  ; O
    Deliveries: I; d; e; n; t

  PROMPTS P102273 [ ] [bug] [completed] [4] — Fixed ReferenceError: _plannerSelectAiSubtype and window._plannerSync undefined errors
    Requirements: F; i; x;  ; U
    Deliveries: R; e; m; o; v

  PROMPTS P102279 [ ] [bug] [completed] [3] — Diagnosed slow data loading in route_work_items due to 60+ second migration on Railway
    Requirements: F; i; x;  ; e
    Deliveries: I; d; e; n; t

  PROMPTS P102154 [ ] [task] [completed] [4] — Clarified MCP server architecture and why Claude doesn't use it directly in web sessions.
    Requirements: E; x; p; l; a
    Deliveries: E; x; p; l; a

  PROMPTS P102156 [ ] [task] [completed] [4] — Confirmed session-commit connection already exists in hooks; UI display was the missing piece.
    Requirements: U; n; d; e; r
    Deliveries: C; o; n; f; i

  PROMPTS P102189 [ ] [task] [completed] [4] — Configured .mcp.json for project root and clarified MCP will activate in next Claude Code session.
    Requirements: D; e; t; e; r
    Deliveries: C; o; n; f; i

  PROMPTS P102209 [ ] [task] [in-progress] [0] — Request to refactor database schema removing client-specific tables — response empty.
    Requirements: R; e; m; o; v

  PROMPTS P102237 [ ] [task] [in-progress] [0] — Identified workspace folder under backend; status of usage not stated.
    Requirements: D; e; t; e; r

  PROMPTS P102238 [ ] [task] [completed] [4] — Deleted workspace folder per user request.
    Requirements: D; e; l; e; t
    Deliveries: R; e; m; o; v

  PROMPTS P102227 [ ] [task] [in-progress] [0] — Test prompt after migration (no changes recorded)
    Requirements: T; e; s; t;  

  PROMPTS P102229 [ ] [task] [in-progress] [0] — Test after mem_ai cleanup (no changes recorded)
    Requirements: V; e; r; i; f

  PROMPTS P102234 [ ] [task] [completed] [2] — Fixed workspace state and memory after session update
    Requirements: F; i; x;  ; i
    Deliveries: W; o; r; k; s

  PROMPTS P102263 [ ] [task] [in-progress] [0] — Test prompt after fix (no changes recorded)
    Requirements: V; e; r; i; f

  PROMPTS P102266 [ ] [task] [in-progress] [0] — Final verification prompt (no changes recorded)
    Requirements: F; i; n; a; l

  PROMPTS P102288 [ ] [task] [completed] [5] — Refactored memory module naming convention and updated all 11 callers consistently
    Requirements: E; n; s; u; r
    Deliveries: D; e; l; e; t

  PROMPTS P102290 [ ] [task] [completed] [4] — Explained commit-to-work-item linkage chain and how to track metrics per work item
    Requirements: E; x; p; l; a
    Deliveries: D; o; c; u; m

  PROMPTS P102329 [ ] [task] [in-progress] [0] — Column naming refactor and work_item enhancement incomplete - awaiting implementation
    Requirements: R; e; n; a; m

---

## **general-commits** · 26/04/12-00:03 [x] (auto)
> Type: existing
> Total: 7 commits
> User tags:
> AI existing:
> AI new:

  COMMITS C200666 [x] [feature] [completed] [5] — Add memory embedding and event extraction to memory promotion flow
    Deliveries: b; a; c; k; e

  COMMITS C200667 [x] [feature] [completed] [5] — Introduce deliveries feature with DB migration and tag/delivery CRUD endpoints
    Deliveries: b; a; c; k; e

  COMMITS C200668 [x] [feature] [completed] [5] — Add feature snapshot memory module with LLM-based snapshot generation
    Deliveries: b; a; c; k; e

  COMMITS C200669 [x] [feature] [completed] [5] — Add pipeline run logging and workflow/pipeline status tracking endpoints
    Deliveries: b; a; c; k; e

  COMMITS C200670 [x] [feature] [completed] [5] — Add PostgreSQL database maintenance and cleanup utilities
    Deliveries: b; a; c; k; e

  COMMITS C200665 [x] [task] [completed] [5] — Refactor memory promotion and work item column naming across DB/memory/router modules
    Deliveries: b; a; c; k; e

  COMMITS C200671 [x] [task] [completed] [5] — Add database index on prompts source_id column for query optimization
    Deliveries: b; a; c; k; e
