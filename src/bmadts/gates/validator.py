from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bmadts._time import utcnow
from bmadts.evidence import (
    Evidence,
    EvidenceStatus,
    EvidenceType,
    hash_file,
    verify_file_evidence,
    verify_numeric_threshold,
)
from bmadts.exceptions import FileSystemError
from bmadts.gates.checklists import GATE_CHECKLISTS, GateCriterion
from bmadts.metrics import StrategyMetrics, compute_metrics, load_trades_csv
from bmadts.montecarlo import MonteCarloResult, run_monte_carlo
from bmadts.models.enums import GateStatus
from bmadts.walk_forward import WalkForwardResult, run_walk_forward


_RULE_ID_RE = re.compile(r"\bR-\d{3}\b")


@dataclass(frozen=True)
class CriterionResult:
    criterion: GateCriterion
    status: EvidenceStatus
    message: str | None = None
    evidence: Evidence | None = None


@dataclass(frozen=True)
class GateResult:
    gate_number: int
    status: GateStatus
    criteria: list[CriterionResult]
    pass_percentage: int

    verified: int
    failed: int
    unverified: int
    skipped: int


class GateValidator:
    def __init__(
        self,
        workdir: Path,
        *,
        min_backtest_trades: int = 100,
        initial_capital: float = 10_000.0,
        risk_free_rate: float = 0.02,
        monte_carlo_iterations: int = 1000,
        walk_forward_periods: int = 5,
    ):
        self._workdir = workdir
        self._min_backtest_trades = min_backtest_trades
        self._initial_capital = initial_capital
        self._risk_free_rate = risk_free_rate
        self._monte_carlo_iterations = monte_carlo_iterations
        self._walk_forward_periods = walk_forward_periods

    def validate_gate(self, gate_number: int) -> GateResult:
        checklist = GATE_CHECKLISTS.get(gate_number)
        if not checklist:
            result = GateResult(
                gate_number,
                GateStatus.FAILED,
                [],
                0,
                verified=0,
                failed=0,
                unverified=0,
                skipped=0,
            )
            self._write_evidence_registry(result)
            return result

        if gate_number == 1:
            results = self._validate_gate_01(checklist)
        elif gate_number == 2:
            results = self._validate_gate_02(checklist)
        elif gate_number == 3:
            results = self._validate_gate_03(checklist)
        elif gate_number == 4:
            results = self._validate_gate_04(checklist)
        else:
            results = [
                CriterionResult(c, EvidenceStatus.FAILED, "Unknown gate")
                for c in checklist
            ]

        gate_status, pct, counts = _summarize_gate(results)
        gate_result = GateResult(
            gate_number,
            gate_status,
            results,
            pct,
            verified=counts[EvidenceStatus.VERIFIED],
            failed=counts[EvidenceStatus.FAILED],
            unverified=counts[EvidenceStatus.UNVERIFIED],
            skipped=counts[EvidenceStatus.SKIPPED],
        )

        # Evidence registry is written for every gate run.
        wrote = self._write_evidence_registry(gate_result)
        if gate_number == 4:
            gate_result = self._maybe_mark_gate_04_registry_written(gate_result, wrote)
            # Re-write to keep the registry consistent with the updated status.
            self._write_evidence_registry(gate_result)

        return gate_result

    def _maybe_mark_gate_04_registry_written(
        self, result: GateResult, wrote: bool
    ) -> GateResult:
        updated: list[CriterionResult] = []
        for r in result.criteria:
            if r.criterion.id != "G4-07":
                updated.append(r)
                continue

            updated.append(
                CriterionResult(
                    r.criterion,
                    EvidenceStatus.VERIFIED if wrote else EvidenceStatus.FAILED,
                    None if wrote else "Failed to write .bmad-evidence.json",
                    Evidence(
                        criterion_id=r.criterion.id,
                        evidence_type=EvidenceType.FILE_HASH
                        if wrote
                        else EvidenceType.FILE_EXISTS,
                        description=r.criterion.description,
                        status=EvidenceStatus.VERIFIED
                        if wrote
                        else EvidenceStatus.FAILED,
                        value=str(self._workdir / ".bmad-evidence.json")
                        if wrote
                        else None,
                        source_path=str(self._workdir / ".bmad-evidence.json"),
                        source_hash=(
                            hash_file(self._workdir / ".bmad-evidence.json")
                            if wrote
                            and (self._workdir / ".bmad-evidence.json").exists()
                            else None
                        ),
                    ),
                )
            )

        gate_status, pct, counts = _summarize_gate(updated)
        return GateResult(
            result.gate_number,
            gate_status,
            updated,
            pct,
            verified=counts[EvidenceStatus.VERIFIED],
            failed=counts[EvidenceStatus.FAILED],
            unverified=counts[EvidenceStatus.UNVERIFIED],
            skipped=counts[EvidenceStatus.SKIPPED],
        )

    def _read_required(self, filename: str) -> str:
        path = self._workdir / filename
        if not path.exists():
            raise FileSystemError(f"Missing artifact: {filename}")
        return path.read_text(encoding="utf-8")

    def _validate_gate_01(
        self, checklist: list[GateCriterion]
    ) -> list[CriterionResult]:
        spec_path = self._workdir / "STRATEGY-SPEC.md"
        if not spec_path.exists():
            msg = "Missing artifact: STRATEGY-SPEC.md"
            return [
                CriterionResult(
                    c,
                    EvidenceStatus.UNVERIFIED,
                    msg,
                    verify_file_evidence(c.id, c.description, spec_path),
                )
                for c in checklist
            ]

        text = spec_path.read_text(encoding="utf-8")

        required_sections = [
            "Overview",
            "Market_Context",
            "Entry_Rules",
            "Exit_Rules",
            "Risk_Management",
            "Filters",
            "Edge_Cases",
        ]
        missing = [s for s in required_sections if f"## {s}" not in text]
        all_sections_ok = len(missing) == 0

        rule_ids = _RULE_ID_RE.findall(text)
        unique_rule_ids = len(rule_ids) == len(set(rule_ids)) and len(rule_ids) > 0

        examples_present = bool(re.search(r"\bexamples?\b", text, re.IGNORECASE))

        checks: dict[str, tuple[EvidenceStatus, str | None]] = {
            "G1-01": (
                EvidenceStatus.VERIFIED if all_sections_ok else EvidenceStatus.FAILED,
                f"Missing sections: {', '.join(missing)}" if missing else None,
            ),
            "G1-02": (
                EvidenceStatus.VERIFIED if unique_rule_ids else EvidenceStatus.FAILED,
                "No Rule_IDs found"
                if not rule_ids
                else "Duplicate Rule_IDs found"
                if len(rule_ids) != len(set(rule_ids))
                else None,
            ),
            "G1-03": (
                EvidenceStatus.VERIFIED
                if _section_nonempty(text, "Entry_Rules")
                else EvidenceStatus.FAILED,
                None
                if _section_nonempty(text, "Entry_Rules")
                else "Entry_Rules section is empty",
            ),
            "G1-04": (
                EvidenceStatus.VERIFIED
                if _section_nonempty(text, "Exit_Rules")
                else EvidenceStatus.FAILED,
                None
                if _section_nonempty(text, "Exit_Rules")
                else "Exit_Rules section is empty",
            ),
            "G1-05": (
                EvidenceStatus.VERIFIED
                if _section_nonempty(text, "Risk_Management")
                else EvidenceStatus.FAILED,
                None
                if _section_nonempty(text, "Risk_Management")
                else "Risk_Management section is empty",
            ),
            "G1-06": (
                EvidenceStatus.VERIFIED
                if _section_nonempty(text, "Market_Context")
                else EvidenceStatus.FAILED,
                None
                if _section_nonempty(text, "Market_Context")
                else "Market_Context section is empty",
            ),
            "G1-07": (
                EvidenceStatus.VERIFIED
                if _section_nonempty(text, "Edge_Cases")
                else EvidenceStatus.FAILED,
                None
                if _section_nonempty(text, "Edge_Cases")
                else "Edge_Cases section is empty",
            ),
            "G1-08": (
                EvidenceStatus.VERIFIED if examples_present else EvidenceStatus.FAILED,
                None if examples_present else "No examples found",
            ),
            "G1-09": (EvidenceStatus.VERIFIED, None),
        }

        results: list[CriterionResult] = []
        for c in checklist:
            status, msg = checks.get(c.id, (EvidenceStatus.FAILED, "Unknown criterion"))
            results.append(
                CriterionResult(
                    c,
                    status,
                    msg,
                    Evidence(
                        criterion_id=c.id,
                        evidence_type=EvidenceType.LOG_CONTAINS,
                        description=c.description,
                        status=status,
                        value=None if msg else c.id,
                        source_path=str(spec_path),
                        source_hash=hash_file(spec_path),
                    ),
                )
            )

        return results

    def _validate_gate_02(
        self, checklist: list[GateCriterion]
    ) -> list[CriterionResult]:
        missing_files: list[str] = []
        spec_path = self._workdir / "STRATEGY-SPEC.md"
        logic_path = self._workdir / "LOGIC-MODEL.md"
        for fn in [spec_path, logic_path]:
            if not fn.exists():
                missing_files.append(fn.name)

        if missing_files:
            msg = "Missing artifacts: " + ", ".join(missing_files)
            return [
                CriterionResult(
                    c,
                    EvidenceStatus.UNVERIFIED,
                    msg,
                    verify_file_evidence(
                        c.id,
                        c.description,
                        logic_path if "LOGIC" in c.id else spec_path,
                    ),
                )
                for c in checklist
            ]

        spec_text = spec_path.read_text(encoding="utf-8")
        logic_text = logic_path.read_text(encoding="utf-8")

        spec_ids = set(_RULE_ID_RE.findall(spec_text))
        logic_ids = set(_RULE_ID_RE.findall(logic_text))

        trace_ok = bool(spec_ids) and spec_ids.issubset(logic_ids)
        missing_rule_ids = sorted(spec_ids - logic_ids)

        vars_ok = _section_nonempty(logic_text, "Variable_Definitions")

        # Gate-02 has several criteria that are not machine-verifiable yet.
        # They are marked UNVERIFIED until Phase 2/3 adds real parsers/checkers.
        checks: dict[str, tuple[EvidenceStatus, str | None]] = {
            "G2-01": (
                EvidenceStatus.VERIFIED if trace_ok else EvidenceStatus.FAILED,
                None
                if trace_ok
                else (
                    "No Rule_IDs found in STRATEGY-SPEC.md"
                    if not spec_ids
                    else "Missing Rule_IDs in LOGIC-MODEL.md: "
                    + ", ".join(missing_rule_ids)
                ),
            ),
            "G2-02": (
                EvidenceStatus.UNVERIFIED,
                "Formal formula validation not implemented yet",
            ),
            "G2-03": (
                EvidenceStatus.UNVERIFIED,
                "State machine reachability checking not implemented yet",
            ),
            "G2-04": (
                EvidenceStatus.VERIFIED if vars_ok else EvidenceStatus.FAILED,
                None if vars_ok else "Variable_Definitions section is empty",
            ),
            "G2-05": (
                EvidenceStatus.UNVERIFIED,
                "BMAD_PC parser not implemented yet",
            ),
            "G2-06": (
                EvidenceStatus.UNVERIFIED,
                "Truth table coverage checking not implemented yet",
            ),
            "G2-07": (EvidenceStatus.VERIFIED, None),
        }

        results: list[CriterionResult] = []
        for c in checklist:
            status, msg = checks.get(c.id, (EvidenceStatus.FAILED, "Unknown criterion"))
            results.append(
                CriterionResult(
                    c,
                    status,
                    msg,
                    Evidence(
                        criterion_id=c.id,
                        evidence_type=EvidenceType.COMPUTED,
                        description=c.description,
                        status=status,
                        source_path=str(logic_path),
                        source_hash=hash_file(logic_path),
                    ),
                )
            )

        return results

    def _validate_gate_03(
        self, checklist: list[GateCriterion]
    ) -> list[CriterionResult]:
        logic_path = self._workdir / "LOGIC-MODEL.md"
        code_files: list[Path] = []
        for p in ["*_MT4.mq4", "*_MT5.mq5", "*_Pine.pine"]:
            code_files.extend(self._workdir.glob(p))
        code_files = sorted({p.resolve() for p in code_files})

        compile_log = self._workdir / "compilation.log"

        if not logic_path.exists() or not code_files:
            missing: list[str] = []
            if not logic_path.exists():
                missing.append("LOGIC-MODEL.md")
            if not code_files:
                missing.append("<code files>")
            msg = "Missing artifacts: " + ", ".join(missing)
            return [
                CriterionResult(c, EvidenceStatus.UNVERIFIED, msg) for c in checklist
            ]

        logic_text = logic_path.read_text(encoding="utf-8")
        logic_rule_ids = sorted(set(_RULE_ID_RE.findall(logic_text)))

        code_texts: dict[Path, str] = {
            p: p.read_text(encoding="utf-8", errors="replace") for p in code_files
        }

        # G3-01: external compilation proof required.
        compile_status = EvidenceStatus.UNVERIFIED
        compile_msg = "Provide compilation.log from your platform (must show 0 errors)"
        compile_evidence: Evidence | None = None
        if compile_log.exists():
            text = compile_log.read_text(encoding="utf-8", errors="replace")
            low = text.lower()
            has_success = ("0 error" in low) or ("compilation successful" in low)
            if has_success:
                compile_status = EvidenceStatus.VERIFIED
                compile_msg = None
            else:
                compile_status = EvidenceStatus.FAILED
                compile_msg = (
                    "Compilation log does not indicate success (expected '0 error(s)')"
                )
            compile_evidence = Evidence(
                criterion_id="G3-01",
                evidence_type=EvidenceType.LOG_CONTAINS,
                description="Compilation evidence",
                status=compile_status,
                value="0 error" if has_success else None,
                threshold="0 error",
                source_path=str(compile_log),
                source_hash=hash_file(compile_log),
            )
        else:
            compile_evidence = verify_file_evidence(
                "G3-01",
                "Compilation log exists (compilation.log)",
                compile_log,
            )

        # G3-02: Rule_ID traceability.
        if not logic_rule_ids:
            trace_status = EvidenceStatus.UNVERIFIED
            trace_msg = "No Rule_IDs found in LOGIC-MODEL.md"
        else:
            missing_rule_ids: list[str] = []
            for rid in logic_rule_ids:
                if not any(rid in code_texts[p] for p in code_files):
                    missing_rule_ids.append(rid)
            if missing_rule_ids:
                trace_status = EvidenceStatus.FAILED
                trace_msg = "Missing Rule_IDs in code: " + ", ".join(missing_rule_ids)
            else:
                trace_status = EvidenceStatus.VERIFIED
                trace_msg = None

        # G3-03: template markers.
        required_markers = [
            "Inputs",
            "Variables",
            "Initialization",
            "Main_Logic",
            "Entry_Functions",
            "Exit_Functions",
            "Risk_Management",
        ]
        template_ok = all(
            sum(1 for m in required_markers if m in code_texts[p]) >= 4
            for p in code_files
        )
        template_status = (
            EvidenceStatus.VERIFIED if template_ok else EvidenceStatus.FAILED
        )
        template_msg = (
            None
            if template_ok
            else "Code does not appear to follow the standard template"
        )

        # G3-04: best-effort error handling scan.
        error_ok = any(
            re.search(
                r"\b(error|getlasterror|lasterror)\b", code_texts[p], re.IGNORECASE
            )
            for p in code_files
        )
        error_status = EvidenceStatus.VERIFIED if error_ok else EvidenceStatus.FAILED
        error_msg = None if error_ok else "No obvious error handling found"

        # G3-05: variables from logic declared in code.
        var_names = _extract_variable_names_from_logic(logic_text)
        if not var_names:
            vars_status = EvidenceStatus.UNVERIFIED
            vars_msg = "No variables found in LOGIC-MODEL.md Variable_Definitions"
        else:
            missing_vars: list[str] = []
            for v in sorted(var_names):
                if not any(
                    re.search(rf"\b{re.escape(v)}\b", code_texts[p]) for p in code_files
                ):
                    missing_vars.append(v)
            if missing_vars:
                vars_status = EvidenceStatus.FAILED
                vars_msg = "Missing variables in code: " + ", ".join(missing_vars)
            else:
                vars_status = EvidenceStatus.VERIFIED
                vars_msg = None

        # G3-06: filename patterns.
        ok_names = all(
            p.name.endswith("_MT4.mq4")
            or p.name.endswith("_MT5.mq5")
            or p.name.endswith("_Pine.pine")
            for p in code_files
        )
        names_status = EvidenceStatus.VERIFIED if ok_names else EvidenceStatus.FAILED
        names_msg = (
            None if ok_names else "One or more code files have an unexpected filename"
        )

        checks: dict[str, tuple[EvidenceStatus, str | None, Evidence | None]] = {
            "G3-01": (compile_status, compile_msg, compile_evidence),
            "G3-02": (
                trace_status,
                trace_msg,
                Evidence(
                    criterion_id="G3-02",
                    evidence_type=EvidenceType.COMPUTED,
                    description="Rule_ID traceability in code",
                    status=trace_status,
                    value=None if trace_msg else "all-present",
                    source_path=str(logic_path),
                    source_hash=hash_file(logic_path),
                ),
            ),
            "G3-03": (
                template_status,
                template_msg,
                Evidence(
                    criterion_id="G3-03",
                    evidence_type=EvidenceType.COMPUTED,
                    description="Template structure markers",
                    status=template_status,
                ),
            ),
            "G3-04": (
                error_status,
                error_msg,
                Evidence(
                    criterion_id="G3-04",
                    evidence_type=EvidenceType.COMPUTED,
                    description="Error handling scan",
                    status=error_status,
                ),
            ),
            "G3-05": (
                vars_status,
                vars_msg,
                Evidence(
                    criterion_id="G3-05",
                    evidence_type=EvidenceType.COMPUTED,
                    description="Variable declarations scan",
                    status=vars_status,
                ),
            ),
            "G3-06": (
                names_status,
                names_msg,
                Evidence(
                    criterion_id="G3-06",
                    evidence_type=EvidenceType.COMPUTED,
                    description="Filename pattern check",
                    status=names_status,
                ),
            ),
        }

        results: list[CriterionResult] = []
        for c in checklist:
            status, msg, ev = checks.get(
                c.id, (EvidenceStatus.FAILED, "Unknown criterion", None)
            )
            results.append(CriterionResult(c, status, msg, ev))
        return results

    def _validate_gate_04(
        self, checklist: list[GateCriterion]
    ) -> list[CriterionResult]:
        trades_path = self._workdir / "trades.csv"
        metrics_path = self._workdir / ".bmad-metrics.json"

        evidence_trade_file = verify_file_evidence(
            "G4-01",
            "trades.csv exists (exported from backtest platform)",
            trades_path,
        )
        if evidence_trade_file.status != EvidenceStatus.VERIFIED:
            msg = "Missing trades.csv. Export real trades and place trades.csv in the project root."
            results: list[CriterionResult] = []
            for c in checklist:
                if c.id == "G4-01":
                    results.append(
                        CriterionResult(
                            c, EvidenceStatus.UNVERIFIED, msg, evidence_trade_file
                        )
                    )
                else:
                    results.append(CriterionResult(c, EvidenceStatus.UNVERIFIED, msg))
            return results

        metrics_file_ev = verify_file_evidence(
            "G4-06",
            "Metrics evidence file written (.bmad-metrics.json)",
            metrics_path,
        )

        if metrics_file_ev.status != EvidenceStatus.VERIFIED:
            msg = "Missing .bmad-metrics.json. Run: bmadts verify"
            placeholder_registry = Evidence(
                criterion_id="G4-07",
                evidence_type=EvidenceType.FILE_EXISTS,
                description="Evidence registry updated (.bmad-evidence.json)",
                status=EvidenceStatus.UNVERIFIED,
                source_path=str(self._workdir / ".bmad-evidence.json"),
            )

            checks: dict[str, tuple[EvidenceStatus, str | None, Evidence | None]] = {
                "G4-01": (EvidenceStatus.VERIFIED, None, evidence_trade_file),
                "G4-02": (EvidenceStatus.UNVERIFIED, msg, None),
                "G4-03": (EvidenceStatus.UNVERIFIED, msg, None),
                "G4-04": (EvidenceStatus.UNVERIFIED, msg, None),
                "G4-05": (EvidenceStatus.UNVERIFIED, msg, None),
                "G4-06": (metrics_file_ev.status, msg, metrics_file_ev),
                "G4-07": (
                    EvidenceStatus.UNVERIFIED,
                    "Evidence registry not written yet",
                    placeholder_registry,
                ),
            }

            results: list[CriterionResult] = []
            for c in checklist:
                status, m, ev = checks.get(
                    c.id, (EvidenceStatus.FAILED, "Unknown criterion", None)
                )
                results.append(CriterionResult(c, status, m, ev))
            return results

        # metrics file exists; load and validate it matches trades.csv
        try:
            payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        except Exception as e:
            msg = f"Failed to parse .bmad-metrics.json: {e}"
            return [CriterionResult(c, EvidenceStatus.FAILED, msg) for c in checklist]

        expected_hash = hash_file(trades_path)
        actual_hash = payload.get("source_hash") if isinstance(payload, dict) else None
        if actual_hash != expected_hash:
            msg = "Metrics file does not match trades.csv (hash mismatch). Re-run: bmadts verify"
            return [CriterionResult(c, EvidenceStatus.FAILED, msg) for c in checklist]

        metrics = payload.get("metrics") if isinstance(payload, dict) else None
        wfa = payload.get("walk_forward") if isinstance(payload, dict) else None
        mc = payload.get("monte_carlo") if isinstance(payload, dict) else None

        total_trades = None
        if isinstance(metrics, dict):
            try:
                total_trades = int(metrics.get("total_trades"))
            except Exception:
                total_trades = None

        ev_trades = verify_numeric_threshold(
            "G4-02",
            "Backtest includes at least min trades",
            value=total_trades,
            threshold=self._min_backtest_trades,
            operator=">=",
        )

        required_metric_keys = [
            "total_trades",
            "win_rate",
            "profit_factor",
            "sharpe_ratio",
            "maximum_drawdown",
            "average_win",
            "average_loss",
            "largest_win",
            "largest_loss",
            "consecutive_wins",
            "consecutive_losses",
            "average_trade_duration_seconds",
            "total_return_pct",
            "annualized_return_pct",
            "risk_reward_ratio",
            "recovery_factor",
            "expectancy",
            "calmar_ratio",
        ]

        metrics_ok = isinstance(metrics, dict) and all(
            (k in metrics) and (metrics.get(k) is not None)
            for k in required_metric_keys
        )
        ev_metrics = Evidence(
            criterion_id="G4-03",
            evidence_type=EvidenceType.COMPUTED,
            description="All 18 backtest metrics computed from trades.csv",
            status=EvidenceStatus.VERIFIED if metrics_ok else EvidenceStatus.FAILED,
            value=("18/18" if metrics_ok else "missing"),
            source_path=str(metrics_path),
            source_hash=hash_file(metrics_path),
        )

        wfa_status = EvidenceStatus.UNVERIFIED
        wfa_msg = None
        if isinstance(wfa, dict):
            try:
                pr = wfa.get("period_results")
                pr_len = len(pr) if isinstance(pr, list) else 0
                wfa_ok = pr_len >= self._walk_forward_periods
                wfa_status = (
                    EvidenceStatus.VERIFIED if wfa_ok else EvidenceStatus.FAILED
                )
                if not wfa_ok:
                    wfa_msg = "Walk-forward results do not include enough periods"
            except Exception:
                wfa_status = EvidenceStatus.FAILED
                wfa_msg = "Walk-forward results invalid"

        ev_wfa = Evidence(
            criterion_id="G4-04",
            evidence_type=EvidenceType.COMPUTED,
            description="Walk-Forward Analysis computed",
            status=wfa_status,
            source_path=str(metrics_path),
            source_hash=hash_file(metrics_path),
        )

        mc_status = EvidenceStatus.UNVERIFIED
        mc_msg = None
        if isinstance(mc, dict):
            try:
                iters = int(mc.get("iterations"))
                mc_ok = iters >= self._monte_carlo_iterations
                mc_status = EvidenceStatus.VERIFIED if mc_ok else EvidenceStatus.FAILED
                if not mc_ok:
                    mc_msg = "Monte Carlo iterations below configured requirement"
            except Exception:
                mc_status = EvidenceStatus.FAILED
                mc_msg = "Monte Carlo results invalid"

        ev_mc = Evidence(
            criterion_id="G4-05",
            evidence_type=EvidenceType.COMPUTED,
            description="Monte Carlo Simulation computed",
            status=mc_status,
            source_path=str(metrics_path),
            source_hash=hash_file(metrics_path),
        )

        placeholder_registry = Evidence(
            criterion_id="G4-07",
            evidence_type=EvidenceType.FILE_EXISTS,
            description="Evidence registry updated (.bmad-evidence.json)",
            status=EvidenceStatus.UNVERIFIED,
            source_path=str(self._workdir / ".bmad-evidence.json"),
        )

        checks: dict[str, tuple[EvidenceStatus, str | None, Evidence | None]] = {
            "G4-01": (EvidenceStatus.VERIFIED, None, evidence_trade_file),
            "G4-02": (
                ev_trades.status,
                None
                if ev_trades.status == EvidenceStatus.VERIFIED
                else f"Total trades {total_trades} < min {self._min_backtest_trades}",
                ev_trades,
            ),
            "G4-03": (
                ev_metrics.status,
                None
                if ev_metrics.status == EvidenceStatus.VERIFIED
                else "Not all metrics present in .bmad-metrics.json",
                ev_metrics,
            ),
            "G4-04": (wfa_status, wfa_msg, ev_wfa),
            "G4-05": (mc_status, mc_msg, ev_mc),
            "G4-06": (EvidenceStatus.VERIFIED, None, metrics_file_ev),
            "G4-07": (
                EvidenceStatus.UNVERIFIED,
                "Evidence registry not written yet",
                placeholder_registry,
            ),
        }

        results: list[CriterionResult] = []
        for c in checklist:
            status, msg, ev = checks.get(
                c.id, (EvidenceStatus.FAILED, "Unknown criterion", None)
            )
            results.append(CriterionResult(c, status, msg, ev))
        return results

    def _write_evidence_registry(self, result: GateResult) -> bool:
        path = self._workdir / ".bmad-evidence.json"
        payload = {
            "generated_at": utcnow().isoformat(),
            "gate": result.gate_number,
            "status": result.status.value,
            "pass_percentage": result.pass_percentage,
            "counts": {
                "verified": result.verified,
                "failed": result.failed,
                "unverified": result.unverified,
                "skipped": result.skipped,
            },
            "criteria": [
                {
                    "id": r.criterion.id,
                    "description": r.criterion.description,
                    "status": r.status.value,
                    "message": r.message,
                    "evidence": r.evidence.to_dict() if r.evidence else None,
                }
                for r in result.criteria
            ],
        }
        try:
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            return True
        except Exception:
            return False


def _summarize_gate(
    results: list[CriterionResult],
) -> tuple[GateStatus, int, dict[EvidenceStatus, int]]:
    counts: dict[EvidenceStatus, int] = {
        EvidenceStatus.VERIFIED: 0,
        EvidenceStatus.FAILED: 0,
        EvidenceStatus.UNVERIFIED: 0,
        EvidenceStatus.SKIPPED: 0,
    }
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1

    total = max(1, len(results))
    pct = int(round(100 * counts[EvidenceStatus.VERIFIED] / total))

    if counts[EvidenceStatus.FAILED] > 0:
        return GateStatus.FAILED, pct, counts
    if counts[EvidenceStatus.UNVERIFIED] > 0:
        return GateStatus.UNVERIFIED, pct, counts
    return GateStatus.PASSED, pct, counts


def _section_nonempty(text: str, section: str) -> bool:
    marker = f"## {section}"
    idx = text.find(marker)
    if idx < 0:
        return False

    after = text[idx + len(marker) :]
    next_idx = after.find("\n## ")
    body = after if next_idx < 0 else after[:next_idx]
    return bool(body.strip())


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
