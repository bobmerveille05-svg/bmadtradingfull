from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from bmadts._time import utcnow
from bmadts.exceptions import FileSystemError
from bmadts.models.artifact import Artifact
from bmadts.models.enums import ArtifactType
from bmadts.artifacts.template_manager import TemplateManager


_VERSION_LINE_RE = re.compile(
    r"^(?://\s*)?(?:\*\*Version:\*\*|Version:)\s*(v\d+\.\d+)\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ArtifactHistoryEntry:
    artifact_type: str
    file_path: str
    version: str
    created_at: str


class ArtifactManager:
    def __init__(self, *, workdir: Path, templates: TemplateManager):
        self._workdir = workdir
        self._templates = templates
        self._history_file = workdir / ".bmad-artifacts.json"

    @property
    def workdir(self) -> Path:
        return self._workdir

    @property
    def history_file(self) -> Path:
        return self._history_file

    @property
    def templates(self) -> TemplateManager:
        return self._templates

    def artifact_path(self, artifact_type: ArtifactType) -> Path:
        return self._workdir / artifact_type.value

    def create_from_template(
        self,
        artifact_type: ArtifactType,
        *,
        template_name: str,
        version: str,
        context: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        rule_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Artifact:
        ts = utcnow() if created_at is None else created_at
        ctx: dict[str, Any] = {
            "version": version,
            "created_at": ts.isoformat(),
        }
        if context:
            ctx.update(context)

        content = self._templates.render(template_name, ctx)
        return Artifact(
            artifact_type=artifact_type,
            content=content,
            version=version,
            created_at=ts,
            rule_ids=[] if rule_ids is None else rule_ids,
            metadata={} if metadata is None else metadata,
        )

    def ensure_skeleton(
        self, artifact_type: ArtifactType, *, template_name: str, version: str
    ) -> Path:
        path = self.artifact_path(artifact_type)
        if path.exists():
            return path

        artifact = self.create_from_template(
            artifact_type,
            template_name=template_name,
            version=version,
        )
        return self.save_artifact(artifact, file_path=path)

    def save_artifact(
        self, artifact: Artifact, *, file_path: Path | None = None
    ) -> Path:
        target = (
            self.artifact_path(artifact.artifact_type)
            if file_path is None
            else file_path
        )

        try:
            if target.exists():
                prev_text = target.read_text(encoding="utf-8")
                prev_version = _extract_version_from_text(prev_text) or "v0.0"
                versioned = _versioned_path(target, prev_version)
                target.replace(versioned)

            target.write_text(artifact.content, encoding="utf-8")
            self._append_history(
                ArtifactHistoryEntry(
                    artifact_type=artifact.artifact_type.value,
                    file_path=str(target),
                    version=artifact.version,
                    created_at=artifact.created_at.isoformat(),
                )
            )
            return target
        except OSError as e:
            raise FileSystemError(str(e)) from e

    def load_text(self, artifact_type: ArtifactType) -> str:
        path = self.artifact_path(artifact_type)
        if not path.exists():
            raise FileSystemError(f"Missing artifact: {path.name}")
        return path.read_text(encoding="utf-8")

    def _append_history(self, entry: ArtifactHistoryEntry) -> None:
        data: list[dict[str, Any]]
        if self._history_file.exists():
            try:
                data = json.loads(self._history_file.read_text(encoding="utf-8"))
                if not isinstance(data, list):
                    data = []
            except Exception:
                data = []
        else:
            data = []

        data.append(asdict(entry))
        self._history_file.write_text(
            json.dumps(data, indent=2) + "\n", encoding="utf-8"
        )


def _extract_version_from_text(text: str) -> str | None:
    for line in text.splitlines():
        m = _VERSION_LINE_RE.match(line.strip())
        if m:
            return m.group(1)
    return None


def _versioned_path(path: Path, version: str) -> Path:
    stem = path.stem
    suffix = path.suffix
    return path.with_name(f"{stem}_{version}{suffix}")
