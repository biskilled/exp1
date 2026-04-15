# Project Memory — aicli
_Generated: 2026-04-15 08:11 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Facts

- **ai_context_file_locations**: .ai/rules.md, .cursor/rules/aicli.mdrules, .github/copilot-instructions.md as primary agent context files; legacy _system/ directory deprecated
- **ai_event_filtering_logic**: event_type IN ('prompt_batch', 'session_summary') filters mem_ai_events; excludes per-commit and diff_file noise from event_count aggregation
- **ai_event_tags_schema**: mem_ai_events.tags JSONB object; preserved keys: phase, feature, bug, source; system metadata (llm, event, chunk_type, commit_hash, commit_msg, file, files, languages, symbols, rows_changed, changed_files) stripped during backfill
- **ai_rules_generation_mechanism**: aicli tool manages rule files; `/memory` command refreshes; auto-generated with UTC timestamp
- **ai_tag_color_default**: #4a90e2 replaces var(--accent), applied when wi.ai_tag_color not set
- **ai_tag_label_format**: category:name when both present, falls back to name-only, empty string if neither
- **ai_tag_suggestion_debugging_status**: investigating missing suggested_new tags in ui_tags query and verifying ai_suggestion column population in work item panel refresh workflow
- **ai_tag_suggestion_feature**: ai_tag_suggestion column with approve/remove button handlers (_wiPanelApproveTag/_wiPanelRemoveTag), refactored to simplified chip markup without category prefix display in non-category mode
- **ai_tag_suggestion_ux**: clickable ✓ button creates missing ai_suggestion tags with category inference; tooltip improved from 'No existing tag' to 'Does not exist yet'
- **approval_workflow_pattern**: single source of truth for pipeline execution; routes multi-source triggers through unified approval before execution
- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **code_extraction_configuration**: min_lines: 5 (per-symbol threshold), min_diff_lines: 5 (commit-level threshold), only_on_commits_with_tags: false
- **column_naming_convention**: prefix_noun_adjective order: commit_hash_short (not commit_short_hash); standardized across schema
- **commit_processing_flag**: exec_llm boolean column replaces tags->>'llm' NULL check
- **commit_tracking_exec_llm_deprecation**: exec_llm boolean column replaced by event_id IS NULL sentinel (event_id set by process_commit() on completion)
- **commit_tracking_schema**: mem_mrr_commits_code table with 19 columns including commit_short_hash and full_symbol as generated column
- **creator_field_convention**: planner_tags.creator: username string for users, 'ai' literal for system-generated tags
- **dashboard_module_architecture**: independent tab for real-time workflow visibility; separate from planner interface to prevent navigation friction
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **date_format_frontend**: YY/MM/DD-HH:MM format in work item panel
- **db_engine**: PostgreSQL with SQL parameter binding
- **db_migration_m027**: planner_tags_drop_ai_cols removes summary/design/embedding/extra via ALTER TABLE DROP IF EXISTS pattern
- **db_migration_m029**: mem_ai_feature_snapshot table: per-tag per-use-case feature snapshots with version='ai' (overwritten on each run) and version='user' (promoted, never overwritten); unique constraint on (project_id, tag_id, use_case_num, version); 3 indexes on project_id, tag_id, tag_id+version
- **db_migration_m031**: m031_commits_cleanup: drops tags_ai and exec_llm from mem_mrr_commits; renames commit_short_hash to commit_hash_short; uses DROP COLUMN IF EXISTS pattern
- **db_migration_m037**: dropped importance column from mem_ai_events table; deprecated as semantically relevant only for work_items
- **db_migration_sequence**: m031_commits_cleanup follows m030_pipeline_runs in MIGRATIONS list
- **db_schema_management**: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_electron_builder_scope**: Electron-builder for desktop; Mac dmg, Windows nsis, Linux AppImage+deb removed from explicit enumeration
- **deployment_target**: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
- **event_count_column_semantics**: counts prompt_batch + session_summary events only; now displayed after commit_count (moved from position 2 to position 4)
- **event_tag_backfill_endpoint**: POST /admin/backfill-event-tags with project and dry_run params; returns per-pass counts; requires admin auth
- **event_tag_backfill_process**: three-pass idempotent operation: Pass 1 strip system metadata, Pass 2 backfill commit events from mem_mrr_commits via source_id or event_id, Pass 3 backfill prompt_batch events from mem_mrr_prompts via event_id
- **event_tags_corrupt_recovery**: Pass 0 detects and resets non-object JSONB tags (arrays/scalars) to {} before backfill
- **feature.auth.design**: {'high_level': "4-phase architecture: (1) Database & Core Token Infrastructure — mng_verification_tokens table with single-use token storage and expiry tracking; mng_resend_cooldown table for rate-limiting; users.verified_at column for lifecycle tracking. (2) Backend Token & Email Logic — TokenService generates cryptographically secure tokens (crypto.randomBytes(32).toString('hex')), EmailService sends verification emails via AWS SES (or configured provider), background job queues async delivery with retry/backoff. (3) Authentication Flow Integration — Existing POST /auth/register endpoint calls token generation and email sending after user creation; new POST /auth/verify-email validates token, marks user as verified, invalidates token; new POST /auth/resend-verification enforces 60s cooldown. (4) Frontend & Access Control — EmailVerificationBanner shows on Sign In screen for unverified users with resend button and cooldown timer; VerifyEmailPage handles token extraction and verification; requireVerified middleware checks verified_at before granting access to protected routes; AwaitingVerificationScreen blocks unverified access with clear instructions.", 'low_level': "Token generation: crypto.randomBytes(32).toString('hex') stored in mng_verification_tokens with uuid, user_id, expires_at=NOW()+24h, redeemed_at=NULL. Token verification: lookup by token string, check expires_at > NOW() (return 410 if expired), check redeemed_at IS NULL (return 409 if used), set users.verified_at = NOW(), set mng_verification_tokens.redeemed_at = NOW(). Resend endpoint: check user already verified (return 400), check cooldown via mng_resend_cooldown.last_resend_at > NOW()-60s (return 429 with remaining_seconds), invalidate unused tokens, generate new token, send email, update cooldown. Email template: plain-text + HTML with verification link {baseUrl}/verify-email?token={token}, subject 'Confirm Your Email Address'. Background job: Bull/Celery/SQS integration, retry up to 3 times with exponential backoff, fire-and-forget (non-blocking HTTP response). Route guards: requireVerified middleware checks user.verified_at IS NOT NULL before resource access, redirects to AwaitingVerificationScreen if null.", 'patterns_used': ['cryptographically_secure_token_generation', 'single_use_token_with_expiry', 'rate_limiting_via_cooldown_table', 'background_job_async_email_delivery', 'soft_deletion_via_redeemed_at_timestamp', 'middleware_based_access_control', 'non_blocking_user_flow_with_verification_prompt']}
- **feature.billing.design**: {'high_level': '4-layer billing architecture: (1) Payment Provider Integration Layer (Stripe/PayPal adapters with webhook handlers), (2) Subscription & Quota Management (manage active plans, enforce limits per client), (3) Usage Tracking & Metering (capture events via middleware, aggregate to billing_events table), (4) Revenue & Reporting (invoices, receipts, admin analytics dashboards). All tables follow mng_/cl_/pr_ naming convention. Integration with existing mng_clients and auth system.', 'low_level': 'Database tables: mng_billing_plans (id, name, tier, price_usd, features_json), mng_subscriptions (id, client_id, plan_id, status, current_period_start/end, stripe_subscription_id), mng_invoices (id, client_id, period_start/end, total_usd, status, stripe_invoice_id), mng_billing_events (id, client_id, event_type, resource_count, cost_usd, created_at—for usage tracking). Backend: PaymentService (create_subscription, process_webhook), UsageTracker (record_event, get_usage_summary), QuotaValidator (check_limits). Frontend: BillingDashboard component showing subscription, invoices, usage charts.', 'patterns_used': ['Adapter pattern for payment providers (StripeAdapter, PayPalAdapter)', 'Middleware pattern for usage tracking (attach to API routes)', 'Event sourcing for billing events (immutable log of charges)', 'Webhook handler pattern for async payment confirmations', 'Tiered pricing with feature flags per subscription tier', 'Soft quota (warn users) → hard quota (block access) progression']}
- **feature.embeddings.design**: {'high_level': '4-layer memory architecture with embeddings as the enrichment step: (1) ephemeral session layer captures raw user interactions (prompts, messages, commits), (2) mem_mrr_* mirror tables normalize and deduplicate raw events with session_id FK, (3) mem_ai_events layer runs LLM Haiku synthesis on batches of prompts/commits/summaries to generate semantic digests + 1536-dim embeddings, (4) mem_ai_work_items/project_facts layer promotes high-confidence events into actionable work items and durable facts. Embeddings enable semantic search, context ranking, and feature snapshot synthesis. Incremental batch processing via background tasks (Bull/SQS) to avoid token exhaustion. All vectors stored in pgvector for fast cosine similarity queries.', 'low_level': "MemoryEmbedding class orchestrates embedding pipeline: (a) process_prompt_batch(project, session_id, count) queries mem_mrr_prompts with event_id IS NULL, chunks prompts by session, calls LLM (Haiku via configured provider) to generate digest + embedding, stores result in mem_ai_events with event_type='prompt_batch', back-propagates event_id to mem_mrr_prompts. (b) process_commit_batch(project, min_commits) groups unembedded commits by repo, chunks diffs per-file, synthesizes summary + embedding, stores in mem_ai_events with event_type='commit', back-propagates to mem_mrr_commits. (c) process_session_summary(project, session_id) synthesizes all tagged events in session into single mem_ai_events row with event_type='session_summary' and embedding. Column ordering: client_id → project_id → created_at/processed_at/event_type/llm_source → embedding (last). Vectors indexed via IVFFLAT (vector_cosine_ops) for O(1) approximate nearest-neighbor search. Incremental flag checks embedding IS NULL before processing. Retry logic with exponential backoff (1s, 2s, 4s) on transient LLM errors.", 'patterns_used': ['Incremental batch processing — skip already-embedded events via WHERE embedding IS NULL', 'Background async tasks — /memory/{project}/embed-prompts and /memory/{project}/embed-commits queued to Bull/SQS', 'Smart chunking — per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs) to manage token budget', 'Event-driven mirroring — mem_mrr_* tables updated on session, mem_ai_events updated on synthesis, mem_ai_work_items on promotion', 'Dual-storage (JSONL + PostgreSQL) — JSONL for durability, pgvector for semantic search', 'Semantic ranking — cosine similarity on embeddings to score work_item relevance for feature snapshots', 'Fallback providers — support Anthropic, OpenAI, DeepSeek with adapter pattern (client selection at runtime)', 'Transactional back-propagation — set event_id on mirror tables in same transaction as mem_ai_events INSERT']}
- **feature.entity-routing.design**: {'high_level': 'Multi-layer entity routing system: (1) Type detection layer reads entity_kind from request (user/project/client/workspace/work_item) and session context; (2) Authorization layer checks role-based access (admin/manager/owner/viewer); (3) Processor registry maps entity types to handler functions; (4) Handler delegates to specialized route files (route_users.py, route_projects.py, etc.); (5) Unified response envelope ensures consistent contract across entity types. Integrates with MCP tools for programmatic entity management and work_item_pipeline for cross-entity linking.', 'low_level': 'Middleware chain: detect_entity_type() → authorize_entity_access() → dispatch_to_processor(). Type detection checks request path, JSON body, query params, or session state to infer entity_kind. Authorization uses mng_agent_roles + role enforcement via RoleCreate/RoleUpdate models. Processor registry (dict mapping entity_kind to handler) delegates to appropriate route module. Response envelope includes { entity_kind, entity_id, data, relations, work_items_linked }. Error handling returns 403 for access denied, 404 for not found, 422 for validation failure.', 'patterns_used': ['Chain of Responsibility (middleware stack for type detection → auth → dispatch)', 'Registry Pattern (entity_kind → processor function mapping)', 'Strategy Pattern (entity-specific handlers as interchangeable strategies)', 'Factory Pattern (processor creation based on entity type)', 'Decorator Pattern (role-based authorization wrapping handler functions)']}
- **feature.graph-workflow.design**: {'high_level': 'graph-workflow is a 3-layer system: (1) DAG data model (workflows, nodes, edges) stored in PostgreSQL with project_id scoping; (2) async execution engine (asyncio.gather, loop-back support, max_iterations cap) with per-node retry + continue_on_fail semantics; (3) UI layer (Cytoscape visualization + 2-pane approval panel) connected to work_item_pipeline 4-stage approval flow. Auto-commit layer parses LLM output for code blocks and applies git operations. Role system (mng_agent_roles) centralized in DB with fallback prompts. All outputs versioned in documents/ tree with old/ subfolder for history.', 'low_level': 'Execution model: _make_node_fn() returns async node function that calls LLM provider (Claude/OpenAI), handles retries (up to max_retry), applies continue_on_fail logic, calls save_approved_output() on approval, and (if auto_commit=true) calls _parse_code_changes() + _apply_code_and_commit() to write code and commit. Database: 4 tables (pr_graph_runs, pr_graph_nodes, pr_graph_edges, pr_graph_workflows) + mng_agent_roles global table. API routes: /graph-workflows/ (CRUD workflows), /graph-workflows/{id}/runs/ (CRUD runs), /graph-workflows/{id}/runs/{run_id}/execute (POST to start), /graph-workflows/{id}/runs/{run_id}/approve/{node} (approve node output). Frontend: Cytoscape instance renders DAG with drag-to-connect nodes; click node opens approval panel; status colors (pending/running/approved/failed) update in real-time. Work item integration: trigger_work_item_pipeline() creates pr_graph_run record, executes 4-stage DAG (PM→Architect→Dev→Reviewer), returns final work_item with populated acceptance_criteria/implementation_plan/output.', 'patterns_used': ['AsyncDAG: asyncio.gather with loop-back detection (set(prev_ran) tracking), max_iterations cap, fail-fast on critical errors', 'Provider abstraction: client factory pattern for Claude/OpenAI/DeepSeek/Gemini; node config specifies provider/model override', 'Database multi-tenancy: project_id foreign keys across all tables; mng_agent_roles global for role templates', 'Dual-layer versioning: current output in documents/{category}/{slug}/{node}.md; timestamped backups in old/; on re-run, move current to old before overwriting', "Auto-commit safety: path traversal prevention (resolve() + startswith check); background push (Popen, don't block HTTP); error logging only, no failure propagation", 'Approval workflow: save_approved_output() on user click; status tracked in pr_graph_runs; missing auto_commit implementation in developer node']}
- **feature.hooks.design**: {'high_level': 'Hooks architecture follows a fire-and-forget event-driven pattern integrated into existing aicli routers. Core HookManager class queries mng_hooks table for enabled hooks matching an event_type, evaluates optional condition filters (JSONPath or simple tag matching), and executes action sequences asynchronously via background job queue (Bull/Celery). Actions are modular (embed, promote_work_item, regenerate_memory, run_pipeline, webhook_post) and composable—a single hook can run multiple actions in sequence with error handling (continue_on_error flag). Time-based hooks (cron or at-specific times) use APScheduler integrated into backend startup. Hook state tracked in mng_hook_runs table (hook_id, project_id, triggered_at, status, result_summary) for audit trail and debugging.', 'low_level': "Database schema: mng_hooks (id UUID PK, client_id INT FK, project_id INT FK, name TEXT, event_type TEXT IN ('prompt_batch','commit','session_start','session_end','work_item_patch','memory_regen'), condition_filter JSONB, actions JSONB[], enabled BOOLEAN, created_at TIMESTAMP, updated_at TIMESTAMP); mng_hook_runs (id UUID PK, hook_id UUID FK, project_id INT FK, triggered_at TIMESTAMP, status TEXT, result_summary TEXT, duration_ms INT). HookManager methods: fire(event_type: str, payload: dict) → async executes matching hooks; create(client_id, project_id, hook_def: dict) → validates actions and inserts; list(project_id) → queries mng_hooks with eager load of action details; test_dry_run(hook_id, sample_payload) → executes actions without side effects. Action executor: each action type (embed, promote, webhook) implemented as async coroutine with timeout (30s default), retry logic (exponential backoff up to 3x), and error logging to mng_hook_runs.result_summary. Trigger points: route_history.sync_commits() calls fire('commit', {commit_hash, files_changed, author}); route_memory.embed_prompts() calls fire('prompt_batch', {session_id, prompt_count}); route_sessions.end_session() calls fire('session_end', {session_id, duration_s, summary}).", 'patterns_used': ['event-driven architecture (fire-and-forget with async execution)', 'observer/publisher-subscriber (hooks subscribe to event_type)', 'command pattern (actions as composable, serializable objects)', 'factory pattern (action executor dispatches on action.type)', 'job queue pattern (background job for hook execution with retry)', 'audit trail (mng_hook_runs table tracks all executions)']}
- **feature.memory.design**: {'high_level': "4-layer memory pyramid: Session (ephemeral state) → Mirrors (mem_mrr_prompts/commits/tags for raw capture) → Events (mem_ai_events with LLM digests + embeddings + tagging) → Work Items/Facts (mem_ai_work_items, mem_ai_project_facts for semantic distillation). Each layer progressively refines raw data: mirrors capture everything, events apply LLM synthesis and semantic embedding, work items extract actionable tasks linked to code/docs. Tagging system unified: event_tags_{project} JSONB column holds phase/feature/bug/source only; system metadata stripped. Multi-client/project architecture: all tables use (client_id, project_id) composite keys; mng_projects FK centralizes project config. Backfill support: commits without active sessions create work items via AI extraction (event_type='commit'); prompts from live sessions create work items via human tagging + AI matching (event_type='prompt_batch'); session summaries provide context digest (event_type='session_summary'). /memory endpoint orchestrates regeneration: loads raw events → filters by type (prompt_batch, session_summary) → synthesizes via Haiku → updates work items/facts → regenerates context files.", 'low_level': "mem_ai_events table structure (final): id | client_id | project_id | created_at | processed_at | event_type (prompt_batch|commit|session_summary) | llm_source (anthropic|openai|etc) | content (full text) | tags (JSONB: {phase, feature, bug, source}) | session_id (FK mem_sessions) | work_item_id (FK mem_ai_work_items, nullable) | source_id (UUID back-ref to mrr table) | embedding (VECTOR 1536, nullable). Indexes: (project_id, event_type), (project_id, created_at), (work_item_id), (session_id). mem_mrr_prompts columns after reorder: client_id | project_id | session_id | prompt_number | prompt_text | response_text | model_used | event_id (back-propagated FK) | created_at. mem_ai_work_items columns: id | client_id | project_id | seq_num | category_ai (feature|bug|task) | name_ai | summary_ai | acceptance_criteria_ai | action_items_ai | score_ai (0–5) | tags (user JSONB) | tags_ai (AI-generated metadata) | tag_id_ai (FK planner_tags, suggested) | tag_id_user (FK planner_tags, confirmed) | status_user (active|in_progress|paused|done) | merged_into (self-FK for dedup). Event filtering: only 'prompt_batch' and 'session_summary' events trigger work item extraction (commits skipped unless explicitly tagged); system metadata (llm, chunk_type, commit_hash) removed from tags. Tag system: event-level tagging via MRR union, work_item-level tagging via user confirm + AI suggest flow. Back-propagation: event_id written to mem_mrr_* after event creation for audit trail.", 'patterns_used': ['Mirror Layer Pattern — raw capture tables (mem_mrr_*) separate from processed tables (mem_ai_*) for append-only history', 'Event Sourcing — all state changes recorded as immutable event rows; work items derived from event stream via projection', 'Composite Foreign Keys — multi-client isolation via (client_id, project_id) pairs; single mng_projects table', 'Dual-Status Design — status_user (user-managed lifecycle) vs status_ai (AI suggestions) keep human and system views separate', 'Incremental Aggregation — /memory endpoint processes only unprocessed rows (processed_at IS NULL) for efficiency', 'Tagging by Convergence — prompts+commits+sessions generate work items only if tagged (human or AI with confidence > 0.70)', 'Backpropagation Links — source_id on mem_ai_events links back to originating mirror row; event_id on mem_mrr_* links forward', 'JSONB Metadata — flexible tags and metadata stored as JSON to avoid schema sprawl and support dynamic attributes', 'Lazy Embedding — embeddings computed only for high-relevance events; NULL for noise or archive entries']}
- **feature.shared-memory.design**: {'high_level': '5-layer memory architecture: (L1) Mirror Tables (mem_mrr_prompts, mem_mrr_commits) capture raw user/system activity with source tracking; (L2) Event Ingestion (mem_ai_events) synthesizes L1 data via LLM (Claude Haiku), stores embeddings, classifies via event_type (prompt_batch, commit, session_summary); (L3) Work Item Extraction (mem_ai_work_items) promotes events to actionable items (feature/bug/task) with AI names/categories/acceptance criteria + user tagging; (L4) Project Facts (mem_ai_project_facts) extracts durable insights (architecture decisions, constraints, tech stack); (L5) Context Regeneration auto-generates CLAUDE.md, MEMORY.md, rules.md from L3+L4 via Haiku synthesis. Each layer maintains backward references to source layer via source_id/event_id for audit trail. User tags (phase, feature, bug, source) flow through all layers; system metadata stripped at L2.', 'low_level': "Data flow: (1) Prompt/commit ingested → mem_mrr_* with session_id, source_id, timestamps; (2) Periodic batch: query mem_mrr_* where event_id IS NULL, pass to MemoryEmbedding.process_prompt_batch/process_commit_batch, generates mem_ai_events row with embedding + LLM digest, back-propagates event_id to mem_mrr_*; (3) MemoryPromotion.promote_work_item scans mem_ai_events where tag matches (phase/feature/bug), extracts code/requirements, updates mem_ai_work_items (name_ai, category_ai, acceptance_criteria_ai, action_items_ai, score_ai, summary_ai); (4) MemoryPromotion.promote_project_facts extracts durable patterns (decision, constraint, architecture) into mem_ai_project_facts; (5) MemoryFiles.render_* queries top 50 events by relevance (exponential decay on age), formats as markdown sections, returns combined context. SQL joins: mem_ai_events.work_item_id → mem_ai_work_items; mem_ai_events.tag_id → planner_tags; mem_mrr_*.event_id → mem_ai_events; work_item.tag_id_user → planner_tags (user link). Tag filtering: event_type IN ('prompt_batch', 'session_summary') for work item extraction; commit events skipped unless matched by tag.", 'patterns_used': ['Mirror pattern (L1): Raw tables capture immutable source data; foreign key (event_id) links to synthesized layer.', 'Event sourcing (L2): All changes tracked as timestamped events; embeddings stored for semantic search.', 'Promotion pipeline (L3-L5): Successive LLM passes refine abstractions; each promotes tagged events to higher layer.', 'Bidirectional linking: source_id tracks origin; work_item_id back-references synthesized artifacts.', 'Load-once-on-access: Tags/workflows cached in memory on project load, updated only on explicit save.', 'Async background jobs: Embedding/synthesis runs via Bull/Celery, non-blocking HTTP response.', "Tag-driven filtering: User tags (phase, feature, bug) act as 'topics'; events grouped/promoted by matching tags.", 'Exponential time decay: Relevance score = exp(-0.01 * days_old); recent events prioritized in context.', 'Soft deletes: Tokens/old events marked redeemed_at/archived rather than hard-deleted for audit trail.']}
- **feature_snapshot_schema**: 19 columns: id (UUID PK), client_id (default 1), project_id (FK), tag_id (FK), use_case_num, name, category, status, priority, due_date, summary, use_case_summary, use_case_type, use_case_delivery_category, use_case_delivery_type, related_work_items (JSONB), requirements (JSONB), action_items (JSONB), version (default 'ai'), created_at, updated_at
- **feature_snapshot_versioning**: two-tier: version='ai' auto-overwritten on snapshot runs; version='user' promoted from AI snapshot, never overwritten by subsequent AI runs
- **feature.tagging.design**: {'high_level': '4-tier tag architecture: (1) Ephemeral—user-initiated tag creation via chat picker (root level) or Planner UI (nested); (2) Mirror capture—prompts/commits/entities tagged via mem_mrr_* tables with event_id back-propagation; (3) AI event layer—mem_ai_events stores synthesized event summaries with user-facing tags only; (4) Work item promotion—mem_ai_work_items linked to planner_tags via tag_id_user (user-confirmed) and tag_id_ai (AI-suggested with confidence). Tag suggestions evaluated by AI with confidence > 0.70 threshold, category inference (task/bug/feature first, then others), and UI display with approve/remove/delete controls. Caching strategy: load all project tags into memory on project open via _pickerPopulateCats(), zero DB calls during picker interaction, save only on explicit action.', 'low_level': 'Database schema: mem_ai_tags (id, project_id, name, category, parent_id FK for nesting, created_at, updated_at, creator, updater); mem_ai_tags_relations (id, project_id, from_tag_id FK, to_tag_id FK, relation_type enum, note); planner_tags (id, project_id, name, category, status, creator, requirements JSONB, action_items JSONB, deliveries JSONB, updater); mem_mrr_prompts/commits/entities (project_id, event_id, source_id FK). Backend: MemoryTagging class handles AI suggestions via _vector_search_tags() and confidence scoring; tag_event_by_source_id/untag_event_by_source_id for bidirectional sync; merge_tags() consolidates duplicates via work_items linking. Frontend: tag picker caches tags in JavaScript object, displays with color-coding (green=EXISTS user tag, red=NEW AI suggestion, blue=USER self-created), sticky headers for category navigation, increased font sizes for Electron visibility. UI components: TagChip with approve/delete buttons, CategoryFilter, NestedTagBrowser for multi-level display.', 'patterns_used': ['cache-on-load', 'lazy-evaluation', 'composite-foreign-keys', 'self-referential-nesting', 'back-propagation-linking', 'event-driven-sync', 'confidence-scoring', 'bidirectional-relationship', 'soft-delete-via-status']}
- **feature.UI.design**: {'high_level': 'Electron desktop application with FastAPI backend and Vanilla JS frontend (no frameworks). 4-tier architecture: (1) CLI Engine (aicli/) with Python asyncio, LLM provider adapters, prompt_toolkit; (2) Backend (ui/backend/) with FastAPI routers, PostgreSQL 15+ with pgvector, memory synthesis pipeline; (3) UI (ui/frontend/) with xterm.js terminal, Monaco editor, Cytoscape DAG visualization, responsive HTML/CSS; (4) Workspace (workspace/) with YAML prompts, JSONL history, per-project state. Memory system: ephemeral session → mem_mrr_* raw capture (commits, prompts) → mem_ai_events LLM digests+embeddings → mem_ai_work_items/project_facts/features. Work item pipeline: 4-stage approval (PM requirements → Architect plan → Developer code → Reviewer testing) with loop-back on rejection. Tag system: unified planner_tags table with user/AI dual status (tag_id_user, tag_id_ai), category-based hierarchy (bug/feature/task), and nested parents via parent_id FK.', 'low_level': 'Frontend: renderEntities() module handles tag/work_item display; drag-and-drop via _loadTagLinkedWorkItems() with visual feedback on hover; tag cache in memory on project open (_pickerPopulateCats()). History view singleton pattern to preserve state across tab switches. Work item drawer with collapsible sections (acceptance criteria, action items, linked events, context tags). Backend: route_memory.py /memory endpoint orchestrates 4-layer synthesis (raw JSONL → tagged events → AI digests → work items); route_work_items.py manages CRUD+tagging with event back-propagation; mem_embeddings.py runs async Haiku batch processing with UUID validation. Database: mem_ai_work_items stores AI-generated definitions (name_ai, category_ai, summary_ai) plus user edits (status_user, tag_id_user); mem_ai_events with event_type filter (prompt_batch/session_summary only); mem_mrr_prompts/commits mirror tables with back-propagated event_id; planner_tags unified tag table with JSONB deliveries. Migrations: m037-m046 handle column reordering, deprecation (importance, embedding in commits), and schema cleanup.', 'patterns_used': ['Load-once-on-access caching (tags, workflows, runs cached in memory; DB updated only on explicit save)', 'Provider contract pattern (every LLM provider: send(prompt, system)→str, stream()→Generator)', 'Event-driven memory synthesis (prompts/commits→events→work_items→facts via async jobs)', 'DAG workflow executor (asyncio.gather with loop-back semantics; max_iterations cap; Cytoscape visualization)', 'Dual-status entity tracking (status_ai for system-suggested, status_user for user-confirmed)', 'Back-propagation linking (events linked to prompts/commits via source_id; event_id back-propagated to mirror tables)', 'Smart chunking (per-class/function Python/JS/TS; per-section Markdown; per-file diffs)', 'Composite indexing for performance (project_id+category_ai+name_ai UNIQUE; project_id+seq_num WHERE seq_num IS NOT NULL)', 'Soft-delete with timestamp tracking (merged_into for work items; redeemed_at for tokens; valid_until for facts)', 'UUID validation in queries (coerce string literals to UUID before SQL bind to prevent psycopg2 errors)', 'Batch processing with transactional safety (explicit BEGIN/COMMIT/ROLLBACK for concurrent requests)', 'Fallback configuration (agent roles fallback to _FALLBACK_PROMPTS; code_dir from project.yaml else settings.code_dir)']}
- **frontend_sticky_header_pattern**: CSS position:sticky;top:0;z-index:1 on table headers for work_items panel
- **frontend_ui_pattern**: inline event handlers with event.stopPropagation(), CSS opacity/color hover states via onmouseenter/onmouseleave, escaped string interpolation in onclick via _esc()
- **known_bug_active**: planner_tag_visibility: categories upload but individual tags don't display in UI bindings
- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
- **mcp_tools_count**: 12+ tools including semantic search with work_items vector search, work item management, session tagging
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
- **memory_management_pattern**: load_once_on_access_update_on_save
- **memory_sync_workflow**: /memory endpoint executes embedding pipeline refresh to sync prompts with work_items and detect new tags
- **memory_synthesis_output_format**: 5 files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) with LLM response summarization instead of full output
- **memory_system_update_status**: updated_with_latest_context_and_session_tags
- **mng_deliveries_planned**: lookup table for delivery categories: code, document, architecture, ppt with subtypes; not yet implemented
- **pending_feature**: tags display under work_items in shared memory context
- **pending_implementation**: memory_items_and_project_facts_table_population
- **pending_issues**: project_visibility_bug_active_project_not_displaying
- **performance_issue_active**: route_work_items latency ~60s; investigating _SQL_UNLINKED_WORK_ITEMS indexing and mem_ai_events join optimization
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
- **pipeline_log_error_handling**: graceful degradation: _insert_run/_finish_run return None/silently fail if db.is_available() false, logged at debug level
- **pipeline_logging_api_endpoint**: GET /memory/{project}/pipeline-status dashboard exposes mem_pipeline_runs data
- **pipeline_logging_pattern**: async context manager pipeline_run() and sync tuple-return pipeline_run_sync() wrapping background tasks with mem_pipeline_runs insert/update
- **pipeline_run_context_pattern**: context dict with items_in/items_out keys, caller mutates ctx[key] inside async with block
- **pipeline_run_status_values**: status column accepts 'running', 'ok', 'error'
- **pipeline_run_table_schema**: mem_pipeline_runs: project_id, pipeline, source_id, status, items_in, items_out, duration_ms, error_msg (max 500 chars), finished_at, id (uuid)
- **pipeline_run_timing_method**: time.monotonic() for duration calculation, stored as integer duration_ms
- **pipeline_trigger_sources**: three paths: planner interface, docs module (feature-based), direct chat execution; consolidated into unified approval/execution flow
- **planner_tag_schema_consolidation_proposed**: drop seq_num and source columns; keep creator only; reduce descriptors (short_desc, full_desc, requirements, acceptance_criteria, summary, action_items, design) to essential fields
- **planner_tags_core_columns**: requirements, acceptance_criteria, action_items, status, priority, due_date, requester, creator, created_at, updater, updated_at retained
- **planner_tags_schema_cleanup**: dropped summary, design, embedding (VECTOR 1536), extra columns; move to future merge-layer table (m027)
- **planner_tags_schema_refactored**: dropped seq_num, source, summary, design, embedding, extra; merged source into creator (username for users, 'ai' default); added updater and deliveries (JSONB); reordered with project_id after client_id, timestamps last
- **prompt_architecture**: core.prompt_loader for centralization; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
- **prompt_count_metric**: distinct metric tracked separately from event_count in work items API response
- **prompt_loading_pattern**: core.prompt_loader._prompts.content() replaces direct mng_system_roles queries
- **prompt_work_item_trigger_automation**: _run_promote_all_work_items() integrated into /memory command pipeline to refresh AI text fields and embedding vectors during memory generation
- **rel:aicli_tool:agent_context**: generates
- **rel:ai_rules_md:cursor_rules**: related_to
- **rel:ai_tag_suggestion:user_tags**: replaces
- **rel:ai_tag_suggestion:work_items_table**: related_to
- **rel:background_tasks:pipeline_logging**: depends_on
- **rel:commit_processing:exec_llm_flag**: replaces
- **rel:dashboard_module:pipeline_controller**: implements
- **rel:db_migrations:planner_tags**: implements
- **rel:docs_module:pipeline_trigger**: depends_on
- **rel:embedding_integration:prompt_work_item_trigger**: implements
- **rel:embedding_vectors:semantic_search**: enables
- **rel:event_filtering:noise_reduction**: implements
- **rel:exec_llm:event_id**: replaces
- **rel:frontend_ui_pattern:ai_tag_suggestion_feature**: implements
- **rel:m037:importance_column**: replaces
- **rel:mcp_tool_memory:work_items_table**: depends_on
- **rel:mem_ai_events:mem_mrr_commits**: backfill_depends_on
- **rel:mem_ai_events:mem_mrr_prompts**: backfill_depends_on
- **rel:mem_ai_events:work_items**: depends_on
- **rel:mem_ai_feature_snapshot:mng_clients**: depends_on
- **rel:mem_ai_feature_snapshot:mng_projects**: depends_on
- **rel:mem_ai_feature_snapshot:planner_tags**: depends_on
- **rel:mem_mrr_commits:mem_ai_events**: replaces
- **rel:mem_mrr_commits:mem_mrr_commits_code**: replaces
- **rel:memory_endpoint:tag_detection**: implements
- **rel:memory_system:session_tags**: implements
- **rel:pipeline_run:mem_pipeline_runs**: implements
- **rel:planner_tags:mng_deliveries**: depends_on
- **rel:planner_tags:vector_embedding**: replaces
- **rel:prompt_loader:mng_system_roles**: replaces
- **rel:route_memory:prompt_loader**: depends_on
- **rel:route_memory:sql_parameter_binding**: depends_on
- **rel:route_prompts:memory_embedding**: depends_on
- **rel:route_search:memory_embedding**: depends_on
- **rel:route_snapshots:prompt_loader**: depends_on
- **rel:route_work_items:sql_parameter_binding**: depends_on
- **rel:session_context:prompt_counter**: implements
- **rel:stag_command:tag_command**: replaces
- **rel:sticky_header:work_items_panel**: implements
- **rel:tag_reminder:session_context**: depends_on
- **rel:ui_notifications:error_handling**: related_to
- **rel:wiDeleteLinked:entities_js**: implements
- **rel:wiUnlink:wiRowLoading**: depends_on
- **rel:work_item_api:prompt_count**: depends_on
- **rel:work_item_consolidation:desc_ai**: depends_on
- **rel:work_item_deletion:api_endpoint**: depends_on
- **rel:work_item_embedding:prompt_work_item_trigger**: implements
- **rel:work_item_panel_sort:prompt_count**: implements
- **rel:work_item_panel:state_management**: implements
- **rel:work_item_vector_search:mcp_tools**: implements
- **route_work_items_sql_errors**: line_249_cur_execute_missing_parameter_binding_line_288_incomplete_column_selection_in_merged_query
- **session_context_prompt_counter**: prompt_count field added to session context JSON, initialized to 0, incremented on each prompt validation
- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
- **stale_code_removed**: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
- **tag_command_alias**: /stag replaces /tag due to Claude Code skill name conflict; identical functionality with immediate availability
- **tag_creation_workflow**: _wiPanelCreateTag creates tags without confirmation, auto-links work item, refreshes tag cache + planner table + category tag list
- **tag_filtering_scope_issue**: non-work-item tags (Shared-memory, billing) incorrectly appearing in work_items panel UI; scope filtering implementation in progress
- **tagging_system**: nested_hierarchy_beyond_2_levels
- **tagging_system_hierarchy**: nested_hierarchy_beyond_2_levels_approved
- **tag_reminder_display_format**: soft: '┄ Prompt #{N} ╌ still on: {tags}'; hard: multi-line box with current tags and re-send/update instructions
- **tag_reminder_feature**: soft reminder every N prompts (default 8, configurable via TAG_REMINDER_INTERVAL), hard check at 3× interval with tag confirmation requirement
- **tags_ai_deprecation**: tags_ai column in mem_mrr_commits removed; data now stored in mem_mrr_commits_code (per-symbol) and mem_ai_events (commit digest)
- **tag_suggestion_workflow**: auto-saved to session via _acceptSuggestedTag; tag management flows through Chat tab (+) with category selection and deduplication
- **ui_action_menu_pattern**: 3_dot_menu_for_action_visibility
- **ui_library**: 3_dot_menu_pattern
- **ui_toast_notification**: toast() function displays error messages with 'error' severity level
- **unimplemented_features**: memory_items_and_project_facts_tables_not_updating
- **unresolved_issues**: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition
- **user_tags_rendering**: removed from panel display (userTagsHtml variable deleted), stored in wi.user_tags array but no longer shown in UI
- **work_item_column_consolidation**: summary consolidated into desc_ai to reduce redundancy; ai_name→name_ai, ai_category→category_ai, ai_desc→desc_ai refactoring completed
- **work_item_deletion_endpoint**: DELETE /work-items/{id} with confirm dialog, cache clearing via window._wiPanelDelete, panel re-rendering
- **work_item_deletion_handler**: _wiDeleteLinked in entities.js with confirmation dialog and _wiRowLoading state management
- **work_item_deletion_pattern**: client-side confirmation dialog, async api.workItems.delete(), local state cleanup, re-render panel
- **work_item_description_processing**: newlines replaced with spaces and trimmed (replace(/\n/g,' ').trim()), clipped to 70 chars with ellipsis
- **work_item_display_fields**: ai_category icon mapping, status_user color mapping, seq_num sequence number, id identifier
- **work_item_embedding_integration**: _embed_work_item() persists vectors for name_ai + desc_ai + summary_ai concatenation; integrated into prompt_work_item() trigger and new work item creation flow
- **work_item_event_association**: two-path join: session_id match from source_event_id OR direct work_item_id link, both filtered by event_type
- **work_item_panel_column_order**: Name, prompt_count, commit_count, event_count, updated_at (prompts column added before commits, events moved last)
- **work_item_panel_column_widths**: prompt_count:46px, commit_count:46px, event_count:46px (resized from 52px event_count + 52px commit_count)
- **work_item_panel_sortable_fields**: prompt_count, event_count, commit_count, seq_num (prompt_count added to sort handler)
- **work_item_panel_state_management**: _wiPanelItems object stores work items, window._wiPanelDelete and window._wiPanelRefresh are global handlers
- **work_item_ui_column_widths**: 56px–80px for multi-column sortable table headers
- **work_item_ui_pattern**: multi-column sortable table with proper header styling, status color badges
- **work_item_unlink_handler**: _wiUnlink uses _wiRowLoading(id, true) for loading state during patch operation
- **work_item_vector_search**: MCP tool_memory.py semantic search includes work_items table with embedding <=> operator, returns category/name/description/status for non-archived items

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns, full_symbol generated); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel; Dashboard tab for pipeline visibility
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac/Windows/Linux)
- **database_schema**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features (unified); mem_mrr_commits_code, mem_mrr_tags (mirroring); per-project tables; shared users/usage_logs/transactions/session_tags/entity_categories tables
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with pgvector extensions + m001-m041 migration framework
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+ with pgvector extensions
- **build_tooling**: npm 8+ + Electron-builder + Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + npm run dev
- **prompt_management**: core.prompt_loader module with centralized prompt caching
- **schema_management**: db_schema.sql + db_migrations.py (m001-m037)
- **database_tables**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; Shared: users, usage_logs, transactions, session_tags, entity_categories, planner_tags, mng_tags_categories
- **embeddings**: text-embedding-3-small (1536-dim vectors)
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **schema_migrations**: m001-m041 framework with db_schema.sql as source of truth
- **llm_provider_location**: agents/providers/

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables for events, tags, facts, work items, features
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; login_as_first_level_hierarchy pattern for hierarchical Clients → Users
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules in agents/providers/ with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with exec_llm boolean flag
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; system metadata stripped, user-facing tags retained (phase, feature, bug, source)
- Agent roles loaded from DB (mng_agent_roles) with fallback prompts; 4-stage work item pipeline (PM→Architect→Developer→Reviewer) with auto_commit flag
- Database schema as single source of truth (db_schema.sql) with m001-m041 migration framework; column ordering: client_id → project_id → created_at/processed_at/embedding
- Backend module organization: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations
- Deployment: Railway (Dockerfile + railway.toml) for backend; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Tag suggestion with ai_tag_suggestion column and approve/remove buttons; simplified chip markup with category inference on tag creation

## In Progress

- Snapshot generation refactor (2026-04-15) — Simplified planner_tags upsert to flat string keys (requirements, action_items, design, code_summary); switched from Sonnet to Haiku; improved JSON parsing with JSONDecoder.raw_decode to handle edge cases
- Schema cleanup and refactoring (2026-04-14) — mem_ai_work_items table reorganized: removed status_ai dual-status design, reordered columns (seq_num moved near id), added explicit FOREIGN KEY constraint for merged_into, added ivfflat embedding index
- Work item pipeline refactor (2026-04-14) — Agent roles loaded from DB with fallback prompts; RoleCreate/RoleUpdate models updated; auto_commit boolean support added; 4-stage pipeline uses _load_role() with provider/model overrides
- Memory promotion timing instrumentation (2026-04-15) — Added _time.monotonic() tracking to _run_promote_all_work_items; updated _finish_run calls with t0 parameter for performance measurement
- Tag suggestion approval flow (2026-04-13) — ai_tag_suggestion column with approve/remove buttons; simplified chip markup; suggested_new tags rendering under investigation; improved tooltip UX
- Route history batch upsert fix (2026-04-06) — PostgreSQL ON CONFLICT DO UPDATE error resolved via JSONB merge operator (||) syntax correction; testing pending

## Active Features / Bugs / Tasks

### Ai_suggestion

- **test123** `[open]`

### Bug

- **hooks** `[open]`

### Doc_type

- **high-level-design** `[open]`
- **low-level-design** `[open]`
- **retrospective** `[open]`
- **Test** `[open]`
- **customer-meeting** `[open]`
- **architecture-decision** `[open]`

### Feature

- **pagination**
- **auth** `[open]`
- **workflow-runner** `[open]`
- **test-picker-feature** `[open]`
- **dropbox** `[open]`
- **billing** `[open]`
- **entity-routing** `[open]`
- **UI** `[open]`
- **shared-memory** `[open]`
- **mcp** `[open]`
- **graph-workflow** `[open]`
- **tagging** `[open]`
- **embeddings** `[open]`

### Phase

- **prod** `[open]`
- **development** `[open]`
- **discovery** `[open]`

### Task

- **implement-projects-tab** `[open]`
- **memory** `[open]`

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-15

diff --git a/.ai/rules.md b/.ai/rules.md
index d90eb4c..bd82af9 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-15 01:20 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-15 01:21 UTC
 
 # aicli — Shared AI Memory Platform
 


### `commit` — 2026-04-15

Commit: chore: consolidate and reorganize _system memory/context files after cla
Hash: ec75b516
Code files (9):
  - .ai/rules.md
  - .cursor/rules/aicli.mdrules
  - .github/copilot-instructions.md
  - backend/core/db_migrations.py
  - backend/core/db_schema.sql
  - backend/memory/memory_embedding.py
  - backend/memory/memory_files.py
  - backend/memory/memory_promotion.py
  - backend/routers/route_history.py
Generated/internal files: MEMORY.md, workspace/aicli/_system/.agent-context, workspace/aicli/_system/CONTEXT.md, workspace/aicli/_system/aicli/copilot.md, workspace/aicli/_system/claude/MEMORY.md
Symbols changed: _is_system_commit, _tag_fingerprint, m047_events_is_system

### `commit` — 2026-04-15

Commit: chore: clean up stale system context files after claude cli session 2a6b
Hash: 36dc1a0f
Generated/internal files: workspace/aicli/_system/commit_log.jsonl, workspace/aicli/_system/dev_runtime_state.json

### `commit: 2a6b600e-9046-4d7b-88e9-ddb136d6ed65` — 2026-04-15

Commits: chore: remove stale agent context and system prompt files after claude c | chore: clean up and restructure _system memory/context files after claud | chore: clean up stale agent context and system memory files after claude
Stats:  workspace/aicli/PROJECT.md      |   4 +-
 6 files changed, 229 insertions(+), 57 deletions(-)

### `commit` — 2026-04-15

diff --git a/backend/memory/memory_files.py b/backend/memory/memory_files.py
index df7bf1f..c1de7ee 100644
--- a/backend/memory/memory_files.py
+++ b/backend/memory/memory_files.py
@@ -49,7 +49,7 @@ _SQL_FACTS = """
 """
 
 _SQL_ACTIVE_WORK_ITEMS = """
-    SELECT wi.name_ai, wi.desc_ai, wi.category_ai,
+    SELECT wi.name_ai, wi.summary_ai, wi.category_ai,
            wi.seq_num, t.name AS tag_name
     FROM mem_ai_work_items wi
     LEFT JOIN planner_tags t ON t.id = wi.tag_id_user
@@ -167,9 +167,9 @@ class MemoryFiles:
 
                     # Active work items
                     cur.execute(_SQL_ACTIVE_WORK_ITEMS, (project_id,))
-                    for ai_name, ai_desc, ai_category, seq_num, tag_name in cur.fetchall():
+                    for ai_name, ai_summary, ai_category, seq_num, tag_name in cur.fetchall():
                         ctx["active_work"].append({
-                            "name": ai_name, "desc": (ai_desc or "")[:120],
+                            "name": ai_name, "desc": (ai_summary or "")[:120],
                             "lifecycle": "active", "category": ai_category,
                             "seq_num": seq_num, "tag_name": tag_name or ai_name,
                         })


### `commit` — 2026-04-15

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index ed04102..459cc85 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-15 01:19 UTC
+> Generated by aicli 2026-04-15 01:20 UTC
 
 # aicli — Shared AI Memory Platform
 

