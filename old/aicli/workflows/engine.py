"""
Workflow engine — runs multi-step AI workflows defined in aicli.yaml.
Steps can alternate between Claude and OpenAI with context passing between them.
"""


class WorkflowEngine:

    def __init__(self, claude_agent, openai_agent, conversation, git_supervisor=None):
        self.claude = claude_agent
        self.openai = openai_agent
        self.conversation = conversation
        self.git_supervisor = git_supervisor

    def run(self, workflow_definition: dict, initial_prompt: str) -> str:
        """
        Execute all steps in the workflow, threading output between steps.
        Returns the final step's output.
        """
        context_output: str | None = None

        for i, step in enumerate(workflow_definition.get("steps", []), 1):
            provider = step.get("provider", "claude")
            role = step.get("role")

            print(f"\n[Workflow step {i}/{len(workflow_definition['steps'])}] provider={provider} role={role}")

            if provider == "claude":
                prompt = initial_prompt if context_output is None else context_output
                output = self.claude.send(prompt)

            elif provider == "openai":
                system_prompt = step.get("system_prompt", "You are a helpful assistant.")
                role_prompt = step.get("role_prompt", step.get("prompt", ""))
                user_content = f"{role_prompt}\n\n{context_output or initial_prompt}"
                output = self.openai.send(system_prompt, user_content)

            else:
                raise ValueError(f"Unknown provider in workflow: {provider!r}")

            print(output)
            context_output = output

            self.conversation.append(
                provider=provider,
                role=role,
                user_input=initial_prompt,
                output=output,
            )

            if self.git_supervisor:
                commit_data = self.git_supervisor.handle_commit(output, self.openai)
                if commit_data:
                    # Update the last conversation entry with commit info
                    self.conversation.data["conversation"][-1]["commit"] = commit_data
                    self.conversation.save()

        return context_output or ""
