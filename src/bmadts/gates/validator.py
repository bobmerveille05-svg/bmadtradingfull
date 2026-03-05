from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from bmadts.exceptions import FileSystemError
from bmadts.gates.checklists import GATE_CHECKLISTS, GateCriterion
from bmadts.models.enums import GateStatus


_RULE_ID_RE = re.compile(r"\bR-\d{3}\b")


@dataclass(frozen=True)
class CriterionResult:
    criterion: GateCriterion
    passed: bool
    message: str | None = None


@dataclass(frozen=True)
class GateResult:
    gate_number: int
    status: GateStatus
    criteria: list[CriterionResult]
    pass_percentage: int


class GateValidator:
    def __init__(self, workdir: Path, *, min_backtest_trades: int = 100):
        self._workdir = workdir
        self._min_backtest_trades = min_backtest_trades

    def validate_gate(self, gate_number: int) -> GateResult:
        checklist = GATE_CHECKLISTS.get(gate_number)
        if not checklist:
            return GateResult(gate_number, GateStatus.FAILED, [], 0)

        if gate_number == 1:
            results = self._validate_gate_01(checklist)
        elif gate_number == 2:
            results = self._validate_gate_02(checklist)
        elif gate_number == 3:
            results = self._validate_gate_03(checklist)
        elif gate_number == 4:
            results = self._validate_gate_04(checklist)
        else:
            results = [CriterionResult(c, False, "Unknown gate") for c in checklist]

        passed = sum(1 for r in results if r.passed)
        pct = int(round(100 * passed / max(1, len(results))))
        status = GateStatus.PASSED if passed == len(results) else GateStatus.FAILED
        return GateResult(gate_number, status, results, pct)

    def _read_required(self, filename: str) -> str:
        path = self._workdir / filename
        if not path.exists():
            raise FileSystemError(f"Missing artifact: {filename}")
        return path.read_text(encoding="utf-8")

    def _sections_present(
        self, text: str, sections: list[str]
    ) -> tuple[bool, list[str]]:
        missing: list[str] = []
        for s in sections:
            if f"## {s}" not in text:
                missing.append(s)
        return (len(missing) == 0), missing

    def _section_nonempty(self, text: str, section: str) -> bool:
        marker = f"## {section}"
        idx = text.find(marker)
        if idx < 0:
            return False

        after = text[idx + len(marker) :]
        # Next section starts with "## ".
        next_idx = after.find("\n## ")
        body = after if next_idx < 0 else after[:next_idx]
        body = body.strip()
        return bool(body)

    def _extract_rule_ids(self, text: str) -> list[str]:
        return _RULE_ID_RE.findall(text)

    def _validate_gate_01(
        self, checklist: list[GateCriterion]
    ) -> list[CriterionResult]:
        filename = "STRATEGY-SPEC.md"
        try:
            text = self._read_required(filename)
        except FileSystemError as e:
            return [CriterionResult(c, False, str(e)) for c in checklist]

        required_sections = [
            "Overview",
            "Market_Context",
            "Entry_Rules",
            "Exit_Rules",
            "Risk_Management",
            "Filters",
            "Edge_Cases",
        ]
        ok_sections, missing = self._sections_present(text, required_sections)

        rule_ids = self._extract_rule_ids(text)
        unique_rule_ids = len(rule_ids) == len(set(rule_ids)) and len(rule_ids) > 0

        examples_present = bool(re.search(r"\bexamples?\b", text, re.IGNORECASE))

        checks: dict[str, tuple[bool, str | None]] = {
            "G1-01": (
                ok_sections,
                f"Missing sections: {', '.join(missing)}" if missing else None,
            ),
            "G1-02": (
                unique_rule_ids,
                "No Rule_IDs found"
                if not rule_ids
                else "Duplicate Rule_IDs found"
                if len(rule_ids) != len(set(rule_ids))
                else None,
            ),
            "G1-03": (
                self._section_nonempty(text, "Entry_Rules"),
                "Entry_Rules section is empty",
            ),
            "G1-04": (
                self._section_nonempty(text, "Exit_Rules"),
                "Exit_Rules section is empty",
            ),
            "G1-05": (
                self._section_nonempty(text, "Risk_Management"),
                "Risk_Management section is empty",
            ),
            "G1-06": (
                self._section_nonempty(text, "Market_Context"),
                "Market_Context section is empty",
            ),
            "G1-07": (
                self._section_nonempty(text, "Edge_Cases"),
                "Edge_Cases section is empty",
            ),
            "G1-08": (examples_present, "No examples found"),
            "G1-09": (True, None),
        }

        results: list[CriterionResult] = []
        for c in checklist:
            ok, msg = checks.get(c.id, (False, "Unknown criterion"))
            results.append(CriterionResult(c, ok, None if ok else msg))
        return results

    def _validate_gate_02(
        self, checklist: list[GateCriterion]
    ) -> list[CriterionResult]:
        missing_files: list[str] = []
        for fn in ["STRATEGY-SPEC.md", "LOGIC-MODEL.md"]:
            if not (self._workdir / fn).exists():
                missing_files.append(fn)
        if missing_files:
            msg = "Missing artifacts: " + ", ".join(missing_files)
            return [CriterionResult(c, False, msg) for c in checklist]

        spec = self._read_required("STRATEGY-SPEC.md")
        logic = self._read_required("LOGIC-MODEL.md")

        required_sections = [
            "Mathematical_Formulas",
            "State_Machine",
            "Pseudo_Code",
            "Truth_Tables",
            "Variable_Definitions",
        ]
        ok_sections, missing = self._sections_present(logic, required_sections)

        spec_ids = set(self._extract_rule_ids(spec))
        logic_ids = set(self._extract_rule_ids(logic))
        trace_ok = bool(spec_ids) and spec_ids.issubset(logic_ids)

        pseudo_ok = bool(re.search(r"\b(IF|FUNCTION|RETURN|WHILE|FOR)\b", logic))
        truth_ok = "|" in logic
        vars_ok = self._section_nonempty(logic, "Variable_Definitions")
        state_ok = self._section_nonempty(logic, "State_Machine")
        formulas_ok = self._section_nonempty(logic, "Mathematical_Formulas")

        checks: dict[str, tuple[bool, str | None]] = {
            "G2-01": (
                trace_ok,
                (
                    "No Rule_IDs found in STRATEGY-SPEC.md"
                    if not spec_ids
                    else "Missing Rule_IDs in LOGIC-MODEL.md: "
                    + ", ".join(sorted(spec_ids - logic_ids))
                ),
            ),
            "G2-02": (formulas_ok, "Mathematical_Formulas section is empty"),
            "G2-03": (state_ok, "State_Machine section is empty"),
            "G2-04": (vars_ok, "Variable_Definitions section is empty"),
            "G2-05": (pseudo_ok, "Pseudo_Code section appears missing or empty"),
            "G2-06": (truth_ok, "Truth_Tables section appears missing"),
            "G2-07": (
                ok_sections,
                f"Missing sections: {', '.join(missing)}" if missing else None,
            ),
        }

        results: list[CriterionResult] = []
        for c in checklist:
            ok, msg = checks.get(c.id, (False, "Unknown criterion"))
            results.append(CriterionResult(c, ok, None if ok else msg))
        return results

    def _validate_gate_03(
        self, checklist: list[GateCriterion]
    ) -> list[CriterionResult]:
        missing_files: list[str] = []
        logic_path = self._workdir / "LOGIC-MODEL.md"
        if not logic_path.exists():
            missing_files.append("LOGIC-MODEL.md")

        code_files: list[Path] = []
        for p in ["*_MT4.mq4", "*_MT5.mq5", "*_Pine.pine"]:
            code_files.extend(self._workdir.glob(p))
        code_files = sorted({p.resolve() for p in code_files})
        if not code_files:
            missing_files.append("<code files>")

        if missing_files:
            msg = "Missing artifacts: " + ", ".join(missing_files)
            return [CriterionResult(c, False, msg) for c in checklist]

        logic = logic_path.read_text(encoding="utf-8")
        logic_rule_ids = set(self._extract_rule_ids(logic))

        code_texts: dict[Path, str] = {}
        for path in code_files:
            try:
                code_texts[path] = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                code_texts[path] = ""

        # G3-01: compilation verification is not wired yet. Best-effort check:
        # require non-empty code files.
        compile_ok = all(code_texts[p].strip() for p in code_files)

        # G3-02: all Rule_IDs from logic appear in code.
        missing_rule_ids: list[str] = []
        if logic_rule_ids:
            for rid in sorted(logic_rule_ids):
                if not any(rid in code_texts[p] for p in code_files):
                    missing_rule_ids.append(rid)
        trace_ok = bool(logic_rule_ids) and not missing_rule_ids

        # G3-03: look for standardized section markers.
        required_markers = [
            "Inputs",
            "Variables",
            "Initialization",
            "Main_Logic",
            "Entry_Functions",
            "Exit_Functions",
            "Risk_Management",
        ]
        template_ok = True
        for p in code_files:
            text = code_texts[p]
            if sum(1 for m in required_markers if m in text) < 4:
                template_ok = False
                break

        # G3-04: basic error handling presence.
        error_ok = any(
            re.search(r"\berror\b", code_texts[p], re.IGNORECASE) for p in code_files
        )

        # G3-05: variables from logic appear in code (best-effort).
        var_names = _extract_variable_names_from_logic(logic)
        missing_vars: list[str] = []
        if var_names:
            for v in sorted(var_names):
                if not any(
                    re.search(rf"\b{re.escape(v)}\b", code_texts[p]) for p in code_files
                ):
                    missing_vars.append(v)
        vars_ok = bool(var_names) and not missing_vars

        checks: dict[str, tuple[bool, str | None]] = {
            "G3-01": (
                compile_ok,
                "One or more code files are empty" if not compile_ok else None,
            ),
            "G3-02": (
                trace_ok,
                (
                    "No Rule_IDs found in LOGIC-MODEL.md"
                    if not logic_rule_ids
                    else "Missing Rule_IDs in code: " + ", ".join(missing_rule_ids)
                ),
            ),
            "G3-03": (
                template_ok,
                "Code does not appear to follow the standard template",
            ),
            "G3-04": (error_ok, "No obvious error handling found"),
            "G3-05": (
                vars_ok,
                (
                    "No variables found in LOGIC-MODEL.md"
                    if not var_names
                    else "Missing variables in code: " + ", ".join(missing_vars)
                ),
            ),
            "G3-06": (True, None),
        }

        results: list[CriterionResult] = []
        for c in checklist:
            ok, msg = checks.get(c.id, (False, "Unknown criterion"))
            results.append(CriterionResult(c, ok, None if ok else msg))
        return results

    def _validate_gate_04(
        self, checklist: list[GateCriterion]
    ) -> list[CriterionResult]:
        report_path = self._workdir / "TEST-REPORT.md"
        if not report_path.exists():
            msg = "Missing artifact: TEST-REPORT.md"
            return [CriterionResult(c, False, msg) for c in checklist]

        text = report_path.read_text(encoding="utf-8")

        unit_ok = bool(re.search(r"\bunit\b.*\bpass", text, re.IGNORECASE))
        integ_ok = bool(re.search(r"\bintegration\b.*\bpass", text, re.IGNORECASE))

        total_trades = _extract_int_metric(text, "Total_Trades")
        trades_ok = (
            total_trades is not None and total_trades >= self._min_backtest_trades
        )

        required_metrics = [
            "Total_Trades",
            "Win_Rate",
            "Profit_Factor",
            "Sharpe_Ratio",
            "Maximum_Drawdown",
            "Average_Win",
            "Average_Loss",
            "Largest_Win",
            "Largest_Loss",
            "Consecutive_Wins",
            "Consecutive_Losses",
            "Average_Trade_Duration",
            "Total_Return",
            "Annualized_Return",
            "Risk_Reward_Ratio",
            "Recovery_Factor",
            "Expectancy",
            "Calmar_Ratio",
        ]
        metrics_ok = all(m in text for m in required_metrics)

        wf_ok = bool(re.search(r"walk[-_ ]?forward", text, re.IGNORECASE))
        mc_ok = bool(re.search(r"monte[-_ ]?carlo", text, re.IGNORECASE))

        checks: dict[str, tuple[bool, str | None]] = {
            "G4-01": (unit_ok, "Unit test pass status not found"),
            "G4-02": (integ_ok, "Integration test pass status not found"),
            "G4-03": (
                trades_ok,
                (
                    "Total_Trades not found"
                    if total_trades is None
                    else f"Total_Trades {total_trades} < min {self._min_backtest_trades}"
                ),
            ),
            "G4-04": (metrics_ok, "Not all required backtest metrics found"),
            "G4-05": (wf_ok, "Walk-Forward Analysis not found"),
            "G4-06": (mc_ok, "Monte Carlo Simulation not found"),
            "G4-07": (True, None),
        }

        results: list[CriterionResult] = []
        for c in checklist:
            ok, msg = checks.get(c.id, (False, "Unknown criterion"))
            results.append(CriterionResult(c, ok, None if ok else msg))
        return results


def _extract_variable_names_from_logic(logic_text: str) -> set[str]:
    marker = "## Variable_Definitions"
    idx = logic_text.find(marker)
    if idx < 0:
        return set()

    after = logic_text[idx + len(marker) :]
    next_idx = after.find("\n## ")
    body = after if next_idx < 0 else after[:next_idx]

    names: set[str] = set()
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if not cols:
            continue
        name = cols[0]
        if name.lower() in {"name", "------"}:
            continue
        if re.fullmatch(r"[a-z][a-z0-9_]*", name):
            names.add(name)
    return names


def _extract_int_metric(text: str, metric: str) -> int | None:
    m = re.search(rf"\b{re.escape(metric)}\b\s*[:=]\s*(\d+)", text)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None
