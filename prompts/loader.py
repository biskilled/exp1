"""
Prompt loader — assembles CLAUDE.md and OPENAI.md from modular template files.
"""

import os
from pathlib import Path


PLACEHOLDER_MAP = {
    "claude": {
        "{{AI_SYSTEM}}": "system.md",
        "{{UI_ARCHITECT}}": "ui-architect.md",
        "{{COMPONENT_BUILDER}}": "component-builder.md",
        "{{FLOW_BUILDER}}": "flow-builder.md",
        "{{qa}}": "qa.md",
    },
    "openai": {
        "{{SYSTEM}}": "system.md",
        "{{REVIEWER}}": "reviewer.md",
        "{{COMMIT_WRITER}}": "commit-writer.md",
        "{{OPTIMIZER}}": "optimizer.md",
    },
}


def _load_file(path: str | Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def build_md(module_name: str, provider_name: str, output_file: Path):
    """
    Assemble the provider's prompt file from modular pieces and write it to output_file.

    Args:
        module_name:   e.g. "ui"
        provider_name: "claude" or "openai"
        output_file:   full Path where the assembled file should be written
    """
    prompts_dir = Path(__file__).parent
    ai_dir = prompts_dir / module_name / f"sys_{provider_name}"

    if not ai_dir.is_dir():
        print(f"[loader] No sys_{provider_name} directory found: {ai_dir}")
        return

    template_path = ai_dir / f"template.{provider_name}.md"
    if not template_path.exists():
        print(f"[loader] Template not found: {template_path}")
        return

    placeholders = PLACEHOLDER_MAP.get(provider_name, {})
    template = _load_file(template_path)

    for placeholder, filename in placeholders.items():
        file_path = ai_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Missing prompt file: {file_path}")
        content = _load_file(file_path)
        template = template.replace(placeholder, content)

    # Ensure output directory exists
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_file.write_text(template, encoding="utf-8")
    print(f"[loader] Built {output_file}")


def load_openai_role(prompts_root: Path, module: str, role_name: str) -> str:
    """Load an OpenAI role prompt file."""
    path = prompts_root / module / "sys_openai" / f"{role_name}.md"
    if not path.exists():
        raise ValueError(f"OpenAI role '{role_name}' not found at {path}")
    return path.read_text(encoding="utf-8")


def load_openai_system(prompts_root: Path, module: str) -> str:
    """Load the OpenAI system prompt."""
    path = prompts_root / module / "sys_openai" / "system.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
