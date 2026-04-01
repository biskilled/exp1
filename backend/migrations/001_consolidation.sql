-- 001_consolidation.sql
-- Consolidate planner_tags_meta → planner_tags, create mem_tags_relations,
-- migrate mem_mrr_tags + mem_ai_tags into mem_tags_relations,
-- drop redundant tables.
--
-- Safe to re-run: all DDL uses IF NOT EXISTS / IF EXISTS.

BEGIN;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1a. Add new columns to planner_tags
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS source              TEXT    NOT NULL DEFAULT 'user';
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS creator             TEXT;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS short_desc          TEXT;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS full_desc           TEXT;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS requirements        TEXT;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS acceptance_criteria TEXT;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS status_new          TEXT    NOT NULL DEFAULT 'open';
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS priority            SMALLINT NOT NULL DEFAULT 3;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS due_date            DATE;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS requester           TEXT;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS extra               JSONB   NOT NULL DEFAULT '{}';
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS summary             TEXT;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS action_items        TEXT;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS design              JSONB;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS code_summary        JSONB;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS is_reusable         BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS embedding           VECTOR(1536);

-- ─────────────────────────────────────────────────────────────────────────────
-- 1b. Copy planner_tags_meta → planner_tags
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
BEGIN
  IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'planner_tags_meta') THEN
    UPDATE planner_tags pt SET
        short_desc   = tm.description,
        requirements = tm.requirements,
        due_date     = tm.due_date,
        requester    = tm.requester,
        priority     = COALESCE(tm.priority, 3),
        extra        = COALESCE(tm.extra, '{}'),
        updated_at   = NOW()
    FROM planner_tags_meta tm WHERE tm.tag_id = pt.id;
  END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1c. Copy mem_ai_features → planner_tags
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
BEGIN
  IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'mem_ai_features') THEN
    UPDATE planner_tags pt SET
        summary      = mf.requirements,
        action_items = mf.action_items,
        design       = mf.design,
        code_summary = mf.code_summary,
        embedding    = mf.embedding,
        updated_at   = NOW()
    FROM mem_ai_features mf WHERE mf.tag_id = pt.id AND mf.project = pt.project;
  END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1d. Map old status/lifecycle → new status
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.columns
    WHERE table_name = 'planner_tags' AND column_name = 'lifecycle'
  ) THEN
    UPDATE planner_tags SET status_new =
        CASE WHEN lifecycle = 'done'     THEN 'done'
             WHEN status    = 'archived' THEN 'archived'
             WHEN status    = 'active'   THEN 'active'
             ELSE 'open' END;
  ELSE
    UPDATE planner_tags SET status_new =
        CASE WHEN status = 'archived' THEN 'archived'
             WHEN status = 'active'   THEN 'active'
             WHEN status = 'done'     THEN 'done'
             ELSE 'open' END;
  END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1e. Create mem_tags_relations
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mem_tags_relations (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tag_id              UUID         NOT NULL REFERENCES planner_tags(id) ON DELETE CASCADE,
    related_layer       TEXT         NOT NULL,   -- 'mirror' | 'ai'
    related_type        TEXT         NOT NULL,   -- 'prompt'|'commit'|'item'|'message'|'memory_event'|'work_item'|'session'
    related_id          TEXT         NOT NULL,   -- TEXT (not UUID) to accommodate commit hashes
    related_type_score  FLOAT,                   -- AI confidence score; NULL = exact match
    related_approved    TEXT,                    -- NULL=pending | 'approved' | 'rejected'
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (tag_id, related_type, related_id)
);
CREATE INDEX IF NOT EXISTS idx_mem_tags_rel_tag    ON mem_tags_relations(tag_id);
CREATE INDEX IF NOT EXISTS idx_mem_tags_rel_type   ON mem_tags_relations(related_type, related_id);
CREATE INDEX IF NOT EXISTS idx_mem_tags_rel_review ON mem_tags_relations(related_approved) WHERE related_approved IS NULL;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1f. Migrate mem_mrr_tags → mem_tags_relations
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
BEGIN
  IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'mem_mrr_tags') THEN
    INSERT INTO mem_tags_relations (tag_id, related_layer, related_type, related_id, created_at)
    SELECT tag_id, 'mirror', 'prompt', prompt_id::TEXT, created_at
    FROM mem_mrr_tags WHERE prompt_id IS NOT NULL
    ON CONFLICT DO NOTHING;

    INSERT INTO mem_tags_relations (tag_id, related_layer, related_type, related_id, created_at)
    SELECT tag_id, 'mirror', 'commit', commit_id, created_at
    FROM mem_mrr_tags WHERE commit_id IS NOT NULL
    ON CONFLICT DO NOTHING;

    INSERT INTO mem_tags_relations (tag_id, related_layer, related_type, related_id, created_at)
    SELECT tag_id, 'mirror', 'item', item_id::TEXT, created_at
    FROM mem_mrr_tags WHERE item_id IS NOT NULL
    ON CONFLICT DO NOTHING;

    INSERT INTO mem_tags_relations (tag_id, related_layer, related_type, related_id, created_at)
    SELECT tag_id, 'mirror', 'message', message_id::TEXT, created_at
    FROM mem_mrr_tags WHERE message_id IS NOT NULL
    ON CONFLICT DO NOTHING;
  END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1g. Migrate mem_ai_tags → mem_tags_relations
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
BEGIN
  IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'mem_ai_tags') THEN
    INSERT INTO mem_tags_relations (tag_id, related_layer, related_type, related_id, related_approved, created_at)
    SELECT tag_id, 'ai', 'memory_event', event_id::TEXT,
           CASE WHEN ai_suggested THEN NULL ELSE 'approved' END, created_at
    FROM mem_ai_tags
    ON CONFLICT DO NOTHING;
  END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1h. Fix UNIQUE constraint: (client_id, project, name) → (client_id, project, name, category_id)
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.table_constraints
    WHERE table_name = 'planner_tags' AND constraint_name = 'planner_tags_client_id_project_name_key'
  ) THEN
    ALTER TABLE planner_tags DROP CONSTRAINT planner_tags_client_id_project_name_key;
  END IF;

  IF NOT EXISTS (
    SELECT FROM information_schema.table_constraints
    WHERE table_name = 'planner_tags' AND constraint_name = 'planner_tags_project_name_cat_key'
  ) THEN
    ALTER TABLE planner_tags ADD CONSTRAINT planner_tags_project_name_cat_key
        UNIQUE(client_id, project, name, category_id);
  END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1i. Swap status columns: drop old status + lifecycle, rename status_new → status
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
BEGIN
  IF EXISTS (
    SELECT FROM information_schema.columns
    WHERE table_name = 'planner_tags' AND column_name = 'status'
  ) THEN
    ALTER TABLE planner_tags DROP COLUMN status;
  END IF;

  IF EXISTS (
    SELECT FROM information_schema.columns
    WHERE table_name = 'planner_tags' AND column_name = 'lifecycle'
  ) THEN
    ALTER TABLE planner_tags DROP COLUMN lifecycle;
  END IF;

  IF EXISTS (
    SELECT FROM information_schema.columns
    WHERE table_name = 'planner_tags' AND column_name = 'status_new'
  ) THEN
    ALTER TABLE planner_tags RENAME COLUMN status_new TO status;
  END IF;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1j. Drop redundant tables
-- ─────────────────────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS planner_tags_meta;
DROP TABLE IF EXISTS mem_ai_features;
DROP TABLE IF EXISTS mem_ai_tags;
DROP TABLE IF EXISTS mem_ai_tags_relations;
DROP TABLE IF EXISTS mem_mrr_tags;

COMMIT;
