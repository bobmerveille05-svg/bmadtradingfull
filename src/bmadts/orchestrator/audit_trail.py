from __future__ import annotations

from pathlib import Path
from typing import Any

from bmadts._time import utcnow


class AuditTrail:
    def __init__(self, file_path: Path):
        self._file_path = file_path
        if not file_path.exists():
            file_path.write_text("# AUDIT-TRAIL\n\n", encoding="utf-8")

    @property
    def file_path(self) -> Path:
        return self._file_path

    def record(
        self, entry_type: str, description: str, details: dict[str, Any] | None = None
    ) -> None:
        ts = utcnow().isoformat()
        lines: list[str] = [f"## {ts} - {entry_type}", "", description, ""]
        if details:
            lines.append("Details:")
            for k in sorted(details.keys()):
                v = details[k]
                lines.append(f"- {k}: {v}")
            lines.append("")

        with self._file_path.open("a", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
