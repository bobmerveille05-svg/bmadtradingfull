from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
import sys


@dataclass(frozen=True)
class PartyMember:
    name: str
    display_name: str
    title: str
    icon: str
    role: str
    identity: str
    communication_style: str
    principles: str


def load_party_members(csv_path: Path) -> list[PartyMember]:
    members: list[PartyMember] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row:
                continue
            members.append(
                PartyMember(
                    name=(row.get("name") or "").strip(),
                    display_name=(row.get("displayName") or "").strip(),
                    title=(row.get("title") or "").strip(),
                    icon=(row.get("icon") or "").strip(),
                    role=(row.get("role") or "").strip(),
                    identity=(row.get("identity") or "").strip(),
                    communication_style=(row.get("communicationStyle") or "").strip(),
                    principles=(row.get("principles") or "").strip(),
                )
            )
    return members


def render_party(*, workdir: Path) -> str:
    csv_path = workdir / "_bmad" / "bts" / "teams" / "default-party.csv"
    if not csv_path.exists():
        return "Party data not found: _bmad/bts/teams/default-party.csv"

    members = load_party_members(csv_path)
    lines: list[str] = ["Party Mode (BTS)"]
    for m in members:
        icon = m.icon if _can_encode(m.icon) else "*"
        lines.append(f"- {icon} {m.display_name} ({m.title}) - {m.role}")

    return _safe_for_stdout("\n".join(lines))


def _safe_for_stdout(text: str) -> str:
    enc = sys.stdout.encoding or "utf-8"
    try:
        text.encode(enc)
        return text
    except UnicodeEncodeError:
        return text.encode(enc, errors="replace").decode(enc, errors="replace")


def _can_encode(text: str) -> bool:
    enc = sys.stdout.encoding or "utf-8"
    try:
        text.encode(enc)
        return True
    except UnicodeEncodeError:
        return False
