"""
aicli hooks system — run shell scripts at defined lifecycle points.

Hook events (defined in aicli.yaml under `hooks:`):
  pre_prompt   — before the LLM is called
  post_prompt  — after the LLM responds (main use: auto-commit, log)
  post_commit  — after a successful git commit
  post_push    — after a successful git push

Each hook receives context via environment variables:
  AICLI_EVENT          — the event name
  AICLI_PROVIDER       — "claude" or "openai"
  AICLI_ROLE           — openai role name (or empty)
  AICLI_USER_INPUT     — the user's prompt
  AICLI_OUTPUT         — the LLM's response (may be long)
  AICLI_FEATURE        — current feature (or empty)
  AICLI_TAG            — current tag (or empty)
  AICLI_COMMIT_HASH    — git commit hash (post_commit / post_push only)
  AICLI_COMMIT_MESSAGE — commit message (post_commit / post_push only)
  AICLI_FILES_CHANGED  — space-separated list of changed files
  AICLI_BRANCH         — current git branch

Hook scripts can also read JSON from stdin (same data as env vars).
Exit code 0 = success.  Any other exit code logs a warning but does
not stop aicli.
"""

import json
import os
import subprocess
from typing import Any


class HookRunner:

    def __init__(self, config: dict, logger=None):
        self.config = config
        self.logger = logger
        # hooks: {event_name: [ {name, command, providers?, async?}, ... ]}
        self._hooks: dict[str, list[dict]] = config.get("hooks", {})

    # ------------------------------------------------------------------

    def run(self, event: str, context: dict[str, Any]) -> list[dict]:
        """
        Run all hooks registered for `event`.
        Returns a list of result dicts (one per hook).
        Context keys become AICLI_* env vars and are also written to stdin as JSON.
        """
        event_hooks = self._hooks.get(event, [])
        if not event_hooks:
            return []

        results = []
        for hook in event_hooks:
            result = self._run_one(event, hook, context)
            results.append(result)
        return results

    # ------------------------------------------------------------------

    def _run_one(self, event: str, hook: dict, context: dict) -> dict:
        name = hook.get("name", hook.get("command", "?"))
        command = hook.get("command", "").strip()

        if not command:
            return {"name": name, "skipped": True, "reason": "no command"}

        # Provider filter: only run for specified providers
        allowed_providers = hook.get("providers")
        if allowed_providers and context.get("provider") not in allowed_providers:
            return {"name": name, "skipped": True, "reason": "provider filter"}

        # Build environment
        env = dict(os.environ)
        env["AICLI_EVENT"] = event
        for key, value in context.items():
            env_key = f"AICLI_{key.upper()}"
            env[env_key] = str(value) if value is not None else ""

        # JSON payload for stdin
        stdin_payload = json.dumps({"event": event, **context}, default=str)

        timeout = hook.get("timeout", 60)

        if self.logger:
            self.logger.debug("hook_start", event=event, name=name, command=command[:80])

        try:
            proc = subprocess.run(
                command,
                shell=True,
                input=stdin_payload,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )

            result = {
                "name": name,
                "exit_code": proc.returncode,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
            }

            if proc.returncode != 0:
                if self.logger:
                    self.logger.warning(
                        "hook_failed",
                        event=event,
                        name=name,
                        exit_code=proc.returncode,
                        stderr=proc.stderr[:200],
                    )
                # Print stderr to user so they know the hook had a problem
                if proc.stderr:
                    print(f"  [hook:{name}] {proc.stderr.strip()[:200]}")
            else:
                if self.logger:
                    self.logger.debug("hook_ok", event=event, name=name)
                if proc.stdout:
                    print(f"  [hook:{name}] {proc.stdout.strip()[:200]}")

            return result

        except subprocess.TimeoutExpired:
            if self.logger:
                self.logger.warning("hook_timeout", event=event, name=name, timeout=timeout)
            print(f"  [hook:{name}] timed out after {timeout}s")
            return {"name": name, "exit_code": -1, "error": "timeout"}

        except Exception as e:
            if self.logger:
                self.logger.error("hook_error", event=event, name=name, error=str(e))
            return {"name": name, "exit_code": -1, "error": str(e)}

    # ------------------------------------------------------------------

    def has_hooks(self, event: str) -> bool:
        return bool(self._hooks.get(event))
