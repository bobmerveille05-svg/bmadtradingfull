from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from bmadts.models.session import SessionState


@dataclass(frozen=True)
class HelpEntry:
    module: str
    phase: str
    name: str
    code: str
    sequence: int
    command: str
    required: bool
    description: str


def load_help_entries(csv_path: Path) -> list[HelpEntry]:
    entries: list[HelpEntry] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row:
                continue
            entries.append(
                HelpEntry(
                    module=(row.get("module") or "").strip(),
                    phase=(row.get("phase") or "").strip(),
                    name=(row.get("name") or "").strip(),
                    code=(row.get("code") or "").strip(),
                    sequence=int((row.get("sequence") or "0").strip() or "0"),
                    command=(row.get("command") or "").strip(),
                    required=_parse_bool(row.get("required") or "false"),
                    description=(row.get("description") or "").strip(),
                )
            )

    entries.sort(key=lambda e: (e.phase, e.sequence, e.name))
    return entries


def render_bmad_help(*, workdir: Path, state: SessionState) -> str:
    csv_path = workdir / "_bmad" / "bts" / "module-help.csv"
    if not csv_path.exists():
        return "BMAD help data not found: _bmad/bts/module-help.csv"

    entries = load_help_entries(csv_path)
    phase = state.current_phase.value

    applicable = [e for e in entries if e.phase in {"anytime", phase}]
    required = [e for e in applicable if e.required]
    optional = [e for e in applicable if not e.required]

    def fmt(e: HelpEntry) -> str:
        req = "(required)" if e.required else ""
        desc = f" - {e.description}" if e.description else ""
        return f"- {e.command} {req}{desc}".rstrip()

    lines: list[str] = [
        "BMAD Help (BTS)",
        f"- phase: {phase}",
        f"- gate: {state.current_gate} ({state.gate_status.value})",
        f"- active_agent: {state.active_agent.value if state.active_agent else '-'}",
        "",
        "Recommended:",
    ]

    if required:
        for e in sorted(required, key=lambda x: x.sequence):
            lines.append(fmt(e))
    else:
        lines.append("- (no required commands for this phase)")

    if optional:
        lines.append("")
        lines.append("Optional:")
        for e in sorted(optional, key=lambda x: x.sequence):
            lines.append(fmt(e))

    return "\n".join(lines).rstrip()


def _parse_bool(v: str) -> bool:
    v = v.strip().lower()
    return v in {"1", "true", "yes", "y"}
