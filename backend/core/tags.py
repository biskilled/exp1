"""
core/tags.py — Utilities for converting between tag formats.

Storage format  : JSONB dict  {"phase": "discovery", "feature": "auth-refactor"}
API wire format : string list ["phase:discovery", "feature:auth-refactor"]

Use these helpers at every DB read/write boundary so the rest of the codebase
can work with plain string lists while the DB stores efficient JSONB dicts.
"""
from __future__ import annotations

import json


def tags_to_dict(tags: list[str] | dict | None) -> dict[str, str]:
    """Convert wire-format string list → JSONB dict for storage.

    "phase:discovery"        → {"phase": "discovery"}
    "work-item:abc-uuid"     → {"work-item": "abc-uuid"}
    bare "mytag" (no colon)  → {"tag": "mytag"}
    """
    if not tags:
        return {}
    if isinstance(tags, dict):
        return {str(k): str(v) for k, v in tags.items()}
    result: dict[str, str] = {}
    for t in tags:
        i = t.find(":")
        if i > 0:
            result[t[:i]] = t[i + 1:]
        else:
            result["tag"] = t
    return result


def tags_to_list(tags: dict | list | None) -> list[str]:
    """Convert JSONB dict → wire-format string list for API responses.

    {"phase": "discovery", "feature": "auth"} → ["phase:discovery", "feature:auth"]
    Already-a-list passthrough (for compat with old code paths).
    """
    if not tags:
        return []
    if isinstance(tags, list):
        return [str(t) for t in tags]
    return [f"{k}:{v}" for k, v in tags.items()]


def parse_tag(tag_str: str) -> tuple[str, str]:
    """Split 'phase:discovery' → ('phase', 'discovery').  No-colon → ('tag', value)."""
    i = tag_str.find(":")
    if i > 0:
        return tag_str[:i], tag_str[i + 1:]
    return "tag", tag_str


def tag_merge_sql() -> str:
    """Return the PostgreSQL expression to idempotently merge a JSONB tag dict.

    Usage in a parameterised query:
        UPDATE tbl SET tags = tags || %s::jsonb WHERE ...
    Pass json.dumps(tags_to_dict(["phase:discovery"])) as the param.
    """
    return "tags || %s::jsonb"


def tag_remove_sql() -> str:
    """Return the PostgreSQL expression to remove a key from a JSONB tags dict.

    Usage:
        UPDATE tbl SET tags = tags - %s WHERE ...
    Pass the key string (e.g. "phase") as the param.
    """
    return "tags - %s"
