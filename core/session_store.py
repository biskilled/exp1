"""
SessionStore — persists provider conversation history and session handoff state.

Why this matters:
  Without persistence, every new aicli session starts cold. With it:
  - Claude continues from where it left off
  - DeepSeek / OpenAI / Grok carry full conversation history forward
  - Gemini resumes its chat session
  - Any LLM picking up mid-project sees what was last worked on

Files written:
  .aicli/sessions/<provider>_messages.json  ← per-provider message history
  .aicli/session_state.json                 ← "sticky note" for cross-LLM handoff
"""

import json
from datetime import datetime, timezone
from pathlib import Path

# Cap stored messages per provider to avoid unbounded growth.
# At ~1KB/message, 200 messages = ~200KB — negligible.
MAX_STORED_MESSAGES = 200


class SessionStore:
    """Saves and loads provider message histories across sessions."""

    def __init__(self, working_dir: Path):
        self.dir = working_dir / ".aicli" / "sessions"
        self.dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------

    def load_messages(self, provider: str) -> list[dict]:
        """Load saved messages for a provider. Returns [] if none saved."""
        path = self.dir / f"{provider}_messages.json"
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            messages = data.get("messages", [])
            # Basic validation: each entry must have role + content/parts
            return [
                m for m in messages
                if isinstance(m, dict) and "role" in m
            ]
        except Exception:
            return []

    def save_messages(self, provider: str, messages: list[dict]) -> None:
        """Persist provider messages. Trims to MAX_STORED_MESSAGES."""
        if not messages:
            return
        trimmed = messages[-MAX_STORED_MESSAGES:]
        path = self.dir / f"{provider}_messages.json"
        path.write_text(
            json.dumps(
                {
                    "provider": provider,
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                    "message_count": len(trimmed),
                    "messages": trimmed,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def clear(self, provider: str | None = None) -> None:
        """Delete saved messages for one provider or all providers."""
        if provider:
            (self.dir / f"{provider}_messages.json").unlink(missing_ok=True)
        else:
            for f in self.dir.glob("*_messages.json"):
                f.unlink()

    def providers_with_history(self) -> list[str]:
        """Return provider names that have saved history."""
        return [f.stem.replace("_messages", "") for f in sorted(self.dir.glob("*_messages.json"))]


# ------------------------------------------------------------------
# session_state.json — the "sticky note" for cross-LLM handoff
# ------------------------------------------------------------------

def load_session_state(working_dir: Path) -> dict:
    """
    Load the last session's state. Returns {} if no previous session.

    Used to inject a [PREVIOUS SESSION] block into the first prompt of a
    new session so any provider immediately knows what was last worked on.
    """
    path = working_dir / ".aicli" / "session_state.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_session_state(
    working_dir: Path,
    provider: str,
    project: str,
    feature: str,
    tag: str,
    last_input: str,
    last_output: str,
    session_count: int = 0,
) -> None:
    """
    Update session_state.json after each turn.

    This file is the handoff document when switching between LLMs:
      - LLM-A finishes work → saves state
      - User restarts, switches to LLM-B → B reads this and picks up
    """
    state = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "active_provider": provider,
        "active_project": project or "",
        "feature": feature or "",
        "tag": tag or "",
        "last_input_preview": last_input[:250],
        "last_output_preview": last_output[:400],
        "session_count": session_count,
    }
    path = working_dir / ".aicli" / "session_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def format_session_state_for_prompt(state: dict) -> str:
    """
    Format session_state.json into a [PREVIOUS SESSION] block for LLM injection.

    All providers receive this at the start of their context so they understand
    where work stands, regardless of which LLM ran the last session.
    """
    if not state:
        return ""

    ts = state.get("last_updated", "")[:10]  # YYYY-MM-DD
    lines = [
        f"[PREVIOUS SESSION — {ts}]",
        f"Provider: {state.get('active_provider', '?')}  "
        f"Project: {state.get('active_project', '?')}",
    ]
    if state.get("feature"):
        lines.append(f"Feature in progress: {state['feature']}")
    if state.get("tag"):
        lines.append(f"Tag: #{state['tag']}")

    last_q = state.get("last_input_preview", "").strip()
    last_a = state.get("last_output_preview", "").strip()
    if last_q:
        lines.append(f"Last question: {last_q}")
    if last_a:
        lines.append(f"Last answer: {last_a}")

    count = state.get("session_count", 0)
    if count:
        lines.append(f"(session #{count})")

    return "\n".join(lines)
