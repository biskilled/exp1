"""
agent_tools — Registry of callable tools for the Agent agentic loop.

AGENT_TOOLS maps tool name → {"definition": dict, "handler": callable, "category": str}
invoke_tool(name, args) dispatches a tool call and returns a string result.

Tool modules:
  tool_git       — git_status, git_diff, git_commit, git_push
  tool_file      — read_file, write_file, list_dir
  tool_memory    — search_memory, get_recent_history, get_project_facts,
                   get_tag_context, search_features
"""
from __future__ import annotations

from agents.tools.tool_git import GIT_TOOL_DEFS, GIT_HANDLERS
from agents.tools.tool_file import FILE_TOOL_DEFS, FILE_HANDLERS
from agents.tools.tool_memory import MEMORY_TOOL_DEFS, MEMORY_HANDLERS

# Category assignments per tool name
_TOOL_CATEGORIES: dict[str, str] = {
    "git_status":         "git",
    "git_diff":           "git",
    "git_commit":         "git",
    "git_push":           "git",
    "read_file":          "files",
    "write_file":         "files",
    "list_dir":           "files",
    "search_memory":      "memory",
    "get_recent_history": "memory",
    "get_project_facts":  "memory",
    "get_tag_context":    "memory",
    "search_features":    "memory",
}

# Master registry: name → {definition, handler, category}
AGENT_TOOLS: dict[str, dict] = {}

_all_handlers: dict = {**GIT_HANDLERS, **FILE_HANDLERS, **MEMORY_HANDLERS}

for _def in GIT_TOOL_DEFS + FILE_TOOL_DEFS + MEMORY_TOOL_DEFS:
    _name = _def["name"]
    _handler = _all_handlers.get(_name)
    if _handler:
        AGENT_TOOLS[_name] = {
            "definition": _def,
            "handler":    _handler,
            "category":   _TOOL_CATEGORIES.get(_name, "other"),
        }

ALL_TOOL_DEFS: list[dict] = [v["definition"] for v in AGENT_TOOLS.values()]


def invoke_tool(name: str, args: dict) -> str:
    """Invoke a registered agent tool by name. Returns string output."""
    entry = AGENT_TOOLS.get(name)
    if not entry:
        return f"Error: unknown tool '{name}'"
    try:
        return str(entry["handler"](args))
    except Exception as e:
        return f"Error calling {name}: {e}"
