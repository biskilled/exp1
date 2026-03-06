"""Tests for workflows/runner.py — JSON extraction, workflow loading, step routing."""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from workflows.runner import _extract_json, WorkflowRunner


# ---------------------------------------------------------------------------
# _extract_json
# ---------------------------------------------------------------------------

class TestExtractJson:
    def test_bare_json(self):
        result = _extract_json('{"score": 8, "approved": true}')
        assert result["score"] == 8
        assert result["approved"] is True

    def test_json_in_code_fence(self):
        text = '```json\n{"score": 9, "issues": []}\n```'
        result = _extract_json(text)
        assert result["score"] == 9

    def test_json_in_plain_code_fence(self):
        text = '```\n{"approved": false, "score": 4}\n```'
        result = _extract_json(text)
        assert result["approved"] is False

    def test_json_with_surrounding_text(self):
        text = "Here is my review:\n```json\n{\"score\": 7}\n```\nEnd of review."
        result = _extract_json(text)
        assert result["score"] == 7

    def test_invalid_json_returns_empty_dict(self):
        result = _extract_json("This is not JSON at all.")
        assert result == {}

    def test_malformed_json_returns_empty_dict(self):
        result = _extract_json('{"score": }')
        assert result == {}

    def test_empty_string_returns_empty_dict(self):
        result = _extract_json("")
        assert result == {}


# ---------------------------------------------------------------------------
# WorkflowRunner — loading and step execution (fully mocked providers)
# ---------------------------------------------------------------------------

@pytest.fixture
def workflow_dir(tmp_path):
    """Create a minimal project workspace with one workflow."""
    project_dir = tmp_path / "workspace" / "testproject"
    wf_dir = project_dir / "workflows" / "simple"
    wf_dir.mkdir(parents=True)

    # project.yaml
    (project_dir / "project.yaml").write_text(
        "name: testproject\ncode_dir: ../../code\n"
    )

    # workflow.yaml — single step, no git actions
    wf_yaml = {
        "name": "simple",
        "description": "A simple test workflow",
        "steps": [
            {
                "name": "generate",
                "provider": "claude",
                "prompt": "prompts/step1.md",
            }
        ],
    }
    import yaml
    (wf_dir / "workflow.yaml").write_text(yaml.dump(wf_yaml))
    (wf_dir / "prompts").mkdir()
    (wf_dir / "prompts" / "step1.md").write_text("Generate something useful.")

    return tmp_path, project_dir, wf_dir


@pytest.fixture
def mock_claude_agent():
    agent = MagicMock()
    agent.send.return_value = "Claude output here"
    agent.max_retries = 3
    agent.count_tokens.return_value = 100
    agent.model = "claude-sonnet-4-6"
    return agent


class TestWorkflowRunnerLoad:
    def test_raises_when_workflow_not_found(self, workflow_dir, mock_claude_agent):
        tmp_path, project_dir, _ = workflow_dir
        config = {"providers": {}}
        runner = WorkflowRunner(config=config, workspace_root=tmp_path / "workspace", project_name="testproject")

        with pytest.raises(FileNotFoundError):
            runner.run("nonexistent_workflow", "input")

    def test_list_workflows(self, workflow_dir):
        tmp_path, project_dir, _ = workflow_dir
        config = {"providers": {}}
        runner = WorkflowRunner(config=config, workspace_root=tmp_path / "workspace", project_name="testproject")
        wfs = runner.list_workflows()
        assert "simple" in wfs

    def test_list_workflows_empty_when_no_project(self, tmp_path):
        config = {"providers": {}}
        runner = WorkflowRunner(config=config, workspace_root=tmp_path / "workspace", project_name="ghost")
        assert runner.list_workflows() == []


class TestWorkflowRunnerExecution:
    def test_single_step_runs_and_returns_output(self, workflow_dir, mock_claude_agent):
        tmp_path, project_dir, _ = workflow_dir
        config = {"providers": {"claude": {"model": "claude-sonnet-4-6"}}}
        runner = WorkflowRunner(config=config, workspace_root=tmp_path / "workspace", project_name="testproject")

        with patch("workflows.runner._make_provider", return_value=mock_claude_agent):
            result = runner.run("simple", "my input")

        assert result == "Claude output here"
        mock_claude_agent.send.assert_called_once()

    def test_run_log_saved(self, workflow_dir, mock_claude_agent):
        tmp_path, project_dir, _ = workflow_dir
        config = {"providers": {"claude": {"model": "claude-sonnet-4-6"}}}
        runner = WorkflowRunner(config=config, workspace_root=tmp_path / "workspace", project_name="testproject")

        with patch("workflows.runner._make_provider", return_value=mock_claude_agent):
            runner.run("simple", "test input")

        runs_dir = project_dir / "runs"
        run_files = list(runs_dir.glob("*.json"))
        assert len(run_files) == 1

        log = json.loads(run_files[0].read_text())
        assert log["workflow"] == "simple"
        assert "steps" in log
        assert log["final_output_preview"] == "Claude output here"


class TestWorkflowStopCondition:
    def test_stop_condition_met_breaks_loop(self, tmp_path):
        """Workflow with score stop_condition should stop when score >= threshold."""
        project_dir = tmp_path / "workspace" / "proj"
        wf_dir = project_dir / "workflows" / "scored"
        wf_dir.mkdir(parents=True)
        (project_dir / "project.yaml").write_text("name: proj\n")
        (wf_dir / "prompts").mkdir()
        (wf_dir / "prompts" / "review.md").write_text("Review this.")

        import yaml
        wf_yaml = {
            "name": "scored",
            "steps": [
                {
                    "name": "implement",
                    "provider": "deepseek",
                    "prompt": "prompts/review.md",
                    "output_format": "json",
                    "produces": {"score": "int", "approved": "bool"},
                }
            ],
            "stop_condition": {"field": "score", "threshold": 8},
            "max_iterations": 3,
        }
        (wf_dir / "workflow.yaml").write_text(yaml.dump(wf_yaml))

        # Mock provider returns JSON with score=9 → should stop immediately
        mock_provider = MagicMock()
        mock_provider.stream.return_value = iter(['{"score": 9, "approved": true}'])
        mock_provider.count_tokens.return_value = 100
        mock_provider.model = "deepseek-chat"
        mock_provider.max_retries = 3

        config = {"providers": {"deepseek": {"model": "deepseek-chat"}}}
        runner = WorkflowRunner(config=config, workspace_root=tmp_path / "workspace", project_name="proj")

        with patch("workflows.runner._make_provider", return_value=mock_provider):
            result = runner.run("scored", "input")

        # Provider called exactly once (stop condition met on first call)
        assert mock_provider.stream.call_count == 1
