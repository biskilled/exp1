"""
memory_mirroring.py — Layer 1 of the three-layer memory architecture.

Stores source data as-is into the mem_mrr_* tables.  Every row has an
``ai_tags`` status column (NULL=unprocessed, 'approved', 'ignored') so the
tagging layer can query which rows still need AI tag suggestions.

Public API::

    mirroring = MemoryMirroring()
    prompt_id = mirroring.store_prompt(project, session_id, prompt, response, ...)
    count = mirroring.count_session_prompts(project, session_id)
    prompts = mirroring.get_last_n_prompts(project, session_id, n=5)
    untagged = mirroring.get_untagged(project, 'prompt', limit=50)
    mirroring.set_ai_tag_status('prompt', prompt_id, 'approved')
"""
from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from core.database import db

log = logging.getLogger(__name__)

# ── SQL constants ──────────────────────────────────────────────────────────────

_SQL_INSERT_PROMPT = """
    INSERT INTO mem_mrr_prompts
           (client_id, project, session_id, session_src_id, session_src_desc,
            llm_source, event_type, source_id, prompt, response,
            phase, metadata, ai_tags, created_at)
       VALUES (1, %s, %s, %s, %s, %s, 'prompt', %s, %s, %s, %s, %s::jsonb, NULL, %s::timestamptz)
       ON CONFLICT (client_id, project, source_id) WHERE source_id IS NOT NULL DO NOTHING
    RETURNING id
"""

_SQL_INSERT_COMMIT = """
    INSERT INTO mem_mrr_commits
           (client_id, project, commit_hash, commit_msg, summary,
            phase, feature, bug_ref, source, session_id, tags,
            committed_at, diff_details, ai_tags)
       VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s::jsonb, NULL)
       ON CONFLICT (commit_hash) DO NOTHING
    RETURNING id
"""

_SQL_INSERT_ITEM = """
    INSERT INTO mem_mrr_items
           (client_id, project, item_type, title, meeting_at, attendees,
            raw_text, summary, ai_tags)
       VALUES (1, %s, %s, %s, %s, %s, %s, %s, NULL)
    RETURNING id
"""

_SQL_INSERT_MESSAGE = """
    INSERT INTO mem_mrr_messages
           (client_id, project, platform, channel, thread_ref,
            messages, date_range, ai_tags)
       VALUES (1, %s, %s, %s, %s, %s::jsonb, %s, NULL)
    RETURNING id
"""

_SQL_COUNT_SESSION_PROMPTS = """
    SELECT COUNT(*) FROM mem_mrr_prompts
    WHERE client_id=1 AND project=%s AND session_id=%s
"""

_SQL_GET_LAST_N_PROMPTS = """
    SELECT id, prompt, response, session_id, created_at
    FROM mem_mrr_prompts
    WHERE client_id=1 AND project=%s AND session_id=%s
      AND response != ''
    ORDER BY created_at DESC
    LIMIT %s
"""

_SQL_GET_UNTAGGED_PROMPTS = """
    SELECT id::text, 'prompt' AS source_type, (prompt || ' ' || response)[:500] AS content_preview,
           created_at
    FROM mem_mrr_prompts
    WHERE client_id=1 AND project=%s AND ai_tags IS NULL
    ORDER BY created_at ASC
    LIMIT %s
"""

_SQL_GET_UNTAGGED_COMMITS = """
    SELECT id::text, 'commit' AS source_type,
           (commit_hash || ' ' || commit_msg)[:500] AS content_preview, created_at
    FROM mem_mrr_commits
    WHERE client_id=1 AND project=%s AND ai_tags IS NULL
    ORDER BY created_at ASC
    LIMIT %s
"""

_SQL_GET_UNTAGGED_ITEMS = """
    SELECT id::text, 'item' AS source_type, raw_text[:500] AS content_preview, created_at
    FROM mem_mrr_items
    WHERE client_id=1 AND project=%s AND ai_tags IS NULL
    ORDER BY created_at ASC
    LIMIT %s
"""

_SQL_SET_AI_TAG_STATUS_PROMPT = (
    "UPDATE mem_mrr_prompts SET ai_tags=%s WHERE client_id=1 AND id=%s::uuid"
)
_SQL_SET_AI_TAG_STATUS_COMMIT = (
    "UPDATE mem_mrr_commits SET ai_tags=%s WHERE client_id=1 AND id=%s"
)
_SQL_SET_AI_TAG_STATUS_ITEM = (
    "UPDATE mem_mrr_items SET ai_tags=%s WHERE client_id=1 AND id=%s::uuid"
)
_SQL_SET_AI_TAG_STATUS_MESSAGE = (
    "UPDATE mem_mrr_messages SET ai_tags=%s WHERE client_id=1 AND id=%s::uuid"
)


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
        llm_source: str = "claude_cli",
        phase: Optional[str] = None,
        metadata: str = "{}",
        session_src_id: Optional[str] = None,
        session_src_desc: Optional[str] = None,
        ts: Optional[str] = None,
    ) -> Optional[str]:
        """Insert a prompt/response into mem_mrr_prompts. Returns the UUID string or None."""
        if not db.is_available():
            return None
        import json
        from datetime import datetime, timezone
        if ts is None:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        _SQL_INSERT_PROMPT,
                        (project, session_id, session_src_id, session_src_desc,
                         llm_source, source_id,
                         (prompt or "")[:4000], (response or "")[:8000],
                         phase, metadata, ts),
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
        phase: Optional[str] = None,
        feature: Optional[str] = None,
        bug_ref: Optional[str] = None,
        source: str = "git",
        session_id: Optional[str] = None,
        tags: str = "{}",
        committed_at: Optional[str] = None,
        diff_details: str = "{}",
    ) -> Optional[int]:
        """Insert a commit into mem_mrr_commits. Returns the serial id or None."""
        if not db.is_available():
            return None
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        _SQL_INSERT_COMMIT,
                        (project, commit_hash, commit_msg, summary,
                         phase, feature, bug_ref, source, session_id,
                         tags, committed_at, diff_details),
                    )
                    row = cur.fetchone()
            return row[0] if row else None
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
    ) -> Optional[str]:
        """Insert a document item into mem_mrr_items. Returns UUID string or None."""
        if not db.is_available():
            return None
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        _SQL_INSERT_ITEM,
                        (project, item_type, title, meeting_at, attendees, raw_text, summary),
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
    ) -> Optional[str]:
        """Insert a message chunk into mem_mrr_messages. Returns UUID string or None."""
        if not db.is_available():
            return None
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        _SQL_INSERT_MESSAGE,
                        (project, platform, channel, thread_ref, messages_json, date_range),
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
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_COUNT_SESSION_PROMPTS, (project, session_id))
                    return cur.fetchone()[0]
        except Exception:
            return 0

    def get_last_n_prompts(self, project: str, session_id: str, n: int) -> list[dict]:
        """Return the last N prompts for this session, oldest-first."""
        if not db.is_available():
            return []
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(_SQL_GET_LAST_N_PROMPTS, (project, session_id, n))
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
        """Return rows with ai_tags IS NULL for the given source_type."""
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
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (project, limit))
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

    def set_ai_tag_status(self, source_type: str, row_id: str, status: str) -> None:
        """Set ai_tags = 'approved' | 'ignored' on a mirroring row."""
        if not db.is_available():
            return
        sql_map = {
            "prompt":  _SQL_SET_AI_TAG_STATUS_PROMPT,
            "commit":  _SQL_SET_AI_TAG_STATUS_COMMIT,
            "item":    _SQL_SET_AI_TAG_STATUS_ITEM,
            "message": _SQL_SET_AI_TAG_STATUS_MESSAGE,
        }
        sql = sql_map.get(source_type)
        if not sql:
            return
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (status, row_id))
        except Exception as e:
            log.debug(f"MemoryMirroring.set_ai_tag_status error: {e}")
