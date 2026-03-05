from __future__ import annotations

from datetime import datetime
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from bmadts._time import utcnow
from bmadts.models.enums import ArtifactType


class Artifact(BaseModel):
    artifact_type: ArtifactType
    content: str
    version: str
    created_at: datetime = Field(default_factory=utcnow)
    rule_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def _version_re(cls) -> re.Pattern[str]:
        return re.compile(r"^v\d+\.\d+$")

    @classmethod
    def _rule_id_re(cls) -> re.Pattern[str]:
        return re.compile(r"^R-\d{3}$")

    @field_validator("version")
    @classmethod
    def _validate_version(cls, v: str) -> str:
        v = v.strip()
        if not cls._version_re().match(v):
            raise ValueError("version must match v<major>.<minor> (e.g. v1.0)")
        return v

    @field_validator("rule_ids")
    @classmethod
    def _validate_rule_ids(cls, v: list[str]) -> list[str]:
        if len(set(v)) != len(v):
            raise ValueError("rule_ids must be unique")
        for rule_id in v:
            if not cls._rule_id_re().match(rule_id):
                raise ValueError(f"Invalid Rule_ID: {rule_id}")
        return v
