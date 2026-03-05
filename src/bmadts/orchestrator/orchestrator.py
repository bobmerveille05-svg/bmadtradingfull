from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any
import zipfile

from bmadts._time import utcnow
from bmadts.artifacts.artifact_manager import ArtifactManager
from bmadts.artifacts.template_manager import TemplateManager
from bmadts.artifacts.versioning import bump_minor
from bmadts.exceptions import (
    BMADException,
    CommandError,
    ConfigValidationError,
    FileSystemError,
)
from bmadts.models.artifact import Artifact
from bmadts.models.config import Configuration
from bmadts.models.enums import AgentType, ArtifactType, GateStatus, Phase
from bmadts.models.session import ArtifactRef, SessionState
from bmadts.orchestrator.commands import Command, parse_command
from bmadts.orchestrator.audit_trail import AuditTrail
from bmadts.orchestrator.session_manager import SessionManager
from bmadts.orchestrator.state_machine import StateMachine
from bmadts.gates.checklists import GATE_CHECKLISTS
from bmadts.gates.validator import GateValidator
from bmadts.traceability import write_traceability_map


class Orchestrator:
    def __init__(
        self,
        *,
        workdir: Path,
        config: Configuration,
        session_manager: SessionManager,
        state_machine: StateMachine,
        artifact_manager: ArtifactManager,
        gate_validator: GateValidator,
        audit_trail: AuditTrail,
        state: SessionState,
    ):
        self._workdir = workdir
        self._config = config
        self._session_manager = session_manager
        self._state_machine = state_machine
        self._artifact_manager = artifact_manager
        self._gate_validator = gate_validator
        self._audit_trail = audit_trail
        self._state = state

        self._logger = logging.getLogger("bmadts")
        self._configure_logging()

    @classmethod
    def from_workdir(cls, workdir: Path | None = None) -> "Orchestrator":
        wd = Path.cwd() if workdir is None else workdir

        config_path = wd / "bmad-config.json"
        try:
            config = Configuration.load_from_file(config_path, create_if_missing=True)
        except ConfigValidationError as e:
            msg = "Invalid config in bmad-config.json:\n" + "\n".join(
                f"- {x}" for x in e.errors
            )
            raise CommandError(msg) from e

        session_manager = SessionManager(wd / ".bmad-session.json")
        state_machine = StateMachine()

        templates_dir = wd / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        templates = TemplateManager(templates_dir)
        artifact_manager = ArtifactManager(workdir=wd, templates=templates)
        gate_validator = GateValidator(
            wd, min_backtest_trades=config.min_backtest_trades
        )
        audit_trail = AuditTrail(wd / "AUDIT-TRAIL.md")

        if session_manager.session_exists():
            state = session_manager.restore_state()
        else:
            state = SessionState(language=config.language)

        return cls(
            workdir=wd,
            config=config,
            session_manager=session_manager,
            state_machine=state_machine,
            artifact_manager=artifact_manager,
            gate_validator=gate_validator,
            audit_trail=audit_trail,
            state=state,
        )

    def _configure_logging(self) -> None:
        log_file = self._workdir / "bmad-errors.log"
        if self._logger.handlers:
            return

        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setLevel(logging.ERROR)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        handler.setFormatter(formatter)

        self._logger.setLevel(logging.INFO)
        self._logger.addHandler(handler)

    @property
    def state(self) -> SessionState:
        return self._state

    def run_repl(self) -> int:
        print("BMAD Trading System (WIP)")
        print("Type /help for commands. /quit to exit.")

        if (
            self._session_manager.session_exists()
            and self._state.current_phase != Phase.IDLE
        ):
            choice = input(
                f"Found existing session {self._state.session_id} at phase {self._state.current_phase.value}. "
                "Resume? [Y/n] "
            ).strip()
            if choice.lower() in {"n", "no"}:
                print(self._start_session())

        while True:
            try:
                line = input("bmadts> ").strip()
            except EOFError:
                print()
                return 0

            if not line:
                continue

            try:
                output = self.execute_command(line)
            except BMADException as e:
                print(str(e))
                continue

            if output == "__EXIT__":
                return 0
            if output:
                print(output)

    def execute_command(self, command_text: str) -> str:
        self._safe_audit("USER_COMMAND", f"{command_text.strip()}")
        cmd, args = parse_command(command_text)

        if args:
            raise CommandError(f"Command does not accept arguments yet: {cmd.value}")

        try:
            if cmd == Command.HELP:
                return self._help_text()
            if cmd in {Command.EXIT, Command.QUIT}:
                return "__EXIT__"
            if cmd == Command.STATUS:
                return self._status_text()
            if cmd == Command.AGENT:
                return self._agent_text()
            if cmd == Command.START:
                return self._start_session()
            if cmd == Command.ROLLBACK:
                return self._rollback()
            if cmd == Command.GATE:
                return self._gate_text()
            if cmd == Command.CHECKLIST:
                return self._checklist_text()
            if cmd == Command.SPEC:
                return self._show_artifact(ArtifactType.STRATEGY_SPEC)
            if cmd == Command.LOGIC:
                return self._show_artifact(ArtifactType.LOGIC_MODEL)
            if cmd == Command.TEST:
                return self._show_artifact(ArtifactType.TEST_REPORT)
            if cmd == Command.PROOF:
                return self._show_artifact(ArtifactType.PROOF_CERTIFICATE)
            if cmd == Command.CODE:
                return self._show_code_artifacts()
            if cmd == Command.AUDIT:
                return self._audit_text()
            if cmd == Command.EXPORT:
                return self._export_package()
            if cmd == Command.SPEC_WIZARD:
                return self._spec_wizard()
            if cmd == Command.CODE_WIZARD:
                return self._code_wizard()
            if cmd == Command.LOGIC_WIZARD:
                return self._logic_wizard()
            if cmd == Command.TEST_WIZARD:
                return self._test_wizard()

            return f"Not implemented yet: {cmd.value}"
        except BMADException as e:
            self._logger.error(str(e))
            raise
        except Exception as e:
            self._logger.exception("Unhandled error")
            raise CommandError(str(e)) from e

    def _help_text(self) -> str:
        cmds = [c.value for c in Command if c not in {Command.EXIT, Command.QUIT}]
        return "Commands:\n" + "\n".join(f"- {c}" for c in cmds) + "\n- /quit"

    def _status_text(self) -> str:
        s = self._state
        hint = _next_step_hint(s.current_phase)
        return (
            "Status:\n"
            f"- session_id: {s.session_id}\n"
            f"- phase: {s.current_phase}\n"
            f"- gate: {s.current_gate} ({s.gate_status})\n"
            f"- active_agent: {s.active_agent}\n"
            f"- artifacts: {len(s.artifacts)}\n"
            f"- next: {hint}"
        )

    def _start_session(self) -> str:
        # Preserve any existing session file.
        if self._session_manager.session_exists():
            ts = utcnow().strftime("%Y%m%d-%H%M%S")
            backup = self._workdir / f".bmad-session.{ts}.bak.json"
            self._session_manager.session_file.replace(backup)

        self._state = SessionState(language=self._config.language)
        self._state = self._state_machine.transition_forward(self._state)
        self._state = self._state.touch()
        self._session_manager.persist_state(self._state)

        self._safe_audit(
            "PHASE_TRANSITION",
            "IDLE -> SPEC",
            {"from": "IDLE", "to": "SPEC", "session_id": str(self._state.session_id)},
        )

        # Create a skeleton STRATEGY-SPEC.md if missing.
        self._maybe_create_skeleton(ArtifactType.STRATEGY_SPEC)
        return "Session started. Current phase: SPEC"

    def _rollback(self) -> str:
        if self._state.current_phase == Phase.SPEC:
            raise CommandError("Cannot rollback from SPEC")
        if self._state.current_phase == Phase.IDLE:
            raise CommandError("No active session; run /start")

        self._state = self._state_machine.rollback(self._state)
        self._state = self._state.touch()
        self._session_manager.persist_state(self._state)
        self._safe_audit(
            "ROLLBACK",
            f"Rollback to {self._state.current_phase.value}",
            {"phase": self._state.current_phase.value},
        )
        return f"Rolled back. Current phase: {self._state.current_phase.value}"

    def _agent_text(self) -> str:
        s = self._state
        if s.active_agent is None:
            return "No active agent."

        info = _agent_info(s.active_agent)
        lines = [
            "Agent:",
            f"- type: {s.active_agent.value}",
            f"- phase: {s.current_phase.value}",
        ]
        if info.get("output"):
            lines.append(f"- output: {info['output']}")
        if info.get("inputs"):
            lines.append("- inputs: " + ", ".join(info["inputs"]))
        return "\n".join(lines)

    def _gate_text(self) -> str:
        gate = self._state.current_gate
        if gate == 0:
            if self._state.current_phase == Phase.PROOF:
                cert_path = self._workdir / "PROOF-CERTIFICATE.md"
                if not cert_path.exists():
                    return "No active gate. Create PROOF-CERTIFICATE.md (run proof) then run gate to finalize."

                before = self._state.current_phase
                self._state = self._state_machine.transition_forward(
                    self._state
                ).touch()
                self._session_manager.persist_state(self._state)
                self._safe_audit(
                    "PHASE_TRANSITION",
                    f"{before.value} -> {self._state.current_phase.value}",
                    {"from": before.value, "to": self._state.current_phase.value},
                )
                return f"Finalized. Current phase: {self._state.current_phase.value}"

            if self._state.current_phase == Phase.COMPLETE:
                return "No active gate. Workflow already complete."

            return f"No active gate (phase {self._state.current_phase.value})."
        result = self._gate_validator.validate_gate(gate)

        self._state = self._state.model_copy(
            update={"gate_status": result.status}
        ).touch()
        self._session_manager.persist_state(self._state)
        self._safe_audit(
            "GATE_VALIDATION",
            f"Gate {gate} {result.status.value} ({result.pass_percentage}%)",
            {
                "gate": gate,
                "status": result.status.value,
                "pass_percentage": result.pass_percentage,
            },
        )

        lines = [f"Gate {gate}: {result.status.value} ({result.pass_percentage}%)"]
        for r in result.criteria:
            status = "PASS" if r.passed else "FAIL"
            msg = "" if r.passed or not r.message else f" - {r.message}"
            lines.append(
                f"- [{status}] {r.criterion.id}: {r.criterion.description}{msg}"
            )

        if result.status == GateStatus.PASSED:
            before = self._state.current_phase
            try:
                self._state = self._state_machine.transition_forward(
                    self._state
                ).touch()
            except Exception as e:
                lines.append(f"\nTransition blocked: {e}")
            else:
                self._session_manager.persist_state(self._state)
                self._safe_audit(
                    "PHASE_TRANSITION",
                    f"{before.value} -> {self._state.current_phase.value}",
                    {"from": before.value, "to": self._state.current_phase.value},
                )
                lines.append(
                    f"\nTransitioned to phase: {self._state.current_phase.value}"
                )

        return "\n".join(lines)

    def _checklist_text(self) -> str:
        total = 0
        passed = 0

        lines: list[str] = []
        for gate_num in sorted(GATE_CHECKLISTS.keys()):
            result = self._gate_validator.validate_gate(gate_num)
            lines.append(
                f"Gate {gate_num}: {result.status.value} ({result.pass_percentage}%)"
            )
            for r in result.criteria:
                status = "PASS" if r.passed else "FAIL"
                msg = "" if r.passed or not r.message else f" - {r.message}"
                lines.append(
                    f"- [{status}] {r.criterion.id}: {r.criterion.description}{msg}"
                )
                total += 1
                passed += 1 if r.passed else 0
            lines.append("")

        overall = int(round(100 * passed / max(1, total)))
        lines.append(f"Overall pass percentage: {overall}%")
        return "\n".join(lines).rstrip()

    def _template_for_artifact(self, artifact_type: ArtifactType) -> str | None:
        return {
            ArtifactType.STRATEGY_SPEC: "strategy-spec.md.j2",
            ArtifactType.LOGIC_MODEL: "logic-model.md.j2",
            ArtifactType.TEST_REPORT: "test-report.md.j2",
            ArtifactType.PROOF_CERTIFICATE: "proof-certificate.md.j2",
        }.get(artifact_type)

    def _maybe_create_skeleton(self, artifact_type: ArtifactType) -> None:
        template_name = self._template_for_artifact(artifact_type)
        if not template_name:
            return

        path = self._artifact_manager.artifact_path(artifact_type)
        if path.exists():
            return

        if not self._artifact_manager.templates.exists(template_name):
            return

        created = self._artifact_manager.ensure_skeleton(
            artifact_type,
            template_name=template_name,
            version="v1.0",
        )
        self._track_artifact(artifact_type, created, version="v1.0")
        self._safe_audit(
            "ARTIFACT_GENERATION",
            f"Created skeleton {created.name}",
            {"artifact": created.name, "version": "v1.0"},
        )

    def _track_artifact(
        self, artifact_type: ArtifactType, path: Path, *, version: str
    ) -> None:
        s = self._state
        existing = {(a.artifact_type, a.file_path, a.version) for a in s.artifacts}
        key = (artifact_type, str(path), version)
        if key in existing:
            return

        ref = ArtifactRef(
            artifact_type=artifact_type,
            file_path=str(path),
            version=version,
        )
        self._state = s.model_copy(update={"artifacts": [*s.artifacts, ref]}).touch()
        self._session_manager.persist_state(self._state)

    def _show_artifact(self, artifact_type: ArtifactType) -> str:
        self._maybe_create_skeleton(artifact_type)
        return self._artifact_manager.load_text(artifact_type)

    def _show_code_artifacts(self) -> str:
        patterns = ["*_MT4.mq4", "*_MT5.mq5", "*_Pine.pine"]
        files: list[Path] = []
        for p in patterns:
            files.extend(self._workdir.glob(p))

        files = sorted({f.resolve() for f in files})
        if not files:
            return "No code artifacts found in working directory."
        return "Code artifacts:\n" + "\n".join(f"- {f.name}" for f in files)

    def _audit_text(self) -> str:
        audit_path = self._workdir / "AUDIT-TRAIL.md"
        trace_path = self._workdir / "TRACEABILITY-MAP.md"

        parts: list[str] = []
        try:
            if not trace_path.exists():
                write_traceability_map(self._workdir)
        except Exception:
            pass

        if trace_path.exists():
            parts.append(trace_path.read_text(encoding="utf-8"))
        else:
            parts.append("TRACEABILITY-MAP.md not found.")

        parts.append("")
        if audit_path.exists():
            parts.append(audit_path.read_text(encoding="utf-8"))
        else:
            parts.append("AUDIT-TRAIL.md not found.")
        return "\n".join(parts).rstrip()

    def _export_package(self) -> str:
        required = [
            "STRATEGY-SPEC.md",
            "LOGIC-MODEL.md",
            "TEST-REPORT.md",
            "PROOF-CERTIFICATE.md",
            "TRACEABILITY-MAP.md",
            "AUDIT-TRAIL.md",
        ]

        trace_path = self._workdir / "TRACEABILITY-MAP.md"
        if not trace_path.exists() and (self._workdir / "STRATEGY-SPEC.md").exists():
            try:
                write_traceability_map(self._workdir)
            except Exception:
                pass

        missing = [fn for fn in required if not (self._workdir / fn).exists()]
        if missing:
            raise CommandError(
                "Missing required artifacts for export:\n"
                + "\n".join(f"- {m}" for m in missing)
            )

        spec_text = (self._workdir / "STRATEGY-SPEC.md").read_text(encoding="utf-8")
        strategy_name = _extract_strategy_name(spec_text) or "strategy"
        version = _extract_version(spec_text) or "v1.0"

        zip_name = f"{strategy_name}_BMAD_{version}.zip"
        zip_path = self._workdir / zip_name

        templates = self._artifact_manager.templates
        readme_body = ""
        if templates.exists("readme.md.j2"):
            readme_body = templates.render(
                "readme.md.j2",
                {
                    "version": version,
                    "created_at": utcnow().isoformat(),
                    "strategy_name": strategy_name,
                },
            )

        code_files: list[Path] = []
        for p in ["*_MT4.mq4", "*_MT5.mq5", "*_Pine.pine"]:
            code_files.extend(self._workdir.glob(p))
        code_files = sorted({p.resolve() for p in code_files})

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for fn in required:
                zf.write(self._workdir / fn, arcname=fn)
            for cf in code_files:
                zf.write(cf, arcname=cf.name)
            if readme_body:
                zf.writestr("README.md", readme_body)

        self._safe_audit("EXPORT", f"Exported deployment package: {zip_name}")
        return f"Exported: {zip_path.name}"

    def _spec_wizard(self) -> str:
        """Interactive STRATEGY-SPEC.md generator."""

        spec_path = self._workdir / ArtifactType.STRATEGY_SPEC.value
        prev_version = None
        if spec_path.exists():
            try:
                prev_version = _extract_version(spec_path.read_text(encoding="utf-8"))
            except Exception:
                prev_version = None

        version = bump_minor(prev_version) if prev_version else "v1.0"
        ts = utcnow()

        strategy_name = input("Strategy name: ").strip() or "TODO"
        overview = input("One-line overview: ").strip() or "TODO"
        instruments = input("Instruments (comma-separated): ").strip() or "TODO"
        timeframes = input("Timeframes (comma-separated): ").strip() or "TODO"
        market_conditions = input("Market conditions: ").strip() or "TODO"

        entry_count = _prompt_int("Number of entry rules", default=1, min_value=1)
        entry_rules = _prompt_rules(entry_count, start_index=1)

        exit_count = _prompt_int("Number of exit rules", default=1, min_value=1)
        exit_rules = _prompt_rules(exit_count, start_index=1 + len(entry_rules))

        risk_management = input("Risk management (free text): ").strip() or "TODO"
        filters = input("Filters (free text): ").strip() or "TODO"
        edge_cases = input("Edge cases (free text): ").strip() or "TODO"

        content = _render_strategy_spec(
            version=version,
            timestamp=ts.isoformat(),
            strategy_name=strategy_name,
            overview=overview,
            instruments=instruments,
            timeframes=timeframes,
            market_conditions=market_conditions,
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            risk_management=risk_management,
            filters=filters,
            edge_cases=edge_cases,
        )

        artifact = Artifact(
            artifact_type=ArtifactType.STRATEGY_SPEC,
            content=content,
            version=version,
            created_at=ts,
            rule_ids=[str(r["rule_id"]) for r in entry_rules + exit_rules],
            metadata={"strategy_name": strategy_name},
        )

        saved = self._artifact_manager.save_artifact(artifact, file_path=spec_path)
        self._track_artifact(ArtifactType.STRATEGY_SPEC, saved, version=version)
        self._safe_audit(
            "ARTIFACT_GENERATION",
            f"Generated {saved.name}",
            {"artifact": saved.name, "version": version},
        )
        return f"Generated {saved.name} ({version})"

    def _code_wizard(self) -> str:
        """Interactive code skeleton generator for MT4/MT5/Pine."""

        spec_path = self._workdir / "STRATEGY-SPEC.md"
        spec_text = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""

        default_name = _extract_strategy_name(spec_text) or "strategy"
        strategy_name = (
            input(f"Strategy name [{default_name}]: ").strip() or default_name
        )
        strategy_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", strategy_name).strip("_")
        if not strategy_name:
            strategy_name = "strategy"

        logic_path = self._workdir / "LOGIC-MODEL.md"
        version = None
        if logic_path.exists():
            version = _extract_version(logic_path.read_text(encoding="utf-8"))
        if not version and spec_text:
            version = _extract_version(spec_text)
        version = version or "v1.0"

        platforms_raw = input("Platforms (MT4, MT5, Pine, ALL) [ALL]: ").strip()
        platforms = _parse_platforms(platforms_raw or "ALL")

        rule_ids: list[str] = []
        variables: list[str] = []
        if logic_path.exists():
            logic_text = logic_path.read_text(encoding="utf-8")
            rule_ids = sorted(set(re.findall(r"\bR-\d{3}\b", logic_text)))
            variables = sorted(_extract_variable_names_from_logic(logic_text))

        ctx = {
            "strategy_name": strategy_name,
            "version": version,
            "created_at": utcnow().isoformat(),
            "rule_ids": rule_ids,
            "variables": variables,
        }

        created: list[str] = []
        for plat in platforms:
            template_name, out_name, art_type = _platform_template(plat, strategy_name)
            if not self._artifact_manager.templates.exists(template_name):
                raise CommandError(f"Missing template: templates/{template_name}")

            body = self._artifact_manager.templates.render(template_name, ctx)
            artifact = Artifact(
                artifact_type=art_type,
                content=body,
                version=version,
                created_at=utcnow(),
                rule_ids=rule_ids,
                metadata={"strategy_name": strategy_name, "platform": plat},
            )

            out_path = self._workdir / out_name
            saved = self._artifact_manager.save_artifact(artifact, file_path=out_path)
            self._track_artifact(art_type, saved, version=version)
            created.append(saved.name)

        self._safe_audit(
            "ARTIFACT_GENERATION",
            "Generated code skeletons",
            {"files": ", ".join(created), "version": version},
        )
        return "Generated:\n" + "\n".join(f"- {n}" for n in created)

    def _logic_wizard(self) -> str:
        """Generate a LOGIC-MODEL.md skeleton populated with Rule_IDs."""

        spec_path = self._workdir / "STRATEGY-SPEC.md"
        if not spec_path.exists():
            raise CommandError(
                "Missing STRATEGY-SPEC.md (run spec or spec-wizard first)"
            )

        spec_text = spec_path.read_text(encoding="utf-8")
        rule_ids = sorted(set(re.findall(r"\bR-\d{3}\b", spec_text)))
        if not rule_ids:
            raise CommandError("No Rule_IDs found in STRATEGY-SPEC.md")

        logic_path = self._workdir / "LOGIC-MODEL.md"
        prev_version = None
        if logic_path.exists():
            prev_version = _extract_version(logic_path.read_text(encoding="utf-8"))
        version = bump_minor(prev_version) if prev_version else "v1.0"

        ts = utcnow().isoformat()
        content = _render_logic_model(version=version, timestamp=ts, rule_ids=rule_ids)

        artifact = Artifact(
            artifact_type=ArtifactType.LOGIC_MODEL,
            content=content,
            version=version,
            created_at=utcnow(),
            rule_ids=rule_ids,
            metadata={},
        )

        saved = self._artifact_manager.save_artifact(artifact, file_path=logic_path)
        self._track_artifact(ArtifactType.LOGIC_MODEL, saved, version=version)
        self._safe_audit(
            "ARTIFACT_GENERATION",
            f"Generated {saved.name}",
            {"artifact": saved.name, "version": version},
        )
        return f"Generated {saved.name} ({version})"

    def _test_wizard(self) -> str:
        """Generate a TEST-REPORT.md with required metric placeholders."""

        report_path = self._workdir / "TEST-REPORT.md"
        prev_version = None
        if report_path.exists():
            prev_version = _extract_version(report_path.read_text(encoding="utf-8"))
        version = bump_minor(prev_version) if prev_version else "v1.0"

        unit_pass = _prompt_yes_no("Unit tests passed", default=True)
        integ_pass = _prompt_yes_no("Integration tests passed", default=True)
        total_trades = _prompt_int(
            "Total_Trades",
            default=self._config.min_backtest_trades,
            min_value=0,
        )
        walk_forward = _prompt_yes_no("Walk-Forward Analysis performed", default=True)
        monte_carlo = _prompt_yes_no("Monte Carlo Simulation performed", default=True)

        content = _render_test_report(
            version=version,
            timestamp=utcnow().isoformat(),
            unit_pass=unit_pass,
            integration_pass=integ_pass,
            total_trades=total_trades,
            walk_forward=walk_forward,
            monte_carlo=monte_carlo,
        )

        artifact = Artifact(
            artifact_type=ArtifactType.TEST_REPORT,
            content=content,
            version=version,
            created_at=utcnow(),
            rule_ids=[],
            metadata={},
        )

        saved = self._artifact_manager.save_artifact(artifact, file_path=report_path)
        self._track_artifact(ArtifactType.TEST_REPORT, saved, version=version)
        self._safe_audit(
            "ARTIFACT_GENERATION",
            f"Generated {saved.name}",
            {"artifact": saved.name, "version": version},
        )
        return f"Generated {saved.name} ({version})"

    def _safe_audit(
        self, entry_type: str, description: str, details: dict[str, Any] | None = None
    ) -> None:
        try:
            self._audit_trail.record(entry_type, description, details)
        except Exception:
            # Audit trail should never block command execution.
            pass


def _extract_version(text: str) -> str | None:
    for line in text.splitlines():
        m = re.match(
            r"^\*\*Version:\*\*\s*(v\d+\.\d+)\s*$", line.strip(), re.IGNORECASE
        )
        if m:
            return m.group(1)
    return None


def _extract_strategy_name(text: str) -> str | None:
    # Accept either "Strategy_Name: X" or "- Strategy_Name: X".
    for line in text.splitlines():
        m = re.match(
            r"^\s*-?\s*Strategy_Name\s*:\s*(.+)\s*$", line.strip(), re.IGNORECASE
        )
        if m:
            name = m.group(1).strip()
            name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_")
            return name or None
    return None


def _prompt_int(label: str, *, default: int, min_value: int = 0) -> int:
    while True:
        raw = input(f"{label} [{default}]: ").strip()
        if not raw:
            return default
        try:
            v = int(raw)
        except ValueError:
            print("Please enter an integer.")
            continue
        if v < min_value:
            print(f"Value must be >= {min_value}.")
            continue
        return v


def _prompt_rules(count: int, *, start_index: int) -> list[dict[str, object]]:
    rules: list[dict[str, object]] = []
    for i in range(count):
        idx = start_index + i
        rid = f"R-{idx:03d}"
        desc = input(f"Rule {rid} description: ").strip() or "TODO"
        cond_raw = input(f"Rule {rid} conditions (separate with ';'): ").strip()
        ex_raw = input(f"Rule {rid} examples (separate with ';'): ").strip()

        conditions = [c.strip() for c in cond_raw.split(";") if c.strip()] or ["TODO"]
        examples = [e.strip() for e in ex_raw.split(";") if e.strip()] or ["TODO"]

        rules.append(
            {
                "rule_id": rid,
                "description": desc,
                "conditions": conditions,
                "examples": examples,
            }
        )
    return rules


def _render_strategy_spec(
    *,
    version: str,
    timestamp: str,
    strategy_name: str,
    overview: str,
    instruments: str,
    timeframes: str,
    market_conditions: str,
    entry_rules: list[dict[str, object]],
    exit_rules: list[dict[str, object]],
    risk_management: str,
    filters: str,
    edge_cases: str,
) -> str:
    lines: list[str] = [
        "# STRATEGY-SPEC",
        "",
        f"**Version:** {version}",
        f"**Timestamp:** {timestamp}",
        "",
        "## Overview",
        f"- Strategy_Name: {strategy_name}",
        f"- Summary: {overview}",
        "",
        "## Market_Context",
        f"- Instruments: {instruments}",
        f"- Timeframes: {timeframes}",
        f"- Market_Conditions: {market_conditions}",
        "",
        "## Entry_Rules",
    ]

    for r in entry_rules:
        rid = str(r["rule_id"])
        desc = str(r["description"])
        lines.append(f"### {rid} - {desc}")
        lines.append("- Conditions:")
        for c in r["conditions"]:  # type: ignore[index]
            lines.append(f"  - {c}")
        lines.append("- Examples:")
        for e in r["examples"]:  # type: ignore[index]
            lines.append(f"  - {e}")
        lines.append("")

    lines.append("## Exit_Rules")
    for r in exit_rules:
        rid = str(r["rule_id"])
        desc = str(r["description"])
        lines.append(f"### {rid} - {desc}")
        lines.append("- Conditions:")
        for c in r["conditions"]:  # type: ignore[index]
            lines.append(f"  - {c}")
        lines.append("- Examples:")
        for e in r["examples"]:  # type: ignore[index]
            lines.append(f"  - {e}")
        lines.append("")

    lines.extend(
        [
            "## Risk_Management",
            f"- {risk_management}",
            "",
            "## Filters",
            f"- {filters}",
            "",
            "## Edge_Cases",
            f"- {edge_cases}",
            "",
        ]
    )

    return "\n".join(lines)


def _parse_platforms(raw: str) -> list[str]:
    raw = raw.strip().upper()
    if not raw:
        return ["MT4", "MT5", "PINE"]
    if raw in {"ALL", "*"}:
        return ["MT4", "MT5", "PINE"]

    parts = [
        p.strip() for p in raw.replace("PINE_SCRIPT", "PINE").split(",") if p.strip()
    ]
    out: list[str] = []
    for p in parts:
        if p in {"MT4", "MQL4"}:
            out.append("MT4")
        elif p in {"MT5", "MQL5"}:
            out.append("MT5")
        elif p in {"PINE", "PINESCRIPT", "PINE-SCRIPT"}:
            out.append("PINE")
        elif p in {"ALL", "*"}:
            out.extend(["MT4", "MT5", "PINE"])
        else:
            raise CommandError(f"Unknown platform: {p}")

    # Unique, keep order.
    seen: set[str] = set()
    unique: list[str] = []
    for p in out:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def _platform_template(plat: str, strategy_name: str) -> tuple[str, str, ArtifactType]:
    plat = plat.strip().upper()
    if plat == "MT4":
        return (
            "mt4-template.mq4.j2",
            f"{strategy_name}_MT4.mq4",
            ArtifactType.SOURCE_CODE_MT4,
        )
    if plat == "MT5":
        return (
            "mt5-template.mq5.j2",
            f"{strategy_name}_MT5.mq5",
            ArtifactType.SOURCE_CODE_MT5,
        )
    if plat == "PINE":
        return (
            "pine-template.pine.j2",
            f"{strategy_name}_Pine.pine",
            ArtifactType.SOURCE_CODE_PINE,
        )
    raise CommandError(f"Unknown platform: {plat}")


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


def _render_logic_model(*, version: str, timestamp: str, rule_ids: list[str]) -> str:
    lines: list[str] = [
        "# LOGIC-MODEL",
        "",
        f"**Version:** {version}",
        f"**Timestamp:** {timestamp}",
        "",
        "## Mathematical_Formulas",
    ]
    for rid in rule_ids:
        lines.append(f"- {rid}: TODO")

    lines.extend(
        [
            "",
            "## State_Machine",
            "- TODO: Describe states and transitions.",
            "",
            "## Pseudo_Code",
            "```text",
            "TODO: Write BMAD_PC pseudo-code here.",
        ]
    )
    for rid in rule_ids:
        lines.append(f"// Rule_ID: {rid} - TODO")
        lines.append("IF condition THEN")
        lines.append("    // TODO")
        lines.append("ENDIF")
        lines.append("")
    lines.extend(
        [
            "```",
            "",
            "## Truth_Tables",
            "- TODO",
            "",
            "## Variable_Definitions",
            "- TODO",
            "",
            "| name | type | range | unit | initial_value | is_input |",
            "|------|------|-------|------|---------------|----------|",
            "| foo  | FLOAT| [0,1] | none | 0             | false    |",
            "",
        ]
    )
    return "\n".join(lines)


def _prompt_yes_no(label: str, *, default: bool) -> bool:
    suffix = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{label}? [{suffix}]: ").strip().lower()
        if not raw:
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Please answer y or n.")


def _render_test_report(
    *,
    version: str,
    timestamp: str,
    unit_pass: bool,
    integration_pass: bool,
    total_trades: int,
    walk_forward: bool,
    monte_carlo: bool,
) -> str:
    def _pf(v: bool) -> str:
        return "PASS" if v else "FAIL"

    metrics = [
        ("Total_Trades", str(total_trades)),
        ("Win_Rate", "TODO"),
        ("Profit_Factor", "TODO"),
        ("Sharpe_Ratio", "TODO"),
        ("Maximum_Drawdown", "TODO"),
        ("Average_Win", "TODO"),
        ("Average_Loss", "TODO"),
        ("Largest_Win", "TODO"),
        ("Largest_Loss", "TODO"),
        ("Consecutive_Wins", "TODO"),
        ("Consecutive_Losses", "TODO"),
        ("Average_Trade_Duration", "TODO"),
        ("Total_Return", "TODO"),
        ("Annualized_Return", "TODO"),
        ("Risk_Reward_Ratio", "TODO"),
        ("Recovery_Factor", "TODO"),
        ("Expectancy", "TODO"),
        ("Calmar_Ratio", "TODO"),
    ]

    lines: list[str] = [
        "# TEST-REPORT",
        "",
        f"**Version:** {version}",
        f"**Timestamp:** {timestamp}",
        "",
        "## Unit_Test_Results",
        f"- Unit tests: {_pf(unit_pass)}",
        "",
        "## Integration_Test_Results",
        f"- Integration tests: {_pf(integration_pass)}",
        "",
        "## Backtest_Results",
    ]
    for k, v in metrics:
        lines.append(f"- {k}: {v}")

    lines.extend(
        [
            "",
            "## Robustness_Test_Results",
            f"- Walk-Forward Analysis: {_pf(walk_forward)}",
            f"- Monte Carlo Simulation: {_pf(monte_carlo)}",
            "",
            "## Summary",
            "- TODO",
            "",
        ]
    )
    return "\n".join(lines)


def _agent_info(agent_type: AgentType) -> dict[str, Any]:
    return {
        AgentType.ANALYST: {
            "inputs": [],
            "output": ArtifactType.STRATEGY_SPEC.value,
        },
        AgentType.QUANT: {
            "inputs": [ArtifactType.STRATEGY_SPEC.value],
            "output": ArtifactType.LOGIC_MODEL.value,
        },
        AgentType.CODER: {
            "inputs": [ArtifactType.LOGIC_MODEL.value],
            "output": "<platform code files>",
        },
        AgentType.TESTER: {
            "inputs": ["<platform code files>"],
            "output": ArtifactType.TEST_REPORT.value,
        },
        AgentType.AUDITOR: {
            "inputs": [ArtifactType.TEST_REPORT.value],
            "output": ArtifactType.PROOF_CERTIFICATE.value,
        },
    }.get(agent_type, {})


def _next_step_hint(phase: Phase) -> str:
    return {
        Phase.IDLE: "Run start",
        Phase.SPEC: "Edit STRATEGY-SPEC.md (or run spec) then run gate",
        Phase.LOGIC: "Edit LOGIC-MODEL.md (or run logic) then run gate",
        Phase.CODE: "Add code files (*_MT4.mq4, *_MT5.mq5, *_Pine.pine) then run gate",
        Phase.TEST: "Create TEST-REPORT.md (or run test) then run gate",
        Phase.PROOF: "Create PROOF-CERTIFICATE.md (or run proof) then export",
        Phase.COMPLETE: "Run export",
    }[phase]
