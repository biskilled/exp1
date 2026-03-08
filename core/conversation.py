"""
Persistent conversation state with feature and tag tracking.
Stores conversation turns, commits, and a rolling project summary.
"""

import json
import os
from datetime import datetime, timezone


class ConversationState:

    def __init__(self, max_history: int = 200, path: str = ".aicli/current_session.json", cli_data_dir: str = ".aicli"):
        self.max_history = max_history
        self.path = path

        os.makedirs(os.path.dirname(path), exist_ok=True)

        # Default structure — loaded from disk if file exists
        self.data: dict = {
            "session_id": datetime.now(timezone.utc).isoformat(),
            "current_feature": None,
            "current_tag": None,
            "conversation": [],   # list of turn dicts
            "commits": [],        # list of commit dicts
            "project_summary": "",
            "tags": {},           # {tag_name: [entry indices]}
            "features": {},       # {feature_name: count}
        }

        self.load()

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def append(self, provider: str, role, user_input: str, output: str, commit=None, usage=None):
        """Record a conversation turn and optional commit metadata."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": provider,
            "role": role,
            "user_input": user_input,
            "output": output,
            "feature": self.get_feature(),
            "tag": self.get_tag(),
            "usage": usage,
        }

        self.data["conversation"].append(entry)

        # Update feature counter
        if entry["feature"]:
            self.data["features"][entry["feature"]] = (
                self.data["features"].get(entry["feature"], 0) + 1
            )

        # Update tag index
        if entry["tag"]:
            tag = entry["tag"]
            idx = len(self.data["conversation"]) - 1
            if tag not in self.data["tags"]:
                self.data["tags"][tag] = []
            self.data["tags"][tag].append(idx)

        if commit:
            commit_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "feature": self.get_feature(),
                "tag": self.get_tag(),
                "provider": provider,
                "role": role,
                "user_prompt": user_input,
                "commit_hash": commit.get("hash"),
                "commit_message": commit.get("message"),
                "files_changed": commit.get("files", []),
                "change_stats": commit.get("stats"),
            }
            self.data["commits"].append(commit_entry)

        # Trim conversation history to max
        if len(self.data["conversation"]) > self.max_history:
            self.data["conversation"] = self.data["conversation"][-self.max_history:]

        self.save()

    def update_summary(self, summary: str):
        self.data["project_summary"] = summary
        self.save()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, encoding="utf-8") as f:
                    loaded = json.load(f)
                # Merge loaded data, preserving new keys with defaults
                for key, value in loaded.items():
                    self.data[key] = value
                # Ensure new keys exist even in old session files
                self.data.setdefault("tags", {})
                self.data.setdefault("features", {})
                self.data.setdefault("current_tag", None)
            except (json.JSONDecodeError, KeyError):
                pass  # keep defaults on corrupt file

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    # ------------------------------------------------------------------
    # Feature tracking
    # ------------------------------------------------------------------

    def set_feature(self, feature_name: str):
        self.data["current_feature"] = feature_name
        self.save()

    def get_feature(self) -> str | None:
        return self.data.get("current_feature")

    def list_features(self) -> dict:
        return self.data.get("features", {})

    # ------------------------------------------------------------------
    # Tag tracking
    # ------------------------------------------------------------------

    def set_tag(self, tag_name: str):
        self.data["current_tag"] = tag_name
        self.save()

    def get_tag(self) -> str | None:
        return self.data.get("current_tag")

    def list_tags(self) -> dict:
        """Return tag → count mapping."""
        return {tag: len(indices) for tag, indices in self.data.get("tags", {}).items()}

    def get_entries_by_tag(self, tag_name: str) -> list[dict]:
        """Return all conversation entries associated with a tag."""
        indices = self.data.get("tags", {}).get(tag_name, [])
        conversation = self.data.get("conversation", [])
        return [conversation[i] for i in indices if i < len(conversation)]

    # ------------------------------------------------------------------
    # History helpers
    # ------------------------------------------------------------------

    def get_recent_history(self, limit: int = 10) -> list[dict]:
        return self.data["conversation"][-limit:]
