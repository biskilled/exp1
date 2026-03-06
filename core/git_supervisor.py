"""
Git supervisor — detects changes, generates commit messages via OpenAI,
and runs automated commit + push after each AI response.
Fires post_commit and post_push hooks after each successful operation.
"""

import subprocess


class GitSupervisor:

    DEFAULT_IGNORED = [
        ".aicli/",
        "CLAUDE.md",
        "OPENAI.md",
        "prompts/",
        "aicli.yaml",
    ]

    def __init__(self, config: dict, logger=None, hook_runner=None):
        self.config = config
        self.logger = logger
        self.hook_runner = hook_runner
        self.ignored_paths = config.get("ignored_paths", self.DEFAULT_IGNORED)

    # ------------------------------------------------------------------
    # Change detection
    # ------------------------------------------------------------------

    def get_change_stats(self) -> str:
        result = subprocess.run(
            ["git", "diff", "--shortstat"],
            capture_output=True, text=True,
        )
        return result.stdout.strip()

    def get_changed_files(self) -> list[str]:
        staged = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True, text=True,
        ).stdout.strip().splitlines()

        unstaged = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True, text=True,
        ).stdout.strip().splitlines()

        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True, text=True,
        ).stdout.strip().splitlines()

        all_files = list(dict.fromkeys(staged + unstaged + untracked))  # dedup, preserve order
        return self._filter_files(all_files)

    def _filter_files(self, files: list[str]) -> list[str]:
        return [
            f for f in files
            if f and not any(f.startswith(p) for p in self.ignored_paths)
        ]

    def get_current_branch(self) -> str:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True,
        )
        return result.stdout.strip()

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def run_tests(self) -> bool:
        if not self.config.get("run_tests"):
            return True
        test_command = self.config.get("test_command", "pytest")
        print("Running tests...")
        result = subprocess.run(test_command, shell=True)
        if result.returncode != 0:
            print("Tests failed — commit aborted.")
            return False
        return True

    # ------------------------------------------------------------------
    # Commit handler
    # ------------------------------------------------------------------

    def handle_commit(
        self,
        llm_output: str,
        openai_agent,
        context: dict | None = None,
    ) -> dict | None:
        """
        If there are changed files: generate a commit message, stage, commit, push.
        Fires post_commit and post_push hooks with full context.
        Returns commit metadata dict or None.
        """
        changed_files = self.get_changed_files()
        if not changed_files:
            return None

        stats = self.get_change_stats()

        if self.logger:
            self.logger.info("git_changes", files=changed_files, stats=stats)

        print(f"\nChanges: {stats}  ({len(changed_files)} files)")

        # Guard against huge accidental changes
        threshold = self.config.get("large_change_file_threshold", 20)
        if len(changed_files) > threshold:
            confirm = input(f"Large change ({len(changed_files)} files) — commit? (y/n): ")
            if confirm.lower() != "y":
                print("Commit aborted.")
                return None

        if not self.run_tests():
            return None

        # Generate commit message
        commit_message = openai_agent.send(
            system_prompt="You write professional git commit messages.",
            user_prompt=(
                "Summarize into a professional git commit message.\n"
                "Be concise, under 100 words, no hallucination.\n\n"
                f"OUTPUT:\n{llm_output[:3000]}"
            ),
        )

        if not commit_message or len(commit_message.strip()) < 5:
            print("Could not generate commit message — aborting.")
            return None

        commit_message = commit_message.strip()

        # Stage and commit
        subprocess.run(["git", "add", "--"] + changed_files, check=False)

        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True, text=True,
        )

        if commit_result.returncode != 0:
            print(f"Git commit failed:\n{commit_result.stderr}")
            return None

        commit_hash = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True,
        ).stdout.strip()

        branch = self.get_current_branch()

        print(f"Committed {commit_hash[:8]}: {commit_message[:60]}")

        if self.logger:
            self.logger.info("commit_ok", hash=commit_hash[:8], message=commit_message[:80])

        commit_data = {
            "hash": commit_hash,
            "message": commit_message,
            "files": changed_files,
            "stats": stats,
            "branch": branch,
        }

        # Post-commit hook
        if self.hook_runner:
            hook_ctx = {
                **(context or {}),
                "commit_hash": commit_hash,
                "commit_message": commit_message,
                "files_changed": " ".join(changed_files),
                "branch": branch,
            }
            self.hook_runner.run("post_commit", hook_ctx)

        # Push
        git_cfg = self.config.get("git", {})
        if git_cfg.get("auto_push", True):
            push_result = subprocess.run(
                ["git", "push"],
                capture_output=True, text=True,
            )
            if push_result.returncode == 0:
                print("Pushed.")
                if self.hook_runner:
                    self.hook_runner.run("post_push", {
                        **(context or {}),
                        "commit_hash": commit_hash,
                        "commit_message": commit_message,
                        "files_changed": " ".join(changed_files),
                        "branch": branch,
                    })
            else:
                print(f"Push failed: {push_result.stderr.strip()}")

        return commit_data
