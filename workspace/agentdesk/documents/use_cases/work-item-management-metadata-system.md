# US1002 — Work Item Management & Metadata System

created: 2026-04-23 | updated: 2026-04-24 | 8 bugs · 7 features · 8 tasks · 2 requirements

## Summary

Build comprehensive work item lifecycle management with AI-generated metadata, tag integration, and feature snapshot aggregation. Enable storing work item descriptions, acceptance criteria, action items, and deliverables with proper database schema, tag mirroring from source events, and AI promotion workflows to keep work item data synchronized with project progress.

## Requirements

#### AI1070 — Tag mirroring from source events to work items

Work items should automatically inherit and expose all tags from their mirror event sources (phase, feature, source, component, doc_type, bug). User-created tags from linked events must be merged and visible in work_item.tags JSONB column for filtering and metadata purposes.


---

## Open Items (4)

### Bugs (1)

#### AI1075 — Work Item Dashboard & Pipeline Visibility

Design and plan new dashboard tab for work item visibility. Enable pipeline execution from multiple sources (Planner, docs where feature exists, direct chat). Improve visibility of all flows and work item pipelines to give users better control over work item creation and management.

---

## Completed (20)

### Bugs (7)

#### AI1069 — AI tags causing work items to disappear from list

When users accept AI-suggested tags (doc_type, phase, feature), work items incorrectly disappear from the unlinked work items list instead of staying visible with metadata updated. Expected behavior: only disappear when linking to EXISTING tag; NEW tags should be created and item remains visible.

#### AI1078 — Electron Empty Load on Duplicate Variable

Electron loading empty due to duplicate const cats declaration in same function scope. Previous fix for _wiPanelCreateTag introduced naming conflict.

#### AI1080 — Missing Latest Prompts in Chat UI

Chat view not displaying latest prompts from Claude CLI. New prompts not appearing automatically. Auto-update mechanism broken—chat used to refresh on new prompts but no longer does.

#### AI1085 — Chat session ID display position and duplication

Session ID was being displayed multiple times (in message headers and tag bar) and phase chip was redundant. User requested single session ID display in tag bar only (last 5 chars in sidebar, full UUID in bar), with phase shown only once at the top (already mandatory per session).

#### AI1086 — Chat loading shows stale session on startup

When Chat tab loads, it was displaying an old session ID (7d89c79f-b6f1-4bd4-a93f-09f2603fd1b1) instead of current session (f6648726-1e7f-48bf-b604-4c74bf7c8154). After 15 seconds, the UI would auto-update to the correct session. Root cause: _sessionId module-level var persisted across tab navigations, and localStorage cache rendered with old session highlighted.

#### AI1091 — Work Items tab not displaying all items after approval

Work Items tab was not showing all work items in the UI. Issue: _renderList() only displayed pending AI* use cases, and once a UC was approved, it disappeared from Work Items tab. TA4001 and REJBB4111 were unlinked (wi_parent_id: null) and showed as orphaned items in warning zone.

#### AI1092 — Hook health reporting offline due to missing unique index

Hook status displayed 'offline (last prompt 8.3H)' indicating hook health issue. Root cause: migration m073 was required to create missing unique index that ON CONFLICT clause requires in hook-log endpoint upsert query. Without index, hook inserts were failing.


### Features (6)


### Features (6)

#### AI1073 — Deliveries tracking column for planner tags

Add deliveries JSONB column to planner_tags (after action_items) allowing users to specify what outputs were produced: code (python/js/c#...), documents (md/doc), architecture designs (visio), presentations. Support category and type combinations from static mng_deliveries lookup table.

#### AI1074 — Feature snapshot aggregation layer (mem_ai_feature_snapshot)

Create final aggregation layer merging user requirements/tags with actual work items and planner tags. Consolidate feature summary, map use cases with their types (bug/feature/task) and delivery types (code stack, design docs, AWS architecture). Serves as single source of truth for feature progress and input to developer/tester/reviewer workflows.

#### AI1081 — Session ID Display in Chat Header & Body

Display session ID prominently in chat UI: last 5 characters in left panel header (format: …xxxxx) and full session ID with copy button in top-right body banner. Format: 'CLI · development · (ab3f9) · 3 prompts · 26/04/15-19:31'.

#### AI1084 — Chat session visibility and tagging UI

Enhance Chat tab UI to display each session on the left sidebar with source badge, phase chip, and last 5 digits of session ID. When user opens a session, show full session ID in a tag bar with phase and all existing tags. Add '+Tag' button to each CLI prompt message allowing users to add tags from the planner_tag picker. Tag selection persists to mem_mrr_prompts.

#### AI1087 — Instant chat load with background refresh

Chat sessions should load instantly from cache on startup, then fetch fresh data in background. Previously, users saw partial history until network request completed. Implement localStorage caching of session metadata (not full entries to keep size small) with immediate render before any network request.

#### AI1093 — Reorganize Work Items UI - tabs moved to right

Work Items and Use Cases tabs should be on the right side of toolbar (instead of top), grouped as bordered pill (Work Items | Use Cases). This separates concerns: Work Items tab shows pending AI-suggested items awaiting approval; Use Cases tab shows all approved use cases with their linked children.


### Tasks (7)


### Tasks (7)

#### AI1071 — Consolidate work item AI-generated columns (desc_ai, criteria_ai, items_ai)

Rename ai_* columns for consistency (ai_name→name_ai, ai_category→category_ai, ai_desc→desc_ai) and remove redundant summary column by merging into ai_desc. Ensure promote_work_item() runs during /memory updates to keep all AI metadata current with recent commits and progress.

#### AI1072 — Planner tags schema cleanup and optimization

Remove unused/unpopulated planner_tags columns (seq_num, code_summary, summary, design, embedding, extra). Consolidate source+creator into single creator field (null for user, 'ai_extracted' for system). Add updater column tracking last modifier. Reorder columns: project_id after client_id, timestamps at end.

#### AI1077 — Events Table Schema Optimization

Restructure mem_ai_events table column order: move project_id after client_id, relocate created_at/processed_at/embedding to end. Review and remove action_item column if unused. Clarify source_id population logic for multi-event items (prompts with 5 events vs single-event items). Drop importance column from events table.

#### AI1082 — Prompt Timestamp Display in Chat

Add timestamp display next to YOU label in each prompt entry. Format: 'YOU — YY/MM/DD-HH:MM' (em dash for readability). Enable users to see exact timing of each prompt within a session.

#### AI1088 — Chat history completeness - JSONL merge with DB

Chat was loading only prompts from a certain point, not showing full history. System stores prompts in both _system/session JSON files and database. Need to merge both sources and ensure DB is primary source, with JSONL as fallback. Sort correctly by timestamp with LIMIT=500 to show complete history from oldest to newest.

#### AI1089 — Database schema refactor - user_id int conversion

User IDs in database should be INT (like project_id and client_id) not VARCHAR strings. Add updated_at column to all mirror tables to track row modifications. Add user_id INT to all mirror tables after project_id. Migration to convert mng_users.id from UUID to SERIAL INT, preserve old UUID in uuid_id column.

#### AI1090 — Database table column ordering and restructuring

Standardize column ordering across all database tables: id → client_id → project_id → user_id, then domain columns, then created_at → updated_at → embedding (always at end). Remove redundant committed_at from mem_mrr_commits. Reorder quality columns in mem_ai_work_items. Rebuild 18 tables to enforce consistent structure. Convert planner_tags.user_id from VARCHAR(36) to INT.


### Requirements (1)


---

## Open Items (3)

### Bugs (1)

#### AI1076 — Work Item UI Category Display Bug

Planner UI not displaying bug/category labels properly—only shows 'work_item' category. When AI tag is accepted, work item disappears but top screen remains empty. UI not rendering category distinctions correctly.


### Features (1)


### Features (1)

#### AI1079 — Per-Prompt Tag Addition & Management

Add UI option to tag individual user prompts in chat view. Show all existing user tags for each prompt (same functionality as History/Prompts). Tags should persist to mem_mrr_prompts table with phase, feature, bug, source categories. Enable inline tag editing and display in prompt entries.


### Tasks (1)


### Tasks (1)

#### AI1083 — Verify Hook-Log DB Storage After Migration

Verify that hook-log endpoint correctly stores all prompts to database after migration m050. Ensure no silent DB errors and validate prompt persistence.


### Requirements (1)
