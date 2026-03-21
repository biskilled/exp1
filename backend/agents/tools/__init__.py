"""
agent_tools — Registry of callable tools for the Agent agentic loop.

AGENT_TOOLS maps tool name → {"definition": dict, "handler": callable}
invoke_tool(name, args) dispatches a tool call and returns a string result.
"""
from __future__ import annotations

from agents.tools.git_tool import GIT_TOOL_DEFS, GIT_HANDLERS
from agents.tools.file_tool import FILE_TOOL_DEFS, FILE_HANDLERS

# Master registry
AGENT_TOOLS: dict[str, dict] = {}

for _def in GIT_TOOL_DEFS + FILE_TOOL_DEFS:
    _name = _def["name"]
    _handler = {**GIT_HANDLERS, **FILE_HANDLERS}.get(_name)
    if _handler:
        AGENT_TOOLS[_name] = {"definition": _def, "handler": _handler}

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
