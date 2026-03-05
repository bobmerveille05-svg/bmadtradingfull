from __future__ import annotations

from datetime import datetime
import re
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from bmadts._time import utcnow
from bmadts.models.enums import AgentType, ArtifactType, GateStatus, Phase


class ArtifactRef(BaseModel):
    artifact_type: ArtifactType
    file_path: str
    version: str
    created_at: datetime = Field(default_factory=utcnow)

    @classmethod
    def _version_re(cls) -> re.Pattern[str]:
        return re.compile(r"^v\d+\.\d+$")

    @field_validator("version")
    @classmethod
    def _validate_version(cls, v: str) -> str:
        v = v.strip()
        if not cls._version_re().match(v):
            raise ValueError("version must match v<major>.<minor> (e.g. v1.0)")
        return v


class SessionState(BaseModel):
    session_id: UUID = Field(default_factory=uuid4)
    current_phase: Phase = Phase.IDLE
    current_gate: int = 0
    gate_status: GateStatus = GateStatus.PENDING
    active_agent: AgentType | None = None
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    language: str = "en"

    def touch(self) -> "SessionState":
        return self.model_copy(update={"updated_at": utcnow()})
