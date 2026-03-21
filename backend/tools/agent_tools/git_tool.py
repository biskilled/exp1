"""
git_tool.py — Agent-callable git tools.

Provides tool definitions (Claude tool_use format) and handlers
that delegate to gitops/git.py.
"""
from __future__ import annotations

import subprocess
from pathlib import Path


# ── Tool definitions (Claude tool_use JSON schema format) ─────────────────────

GIT_TOOL_DEFS: list[dict] = [
    {
        "name": "git_status",
        "description": "Show the working tree status (staged, unstaged, untracked files).",
        "input_schema": {
            "type": "object",
            "properties": {
                "cwd": {"type": "string", "description": "Directory to run git in (default: code_dir)"},
            },
        },
    },
    {
        "name": "git_diff",
        "description": "Show unstaged (or staged) diff of the working tree.",
        "input_schema": {
            "type": "object",
            "properties": {
                "staged": {"type": "boolean", "description": "Show staged diff instead of unstaged"},
                "cwd": {"type": "string", "description": "Directory to run git in"},
            },
        },
    },
    {
        "name": "git_commit",
        "description": "Stage all changes and create a git commit.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Commit message"},
                "cwd": {"type": "string", "description": "Directory to run git in"},
            },
            "required": ["message"],
        },
    },
    {
        "name": "git_push",
        "description": "Push committed changes to the remote repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cwd": {"type": "string", "description": "Directory to run git in"},
            },
        },
    },
]


# ── Handlers ──────────────────────────────────────────────────────────────────

def _run(cmd: list[str], cwd: str) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=30)
    return (result.stdout + result.stderr).strip()


def _default_cwd() -> str:
    from core.config import settings
    return settings.code_dir


def handle_git_status(args: dict) -> str:
    cwd = args.get("cwd") or _default_cwd()
    return _run(["git", "status", "--short"], cwd)


def handle_git_diff(args: dict) -> str:
    cwd = args.get("cwd") or _default_cwd()
    cmd = ["git", "diff", "--cached"] if args.get("staged") else ["git", "diff"]
    return _run(cmd, cwd)


def handle_git_commit(args: dict) -> str:
    cwd = args.get("cwd") or _default_cwd()
    msg = args["message"]
    _run(["git", "add", "."], cwd)
    return _run(["git", "commit", "-m", msg], cwd)


def handle_git_push(args: dict) -> str:
    cwd = args.get("cwd") or _default_cwd()
    return _run(["git", "push"], cwd)


GIT_HANDLERS: dict = {
    "git_status": handle_git_status,
    "git_diff": handle_git_diff,
    "git_commit": handle_git_commit,
    "git_push": handle_git_push,
}
