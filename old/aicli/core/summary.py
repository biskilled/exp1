"""
Project summary helpers.
build_project_summary  — fast local summary from conversation history.
generate_system_summary — richer AI-generated summary using OpenAI.
"""


def build_project_summary(conversation: list[dict], limit: int = 20) -> str:
    """Build a quick text summary from recent conversation entries."""
    lines = []
    for item in conversation[-limit:]:
        provider = item.get("provider", "?")
        feature = item.get("feature") or ""
        tag = item.get("tag") or ""
        prompt = item.get("user_input", "")[:80]
        meta = " ".join(filter(None, [feature, tag]))
        line = f"[{provider}]{f' ({meta})' if meta else ''} {prompt}"
        lines.append(line)
    return "\n".join(lines)


def generate_system_summary(openai_agent, commits: list[dict]) -> str:
    """Generate an AI system overview from commit history."""
    if not commits:
        return ""

    commit_text = "\n".join(
        f"- {c.get('commit_message', '')}" for c in commits if c.get("commit_message")
    )

    prompt = (
        "Summarize the current system state based on these commits:\n\n"
        f"{commit_text}\n\n"
        "Provide:\n"
        "- Main features implemented\n"
        "- Architecture overview\n"
        "- Key components\n"
        "- Recent changes"
    )

    # send() returns a plain string
    return openai_agent.send(
        system_prompt="You summarize software systems concisely.",
        user_prompt=prompt,
    )
