"""
Project analytics — usage statistics derived from ConversationState data.
"""

from collections import defaultdict
from datetime import datetime


class ProjectAnalytics:

    def __init__(self, conversation):
        self.data = conversation.data

    def total_prompts(self) -> int:
        return len(self.data.get("conversation", []))

    def total_commits(self) -> int:
        return len(self.data.get("commits", []))

    def commits_by_feature(self) -> dict:
        features: dict = defaultdict(int)
        for commit in self.data.get("commits", []):
            feature = commit.get("feature") or "unassigned"
            features[feature] += 1
        return dict(features)

    def commits_by_tag(self) -> dict:
        tags: dict = defaultdict(int)
        for commit in self.data.get("commits", []):
            tag = commit.get("tag") or "untagged"
            tags[tag] += 1
        return dict(tags)

    def total_files_changed(self) -> int:
        return sum(
            len(c.get("files_changed", []))
            for c in self.data.get("commits", [])
        )

    def session_duration_hours(self) -> float:
        conversation = self.data.get("conversation", [])
        if len(conversation) < 2:
            return 0.0
        first = datetime.fromisoformat(conversation[0]["timestamp"])
        last = datetime.fromisoformat(conversation[-1]["timestamp"])
        return (last - first).total_seconds() / 3600

    def estimate_cost(self, cost_per_1k: float = 0.01) -> float:
        total_tokens = 0
        for entry in self.data.get("conversation", []):
            usage = entry.get("usage")
            if usage:
                total_tokens += usage.get("input_tokens", 0)
                total_tokens += usage.get("output_tokens", 0)
        return (total_tokens / 1000) * cost_per_1k
