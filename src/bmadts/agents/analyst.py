from __future__ import annotations

from bmadts.agents.base_agent import AgentContext, BaseAgent
from bmadts.models.enums import AgentType, ArtifactType


class AnalystAgent(BaseAgent):
    agent_type = AgentType.ANALYST
    output_artifact_type = ArtifactType.STRATEGY_SPEC

    def __init__(self, context: AgentContext):
        super().__init__(context)

    def get_system_prompt(self) -> str:
        return (
            "You are the BMAD ANALYST agent. Your job is to collect a complete "
            "strategy questionnaire and produce STRATEGY-SPEC.md with unique Rule_IDs."
        )

    def execute(self) -> str:
        raise NotImplementedError(
            "Interactive questionnaire and STRATEGY-SPEC generation not wired yet."
        )
