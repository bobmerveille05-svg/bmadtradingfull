from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bmadts.models.enums import AgentType, ArtifactType


@dataclass(frozen=True)
class AgentContext:
    workdir: Path
    language: str
    input_artifacts: dict[ArtifactType, str]


class BaseAgent:
    agent_type: AgentType
    output_artifact_type: ArtifactType

    def __init__(self, context: AgentContext):
        self._context = context

    @property
    def context(self) -> AgentContext:
        return self._context

    def get_system_prompt(self) -> str:
        raise NotImplementedError

    def execute(self) -> str:
        """Return artifact content as string."""

        raise NotImplementedError
