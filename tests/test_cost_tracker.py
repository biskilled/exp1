"""Tests for core/cost_tracker.py — CostTracker."""

import json
import pytest
from pathlib import Path

from core.cost_tracker import CostTracker, _calc_cost, PRICING


class TestCalcCost:
    def test_known_model_pricing(self):
        # claude-sonnet-4-6: $3.00/1M input, $15.00/1M output
        cost = _calc_cost("claude-sonnet-4-6", 1_000_000, 0)
        assert abs(cost - 3.00) < 0.01

        cost = _calc_cost("claude-sonnet-4-6", 0, 1_000_000)
        assert abs(cost - 15.00) < 0.01

    def test_unknown_model_uses_default_pricing(self):
        # Default: $1.00/$5.00 per million
        cost = _calc_cost("unknown-model-xyz", 1_000_000, 0)
        assert abs(cost - 1.00) < 0.01

    def test_zero_tokens_is_zero_cost(self):
        assert _calc_cost("gpt-4o", 0, 0) == 0.0

    def test_deepseek_cheapest_per_token(self):
        # DeepSeek is much cheaper than Claude for same token count
        deepseek_cost = _calc_cost("deepseek-chat", 100_000, 100_000)
        claude_cost = _calc_cost("claude-sonnet-4-6", 100_000, 100_000)
        assert deepseek_cost < claude_cost


class TestCostTrackerRecord:
    def test_record_returns_cost(self):
        tracker = CostTracker("test_workflow")
        cost = tracker.record(
            step_name="design",
            provider="claude",
            model="claude-sonnet-4-6",
            input_tokens=1000,
            output_tokens=500,
        )
        assert cost > 0

    def test_record_accumulates_steps(self):
        tracker = CostTracker("test_workflow")
        tracker.record("step1", "claude", "claude-sonnet-4-6", 1000, 200)
        tracker.record("step2", "deepseek", "deepseek-chat", 1000, 200)
        assert len(tracker.steps) == 2

    def test_total_cost_sum(self):
        tracker = CostTracker("test_workflow")
        c1 = tracker.record("s1", "claude", "claude-sonnet-4-6", 1000, 200)
        c2 = tracker.record("s2", "deepseek", "deepseek-chat", 1000, 200)
        assert abs(tracker.total_cost - (c1 + c2)) < 1e-9

    def test_total_tokens(self):
        tracker = CostTracker("test_workflow")
        tracker.record("s1", "claude", "claude-sonnet-4-6", 1000, 200)
        tracker.record("s2", "openai", "gpt-4.1", 500, 100)
        assert tracker.total_input_tokens == 1500
        assert tracker.total_output_tokens == 300

    def test_score_stored_when_provided(self):
        tracker = CostTracker("test_workflow")
        tracker.record("review", "deepseek", "deepseek-chat", 500, 100, score=7.5)
        assert tracker.steps[0]["score"] == 7.5

    def test_score_absent_when_not_provided(self):
        tracker = CostTracker("test_workflow")
        tracker.record("review", "deepseek", "deepseek-chat", 500, 100)
        assert "score" not in tracker.steps[0]


class TestCostTrackerSave:
    def test_save_writes_jsonl(self, tmp_path):
        tracker = CostTracker("my_workflow", project_dir=tmp_path)
        tracker.record("s1", "claude", "claude-sonnet-4-6", 100, 50)
        path = tracker.save()

        assert path is not None
        assert path.exists()
        line = json.loads(path.read_text().strip())
        assert line["workflow"] == "my_workflow"
        assert line["total_cost_usd"] >= 0
        assert len(line["steps"]) == 1

    def test_save_appends_not_overwrites(self, tmp_path):
        tracker1 = CostTracker("wf1", project_dir=tmp_path)
        tracker1.record("s1", "claude", "claude-sonnet-4-6", 100, 50)
        tracker1.save()

        tracker2 = CostTracker("wf2", project_dir=tmp_path)
        tracker2.record("s1", "openai", "gpt-4.1", 200, 80)
        tracker2.save()

        costs_path = tmp_path / ".aicli" / "workflow_costs.jsonl"
        lines = [l for l in costs_path.read_text().splitlines() if l.strip()]
        assert len(lines) == 2

    def test_save_returns_none_without_project_dir(self):
        tracker = CostTracker("wf", project_dir=None)
        result = tracker.save()
        assert result is None


class TestPricingCoverage:
    def test_all_models_in_pricing_have_input_and_output(self):
        for model, prices in PRICING.items():
            assert "input" in prices, f"{model} missing 'input'"
            assert "output" in prices, f"{model} missing 'output'"
            assert prices["input"] >= 0
            assert prices["output"] >= 0
