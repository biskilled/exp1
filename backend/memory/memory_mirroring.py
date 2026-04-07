"""
memory_mirroring.py — Layer 1 of the three-layer memory architecture.

Stores source data as-is into the mem_mrr_* tables.  Each row has an
inline ``tags JSONB`` column (e.g. ``{"phase": "discovery", "feature": "auth"}``)
set by: (1) hook at log time, (2) UI History picker, (3) bulk session-tag API.

Public API::

    mirroring = MemoryMirroring()
    prompt_id = mirroring.store_prompt(project, session_id, prompt, response, ...)
    count = mirroring.count_session_prompts(project, session_id)
    prompts = mirroring.get_last_n_prompts(project, session_id, n=5)
    untagged = mirroring.get_untagged(project, 'prompt', limit=50)
    mirroring.append_tag('prompt', source_id, 'phase:discovery')
    mirroring.remove_tag('commit', commit_hash, 'phase:development')
"""
from __future__ import annotations

import json
import logging
from typing import Optional
from uuid import UUID

from core.database import db
from core.tags import tags_to_dict, parse_tag

log = logging.getLogger(__name__)

# ── SQL constants ──────────────────────────────────────────────────────────────

_SQL_INSERT_PROMPT = """
    INSERT INTO mem_mrr_prompts
           (project_id, session_id, source_id,
            prompt, response, tags, created_at)
       VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::timestamptz)
       ON CONFLICT (project_id, source_id) WHERE source_id IS NOT NULL DO NOTHING
    RETURNING id
"""

_SQL_INSERT_COMMIT = """
    INSERT INTO mem_mrr_commits
           (project_id, commit_hash, commit_msg, summary,
            session_id, committed_at, tags)
       VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
       ON CONFLICT (commit_hash) DO NOTHING
    RETURNING commit_hash
"""

_SQL_INSERT_ITEM = """
    INSERT INTO mem_mrr_items
           (project_id, item_type, title, meeting_at, attendees,
            raw_text, summary, tags)
       VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
    RETURNING id
"""

_SQL_INSERT_MESSAGE = """
    INSERT INTO mem_mrr_messages
           (project_id, platform, channel, thread_ref,
            messages, date_range, tags)
       VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s::jsonb)
    RETURNING id
"""

_SQL_COUNT_SESSION_PROMPTS = """
    SELECT COUNT(*) FROM mem_mrr_prompts
    WHERE project_id=%s AND session_id=%s
"""

_SQL_GET_LAST_N_PROMPTS = """
    SELECT id, prompt, response, session_id, created_at
    FROM mem_mrr_prompts
    WHERE project_id=%s AND session_id=%s
      AND response != ''
    ORDER BY created_at DESC
    LIMIT %s
"""

# "Untagged" = no user-facing classification tags (phase/feature/bug etc.)
# System keys (source, llm) are always present but do not count as "tagged".
_SQL_GET_UNTAGGED_PROMPTS = """
    SELECT source_id, 'prompt' AS source_type,
           (prompt || ' ' || response)[:500] AS content_preview, created_at
    FROM mem_mrr_prompts
    WHERE project_id=%s
      AND (tags - 'source' - 'llm') = '{}'::jsonb
    ORDER BY created_at ASC
    LIMIT %s
"""

_SQL_GET_UNTAGGED_COMMITS = """
    SELECT commit_hash, 'commit' AS source_type,
           (commit_hash || ' ' || commit_msg)[:500] AS content_preview, created_at
    FROM mem_mrr_commits
    WHERE project_id=%s
      AND (tags - 'source' - 'llm') = '{}'::jsonb
    ORDER BY created_at ASC
    LIMIT %s
"""

_SQL_GET_UNTAGGED_ITEMS = """
    SELECT id::text, 'item' AS source_type, raw_text[:500] AS content_preview, created_at
    FROM mem_mrr_items
    WHERE project_id=%s
      AND (tags - 'source' - 'llm') = '{}'::jsonb
    ORDER BY created_at ASC
    LIMIT %s
"""

# JSONB merge (||) is idempotent for same key — new value overwrites old
_SQL_APPEND_TAG_PROMPT   = "UPDATE mem_mrr_prompts  SET tags = tags || %s::jsonb WHERE source_id=%s"
_SQL_APPEND_TAG_COMMIT   = "UPDATE mem_mrr_commits  SET tags = tags || %s::jsonb WHERE commit_hash=%s"
_SQL_APPEND_TAG_ITEM     = "UPDATE mem_mrr_items    SET tags = tags || %s::jsonb WHERE id=%s::uuid"
_SQL_APPEND_TAG_MESSAGE  = "UPDATE mem_mrr_messages SET tags = tags || %s::jsonb WHERE id=%s::uuid"

# JSONB key removal: tags - 'phase'  removes the "phase" key
_SQL_REMOVE_TAG_PROMPT   = "UPDATE mem_mrr_prompts  SET tags = tags - %s WHERE source_id=%s"
_SQL_REMOVE_TAG_COMMIT   = "UPDATE mem_mrr_commits  SET tags = tags - %s WHERE commit_hash=%s"
_SQL_REMOVE_TAG_ITEM     = "UPDATE mem_mrr_items    SET tags = tags - %s WHERE id=%s::uuid"
_SQL_REMOVE_TAG_MESSAGE  = "UPDATE mem_mrr_messages SET tags = tags - %s WHERE id=%s::uuid"


class MemoryMirroring:
    """Stores raw source data in the mem_mrr_* mirroring tables."""

    def store_prompt(
        self,
        project: str,
        session_id: str,
        prompt: str,
        response: str,
        *,
        source_id: Optional[str] = None,
        source: str = "claude_cli",
        llm_source: str = "",  # backward-compat alias for source
        tags: Optional[list[str] | dict] = None,
        ts: Optional[str] = None,
    ) -> Optional[str]:
        """Insert a prompt/response into mem_mrr_prompts. Returns the UUID string or None."""
        if not db.is_available():
            return None
        from datetime import datetime, timezone
        if ts is None:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        # llm_source is kept for backward compat; source takes precedence
        effective_source = source or llm_source or "claude_cli"
        tags_dict = tags_to_dict(tags)
        tags_dict["source"] = effective_source
        project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        _SQL_INSERT_PROMPT,
                        (project_id, session_id, source_id,
                         (prompt or "")[:4000], (response or "")[:8000],
                         json.dumps(tags_dict), ts),
                    )
                    row = cur.fetchone()
            return str(row[0]) if row else None
        except Exception as e:
            log.debug(f"MemoryMirroring.store_prompt error: {e}")
            return None

    def store_commit(
        self,
        project: str,
        commit_hash: str,
        commit_msg: str,
        *,
        summary: str = "",
        source: str = "git",
        session_id: Optional[str] = None,
        committed_at: Optional[str] = None,
        tags: Optional[list[str] | dict] = None,
        **_ignored,  # absorb any legacy kwargs (e.g. diff_details)
    ) -> Optional[str]:
        """Insert a commit into mem_mrr_commits. Returns commit_hash or None."""
        if not db.is_available():
            return None
        tags_dict = tags_to_dict(tags)
        tags_dict["source"] = source
        project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        _SQL_INSERT_COMMIT,
                        (project_id, commit_hash, commit_msg, summary,
                         session_id, committed_at, json.dumps(tags_dict)),
                    )
                    row = cur.fetchone()
            return str(row[0]) if row else None
        except Exception as e:
            log.debug(f"MemoryMirroring.store_commit error: {e}")
            return None

    def store_item(
        self,
        project: str,
        item_type: str,
        raw_text: str,
        *,
        title: Optional[str] = None,
        meeting_at: Optional[str] = None,
        attendees: Optional[list] = None,
        summary: Optional[str] = None,
        tags: Optional[list[str] | dict] = None,
    ) -> Optional[str]:
        """Insert a document item into mem_mrr_items. Returns UUID string or None."""
        if not db.is_available():
            return None
        project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        _SQL_INSERT_ITEM,
                        (project_id, item_type, title, meeting_at, attendees,
                         raw_text, summary, json.dumps(tags_to_dict(tags))),
                    )
                    row = cur.fetchone()
            return str(row[0]) if row else None
        except Exception as e:
            log.debug(f"MemoryMirroring.store_item error: {e}")
            return None

    def store_message(
        self,
        project: str,
        platform: str,
        messages_json: str,
        *,
        channel: Optional[str] = None,
        thread_ref: Optional[str] = None,
        date_range: Optional[str] = None,
        tags: Optional[list[str] | dict] = None,
    ) -> Optional[str]:
        """Insert a message chunk into mem_mrr_messages. Returns UUID string or None."""
        if not db.is_available():
            return None
        project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        _SQL_INSERT_MESSAGE,
                        (project_id, platform, channel, thread_ref,
                         messages_json, date_range, json.dumps(tags_to_dict(tags))),
                    )
                    row = cur.fetchone()
            return str(row[0]) if row else None
        except Exception as e:
            log.debug(f"MemoryMirroring.store_message error: {e}")
            return None

    def count_session_prompts(self, project: str, session_id: str) -> int:
        """Count prompts in this session (used to decide when to trigger batch digest)."""
        if not db.is_available():
            return 0
        project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_COUNT_SESSION_PROMPTS, (project_id, session_id))
                    return cur.fetchone()[0]
        except Exception:
            return 0

    def get_last_n_prompts(self, project: str, session_id: str, n: int) -> list[dict]:
        """Return the last N prompts for this session, oldest-first."""
        if not db.is_available():
            return []
        project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_LAST_N_PROMPTS, (project_id, session_id, n))
                    rows = list(reversed(cur.fetchall()))
            return [
                {
                    "id": str(r[0]),
                    "prompt": r[1],
                    "response": r[2],
                    "session_id": r[3],
                    "created_at": r[4].isoformat() if r[4] else None,
                }
                for r in rows
            ]
        except Exception as e:
            log.debug(f"MemoryMirroring.get_last_n_prompts error: {e}")
            return []

    def get_untagged(
        self, project: str, source_type: str, limit: int = 50
    ) -> list[dict]:
        """Return rows with empty tags ({}) for the given source_type."""
        if not db.is_available():
            return []
        sql_map = {
            "prompt":  _SQL_GET_UNTAGGED_PROMPTS,
            "commit":  _SQL_GET_UNTAGGED_COMMITS,
            "item":    _SQL_GET_UNTAGGED_ITEMS,
        }
        sql = sql_map.get(source_type)
        if not sql:
            return []
        project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (project_id, limit))
                    rows = cur.fetchall()
            return [
                {
                    "id":              r[0],
                    "source_type":     r[1],
                    "content_preview": r[2],
                    "created_at":      r[3].isoformat() if r[3] else None,
                }
                for r in rows
            ]
        except Exception as e:
            log.debug(f"MemoryMirroring.get_untagged({source_type}) error: {e}")
            return []

    def append_tag(self, source_type: str, row_id: str, tag: str) -> None:
        """Merge a tag string into the tags JSONB dict of a mirroring row (idempotent)."""
        if not db.is_available():
            return
        sql_map = {
            "prompt":  _SQL_APPEND_TAG_PROMPT,
            "commit":  _SQL_APPEND_TAG_COMMIT,
            "item":    _SQL_APPEND_TAG_ITEM,
            "message": _SQL_APPEND_TAG_MESSAGE,
        }
        sql = sql_map.get(source_type)
        if not sql:
            return
        k, v = parse_tag(tag)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (json.dumps({k: v}), row_id))
        except Exception as e:
            log.debug(f"MemoryMirroring.append_tag error: {e}")

    def remove_tag(self, source_type: str, row_id: str, tag: str) -> None:
        """Remove a tag key from the tags JSONB dict of a mirroring row."""
        if not db.is_available():
            return
        sql_map = {
            "prompt":  _SQL_REMOVE_TAG_PROMPT,
            "commit":  _SQL_REMOVE_TAG_COMMIT,
            "item":    _SQL_REMOVE_TAG_ITEM,
            "message": _SQL_REMOVE_TAG_MESSAGE,
        }
        sql = sql_map.get(source_type)
        if not sql:
            return
        k, _ = parse_tag(tag)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (k, row_id))
        except Exception as e:
            log.debug(f"MemoryMirroring.remove_tag error: {e}")

    # ── Backward compat alias ──────────────────────────────────────────────────

    def set_ai_tag_status(self, source_type: str, row_id: str, status: str) -> None:
        """Deprecated: use append_tag/remove_tag. No-op — ai_tags column removed."""
        pass
