"""
Lightweight memory store — Layer 4 (Historical Knowledge) of the 5-layer memory system.

Stores entries as JSONL (one JSON object per line) in {cli_data_dir}/memory.jsonl.
Supports retrieval by:
  - tag (exact)
  - feature (exact)
  - keyword (substring match across user_input + output)
  - recency (last N entries)

No ML dependencies, no model downloads, instant startup.
For a personal dev tool this covers all practical memory needs.
The "semantic" gap is covered by CLAUDE.md (project context) and the
self.messages list (full in-session conversation history).

cli_data_dir is read from config['cli_data_dir'] (default: '.aicli').
Set in aicli.yaml to change the storage location.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path


class MemoryStore:

    def __init__(self, config: dict, logger=None):
        self.enabled = config.get("memory_enabled", True)
        self.top_k = config.get("memory_top_k", 5)
        self.logger = logger
        _data_dir = config.get("cli_data_dir", ".aicli")
        self.path = Path(_data_dir) / "memory.jsonl"

        if not self.enabled:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)

        if self.logger:
            self.logger.info("memory_initialized", entries=self.count())

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add_entry(
        self,
        provider: str,
        role,
        user_input: str,
        output: str,
        commit_data: dict | None = None,
        feature: str | None = None,
        tag: str | None = None,
    ):
        if not self.enabled:
            return

        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "provider": provider,
            "role": role or "",
            "feature": feature or "",
            "tag": tag or "",
            "user_input": user_input,
            "output": output,
            "commit_hash": (commit_data or {}).get("hash", ""),
        }

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        if self.logger:
            self.logger.debug("memory_added", tag=tag, feature=feature)

    # ------------------------------------------------------------------
    # Read all entries
    # ------------------------------------------------------------------

    def _load_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        entries = []
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return entries

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int | None = None) -> list[str]:
        """Keyword search across user_input + output. Returns formatted text blocks."""
        if not self.enabled:
            return []

        k = top_k or self.top_k
        query_lower = query.lower()
        all_entries = self._load_all()

        # Score by number of query words that appear in the entry
        query_words = [w for w in query_lower.split() if len(w) > 2]

        scored = []
        for e in all_entries:
            haystack = (e.get("user_input", "") + " " + e.get("output", "")).lower()
            score = sum(1 for w in query_words if w in haystack)
            if score > 0:
                scored.append((score, e))

        scored.sort(key=lambda x: -x[0])
        return [self._format(e) for _, e in scored[:k]]

    def search_by_tag(self, tag: str, top_k: int | None = None) -> list[str]:
        """Return entries matching this tag exactly."""
        if not self.enabled:
            return []
        k = top_k or self.top_k
        matches = [e for e in self._load_all() if e.get("tag") == tag]
        return [self._format(e) for e in matches[-k:]]

    def search_by_feature(self, feature: str, top_k: int | None = None) -> list[str]:
        """Return entries matching this feature exactly."""
        if not self.enabled:
            return []
        k = top_k or self.top_k
        matches = [e for e in self._load_all() if e.get("feature") == feature]
        return [self._format(e) for e in matches[-k:]]

    def recent(self, top_k: int | None = None) -> list[str]:
        """Return the most recent N entries."""
        if not self.enabled:
            return []
        k = top_k or self.top_k
        return [self._format(e) for e in self._load_all()[-k:]]

    # ------------------------------------------------------------------

    def count(self) -> int:
        if not self.enabled or not self.path.exists():
            return 0
        return sum(1 for line in open(self.path, encoding="utf-8") if line.strip())

    def _format(self, e: dict) -> str:
        meta = f"[{e.get('ts','')[:10]}] {e.get('provider','')} feature={e.get('feature') or '-'} tag={e.get('tag') or '-'}"
        return f"{meta}\nUser: {e.get('user_input','')[:150]}\nOutput: {e.get('output','')[:300]}"

    # ------------------------------------------------------------------
    # Compaction — summarise old entries to keep the file manageable
    # ------------------------------------------------------------------

    def maybe_compact(
        self,
        llm_agent=None,
        threshold: int = 200,
        keep_recent: int = 50,
    ) -> bool:
        """
        If memory exceeds `threshold` entries:
          1. Summarise the oldest (count - keep_recent) entries via LLM
          2. Append the summary to memory_summary.md
          3. Rewrite memory.jsonl with only the most recent `keep_recent` entries

        Returns True if compaction ran, False otherwise.

        The LLM agent must have a .send(system, user) → str interface
        (compatible with OpenAIAgent or any BaseProvider).
        No compaction runs if llm_agent is None (safe to call without a key).
        """
        if not self.enabled or not llm_agent:
            return False

        all_entries = self._load_all()
        if len(all_entries) <= threshold:
            return False

        old_entries = all_entries[:-keep_recent]
        recent_entries = all_entries[-keep_recent:]

        # Build text block for the LLM
        lines = []
        for e in old_entries:
            ts = e.get("ts", "")[:10]
            prov = e.get("provider", "?")
            feat = e.get("feature") or ""
            tag = e.get("tag") or ""
            q = e.get("user_input", "")[:200]
            a = e.get("output", "")[:300]
            lines.append(
                f"[{ts}] {prov}"
                + (f" feature={feat}" if feat else "")
                + (f" tag={tag}" if tag else "")
                + f"\nQ: {q}\nA: {a}"
            )

        text_block = "\n\n".join(lines)
        system = "You are a technical summariser. Be concise and factual."
        user_prompt = (
            f"Summarise these {len(old_entries)} AI conversation entries into a "
            f"concise reference document.\n"
            f"Focus on: decisions made, patterns established, bugs fixed, features built.\n"
            f"Format as bullet points grouped by feature or topic. Keep it under 800 words.\n\n"
            f"ENTRIES:\n{text_block}"
        )

        try:
            summary = llm_agent.send(system, user_prompt)
        except Exception:
            return False  # don't corrupt memory if LLM call fails

        # Append to memory_summary.md (prepend so newest summary is first)
        summary_path = self.path.parent / "memory_summary.md"
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        new_section = (
            f"## Compaction — {date_str} ({len(old_entries)} entries → summary)\n\n"
            f"{summary}\n"
        )
        existing = summary_path.read_text(encoding="utf-8") if summary_path.exists() else ""
        summary_path.write_text(new_section + "\n---\n\n" + existing, encoding="utf-8")

        # Rewrite memory.jsonl with only recent entries
        with open(self.path, "w", encoding="utf-8") as f:
            for e in recent_entries:
                f.write(json.dumps(e) + "\n")

        return True

    def load_summary(self, max_chars: int = 2000) -> str:
        """
        Load memory_summary.md — the accumulated summaries of old entries.
        Injected into the context block so LLMs have historical project knowledge.
        """
        summary_path = self.path.parent / "memory_summary.md"
        if not summary_path.exists():
            return ""
        return summary_path.read_text(encoding="utf-8")[:max_chars]
