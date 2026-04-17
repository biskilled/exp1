"""
seq.py — Atomic sequential ID counter for work items and entity values.

Each category has its own number range so users can identify items by a stable
short number across any AI tool:
  feature   → #10000+
  bug       → #20000+
  task      → #30000+
  component → #40000+
  epic      → #50000+

Usage (inside an open connection cursor):
    from data.dl_seq import next_seq
    seq = next_seq(cur, project_id, category_name)
"""
from __future__ import annotations

# Starting values per category (lower bound, first id = this value)
SEQ_STARTS: dict[str, int] = {
    "feature":   10000,
    "bug":       20000,
    "task":      30000,
    "component": 40000,
    "epic":      50000,
    "story":     60000,
    # Backlog source-type prefixes (single uppercase letter)
    "P":         100000,   # prompts
    "C":         200000,   # commits
    "M":         300000,   # messages
    "I":         400000,   # items
    # Planner-tag sequential IDs (human-readable numbers per project)
    # Use cases start at 10000 → displayed as UC10001, UC10002 …
    # Features start at 20000 → displayed as F20001, F20002 …
    # Bugs     start at 30000 → displayed as B30001, B30002 …
    "uc":        10000,    # use_case planner tags
    "feat":      20000,    # feature  planner tags
    "bug":       30000,    # bug      planner tags
}

_DEFAULT_START = 10000


def next_seq(cur, project_id: int, category: str) -> int:
    """Atomically allocate and return the next seq_num for (project_id, category).

    Uses INSERT…ON CONFLICT to guarantee exactly-once increment even under
    concurrent requests.  Must be called inside an open transaction that will
    be committed by the caller.

    Args:
        cur:        An open psycopg2 cursor within an active transaction.
        project_id: Integer PK from the projects table (replaces project TEXT).
        category:   Category name, e.g. 'feature', 'bug', 'task'.

    Returns:
        The allocated sequential number (start value on first use, then +1 each call).
    """
    cat = (category or "").lower()
    start = SEQ_STARTS.get(cat, _DEFAULT_START)

    # On first use for this (project_id, category) the row is created with
    # next_val = start + 1 and we return start (the first assigned value).
    # On subsequent calls the UPDATE adds 1 and we return new_next - 1.
    cur.execute(
        """INSERT INTO pr_seq_counters (project_id, category, next_val)
               VALUES (%s, %s, %s)
               ON CONFLICT (project_id, category) DO UPDATE
                   SET next_val = pr_seq_counters.next_val + 1
               RETURNING next_val""",
        (project_id, category, start + 1),
    )
    return cur.fetchone()[0] - 1
