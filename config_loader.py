# config_loader.py
import yaml
from pydantic import BaseModel
from typing import Dict, List, Any


class ProviderConfig(BaseModel):
    type: str
    command: str | None = None
    model: str | None = None
    api_key_env: str | None = None


class GitConfig(BaseModel):
    auto_push: bool = True
    require_confirmation: bool = True
    branch_prefix: str | None = None
    block_main: bool = True


class WorkflowStep(BaseModel):
    provider: str
    role: str
    prompt: str


class Workflow(BaseModel):
    description: str
    steps: List[WorkflowStep]


class AppConfig(BaseModel):
    providers: Dict[str, Any]
    git: GitConfig
    workflows: Dict[str, Workflow]


def load_config(path="aicli.yaml") -> AppConfig:
    with open(path) as f:
        data = yaml.safe_load(f)
    return AppConfig(**data)