"""
Claude provider using the Anthropic Python SDK.

Why API instead of CLI subprocess:
- The `claude` CLI requires a TTY for interactive use; piped stdin hangs.
- The API gives full control: system prompt, tool use, history, streaming.
- Replicated CLI advantages:
    • CLAUDE.md → passed as `system` prompt
    • Conversation history → self.messages maintained per session
    • Tool use → bash + file tools defined below (same as CLI built-ins)
    • Cross-session memory → MemoryStore (JSONL, no ML deps)
"""

import os
import json
import subprocess
from pathlib import Path

import anthropic


# ---------------------------------------------------------------------------
# Built-in tools (replicates what the Claude CLI provides natively)
# ---------------------------------------------------------------------------

BUILTIN_TOOLS = [
    {
        "name": "bash",
        "description": (
            "Run a shell command and return stdout+stderr. "
            "Use for reading files, running tests, git operations, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to run"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file at the given path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file (creates or overwrites).",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_directory",
        "description": "List files and directories at a given path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (default: current dir)"},
            },
            "required": [],
        },
    },
]


def _run_tool(name: str, tool_input: dict) -> str:
    """Execute a built-in tool and return its string result."""
    try:
        if name == "bash":
            cmd = tool_input["command"]
            timeout = tool_input.get("timeout", 30)
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            return output or "(no output)"

        elif name == "read_file":
            path = Path(tool_input["path"])
            if not path.exists():
                return f"Error: file not found: {path}"
            return path.read_text(encoding="utf-8", errors="replace")

        elif name == "write_file":
            path = Path(tool_input["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(tool_input["content"], encoding="utf-8")
            return f"Written {len(tool_input['content'])} chars to {path}"

        elif name == "list_directory":
            p = Path(tool_input.get("path", "."))
            if not p.exists():
                return f"Error: path not found: {p}"
            entries = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name))
            lines = [
                f"{'D' if e.is_dir() else 'F'}  {e.name}"
                for e in entries
            ]
            return "\n".join(lines) or "(empty directory)"

        else:
            return f"Unknown tool: {name}"

    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {tool_input.get('timeout', 30)}s"
    except Exception as e:
        return f"Error running {name}: {e}"


# ---------------------------------------------------------------------------
# ClaudeAgent
# ---------------------------------------------------------------------------

class ClaudeAgent:

    def __init__(self, config: dict, logger=None):
        self.logger = logger
        claude_cfg = config.get("providers", {}).get("claude", {})
        self.model = claude_cfg.get("model", "claude-sonnet-4-6")

        api_key = os.getenv(claude_cfg.get("api_key_env", "ANTHROPIC_API_KEY"))
        self.client = anthropic.Anthropic(api_key=api_key)

        # Full conversation history — maintained across turns within a session
        self.messages: list[dict] = []

        # System prompt from CLAUDE.md (loaded from cwd)
        self.system_prompt = self._load_system_prompt()

        # Whether to expose built-in tools (bash, file ops)
        self.tools_enabled = claude_cfg.get("tools_enabled", True)

        # Optional remote MCP servers
        self.mcp_servers = self._build_mcp_servers(config.get("mcp", {}))

        if self.logger:
            self.logger.info(
                "claude_initialized",
                model=self.model,
                tools=self.tools_enabled,
                mcp_servers=len(self.mcp_servers),
                has_system_prompt=bool(self.system_prompt),
            )

    # ------------------------------------------------------------------

    def _load_system_prompt(self) -> str:
        claude_md = Path("CLAUDE.md")
        if claude_md.exists():
            return claude_md.read_text(encoding="utf-8")
        return ""

    def reload_system_prompt(self):
        self.system_prompt = self._load_system_prompt()

    # ------------------------------------------------------------------

    def _build_mcp_servers(self, mcp_config: dict) -> list[dict]:
        servers = []
        for server in mcp_config.get("servers", []):
            stype = server.get("type")
            if stype == "github":
                token = os.getenv(server.get("token_env", "GITHUB_TOKEN"), "")
                if token:
                    servers.append({
                        "type": "mcp",
                        "server_label": server.get("name", "github"),
                        "server_url": "https://mcp.github.com",
                        "headers": {"Authorization": f"Bearer {token}"},
                    })
            elif stype == "http":
                url = server.get("url", "")
                if url:
                    entry: dict = {
                        "type": "mcp",
                        "server_label": server.get("name", "mcp"),
                        "server_url": url,
                    }
                    token_env = server.get("token_env")
                    if token_env:
                        t = os.getenv(token_env, "")
                        if t:
                            entry["headers"] = {"Authorization": f"Bearer {t}"}
                    servers.append(entry)
        return servers

    # ------------------------------------------------------------------
    # Core send — handles tool-use loop automatically
    # ------------------------------------------------------------------

    def send(self, message: str) -> str:
        """
        Send a message and stream the response to stdout in real time.
        Handles the full agentic tool-use loop automatically.
        Returns the complete final text for logging/memory.
        """
        if self.logger:
            self.logger.info("claude_request", length=len(message))

        self.messages.append({"role": "user", "content": message})

        tools = BUILTIN_TOOLS if self.tools_enabled else []
        all_tools = tools + self.mcp_servers if self.mcp_servers else tools

        final_text = ""

        # Agentic loop — Claude may call tools several times before finishing
        while True:
            kwargs: dict = {
                "model": self.model,
                "max_tokens": 8192,
                "messages": self.messages,
            }
            if self.system_prompt:
                kwargs["system"] = self.system_prompt
            if all_tools:
                kwargs["tools"] = all_tools

            try:
                if self.mcp_servers:
                    # MCP beta — no streaming context manager available yet
                    kwargs["betas"] = ["mcp-client-2025-04-04"]
                    response = self.client.beta.messages.create(**kwargs)
                    # Print full text at once for MCP responses
                    for block in response.content:
                        if hasattr(block, "text"):
                            print(block.text, end="", flush=True)
                    print()  # final newline
                else:
                    # Stream text tokens as they arrive
                    with self.client.messages.stream(**kwargs) as stream:
                        for chunk in stream.text_stream:
                            print(chunk, end="", flush=True)
                        print()  # final newline
                        response = stream.get_final_message()

            except anthropic.APIError as e:
                if self.logger:
                    self.logger.error("claude_api_error", error=str(e))
                raise

            # Collect text and tool-use blocks from the completed response
            text_parts: list[str] = []
            tool_calls: list = []

            for block in response.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    tool_calls.append(block)

            turn_text = "".join(text_parts)
            if turn_text:
                final_text = turn_text

            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use" or not tool_calls:
                break

            # Execute tools and feed results back for the next turn
            tool_results = []
            for tc in tool_calls:
                print(f"\n  \033[2m[tool:{tc.name}]\033[0m {json.dumps(tc.input)[:120]}")
                result_text = _run_tool(tc.name, tc.input)
                preview = result_text[:300].replace("\n", " ")
                print(f"  \033[2m→ {preview}\033[0m\n")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result_text,
                })

            self.messages.append({"role": "user", "content": tool_results})

        if self.logger:
            self.logger.info("claude_response", length=len(final_text))

        return final_text

    # ------------------------------------------------------------------

    def clear_history(self):
        self.messages = []

    def close(self):
        pass  # SDK client needs no cleanup
