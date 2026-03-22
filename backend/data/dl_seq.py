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
    seq = next_seq(cur, project, category_name)
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
}

_DEFAULT_START = 10000


def next_seq(cur, project: str, category: str) -> int:
    """Atomically allocate and return the next seq_num for (project, category).

    Uses INSERT…ON CONFLICT to guarantee exactly-once increment even under
    concurrent requests.  Must be called inside an open transaction that will
    be committed by the caller.
    """
    cat = (category or "").lower()
    start = SEQ_STARTS.get(cat, _DEFAULT_START)

    # On first use for this (project, category) the row is created with
    # next_val = start + 1 and we return start (the first assigned value).
    # On subsequent calls the UPDATE adds 1 and we return new_next - 1.
    cur.execute(
        """INSERT INTO pr_seq_counters (client_id, project, category, next_val)
               VALUES (1, %s, %s, %s)
               ON CONFLICT (client_id, project, category) DO UPDATE
                   SET next_val = pr_seq_counters.next_val + 1
               RETURNING next_val""",
        (project, category, start + 1),
    )
    return cur.fetchone()[0] - 1
