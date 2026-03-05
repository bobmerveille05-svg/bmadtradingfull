from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from bmadts._time import utcnow


_RULE_ID_RE = re.compile(r"\bR-\d{3}\b")


@dataclass(frozen=True)
class TraceRow:
    rule_id: str
    strategy_spec_ref: str | None
    logic_model_ref: str | None
    source_code_ref: str | None
    test_ref: str | None
    complete: bool


def write_traceability_map(workdir: Path) -> Path:
    content = generate_traceability_map(workdir)
    path = workdir / "TRACEABILITY-MAP.md"
    path.write_text(content, encoding="utf-8")
    return path


def generate_traceability_map(workdir: Path) -> str:
    spec_path = workdir / "STRATEGY-SPEC.md"
    spec_text = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""

    logic_path = workdir / "LOGIC-MODEL.md"
    logic_text = logic_path.read_text(encoding="utf-8") if logic_path.exists() else ""

    test_path = workdir / "TEST-REPORT.md"
    test_text = test_path.read_text(encoding="utf-8") if test_path.exists() else ""

    code_files: list[Path] = []
    for p in ["*_MT4.mq4", "*_MT5.mq5", "*_Pine.pine"]:
        code_files.extend(workdir.glob(p))
    code_files = sorted({p.resolve() for p in code_files})

    rule_ids = sorted(set(_RULE_ID_RE.findall(spec_text)))

    rows: list[TraceRow] = []
    for rid in rule_ids:
        spec_ref = _first_line_ref(spec_text, rid)
        logic_ref = _first_line_ref(logic_text, rid)
        code_ref = _first_code_ref(code_files, rid)
        test_ref = _first_line_ref(test_text, rid)

        complete = all([spec_ref, logic_ref, code_ref, test_ref])
        rows.append(
            TraceRow(
                rule_id=rid,
                strategy_spec_ref=spec_ref,
                logic_model_ref=logic_ref,
                source_code_ref=code_ref,
                test_ref=test_ref,
                complete=complete,
            )
        )

    completeness = 0
    if rows:
        completeness = int(round(100 * sum(1 for r in rows if r.complete) / len(rows)))

    missing_rule_ids: list[str] = [r.rule_id for r in rows if not r.complete]

    lines: list[str] = [
        "# TRACEABILITY-MAP",
        "",
        f"**Generated:** {utcnow().isoformat()}",
        f"**Completeness:** {completeness}%",
        "",
    ]

    if not rule_ids:
        lines.append("No Rule_IDs found in STRATEGY-SPEC.md.")
        lines.append("")
        return "\n".join(lines)

    lines.append(
        "| Rule_ID | STRATEGY-SPEC | LOGIC-MODEL | SOURCE CODE | TEST-REPORT | Complete |"
    )
    lines.append(
        "|--------|--------------|------------|------------|------------|----------|"
    )
    for r in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    r.rule_id,
                    r.strategy_spec_ref or "-",
                    r.logic_model_ref or "-",
                    r.source_code_ref or "-",
                    r.test_ref or "-",
                    "yes" if r.complete else "no",
                ]
            )
            + " |"
        )

    lines.append("")
    if missing_rule_ids:
        lines.append("Missing traceability for:")
        for rid in missing_rule_ids:
            lines.append(f"- {rid}")
        lines.append("")

    return "\n".join(lines)


def _first_line_ref(text: str, rid: str) -> str | None:
    if not text:
        return None
    for i, line in enumerate(text.splitlines(), start=1):
        if rid in line:
            # Keep it compact and safe for Markdown tables.
            snippet = line.strip()
            snippet = snippet.replace("|", "\\|")
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            return f"L{i}: {snippet}"
    return None


def _first_code_ref(code_files: list[Path], rid: str) -> str | None:
    for path in code_files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            if rid in line:
                # Heuristic: capture the next non-empty line as the "function" reference.
                next_sig = None
                for j in range(i, min(i + 6, len(lines))):
                    cand = lines[j].strip()
                    if cand and rid not in cand:
                        next_sig = cand
                        break
                next_sig = (next_sig or line.strip()).replace("|", "\\|")
                if len(next_sig) > 120:
                    next_sig = next_sig[:117] + "..."
                return f"{path.name}:L{i} {next_sig}"
    return None
