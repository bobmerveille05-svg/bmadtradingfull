from __future__ import annotations

from enum import Enum


class Phase(str, Enum):
    IDLE = "IDLE"
    SPEC = "SPEC"
    LOGIC = "LOGIC"
    CODE = "CODE"
    TEST = "TEST"
    PROOF = "PROOF"
    COMPLETE = "COMPLETE"


class GateStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    PASSED = "PASSED"
    FAILED = "FAILED"


class AgentType(str, Enum):
    ANALYST = "ANALYST"
    QUANT = "QUANT"
    CODER = "CODER"
    TESTER = "TESTER"
    AUDITOR = "AUDITOR"


class ArtifactType(str, Enum):
    STRATEGY_SPEC = "STRATEGY-SPEC.md"
    LOGIC_MODEL = "LOGIC-MODEL.md"
    SOURCE_CODE_MT4 = "MT4.mq4"
    SOURCE_CODE_MT5 = "MT5.mq5"
    SOURCE_CODE_PINE = "Pine.pine"
    TEST_REPORT = "TEST-REPORT.md"
    PROOF_CERTIFICATE = "PROOF-CERTIFICATE.md"
    TRACEABILITY_MAP = "TRACEABILITY-MAP.md"
    AUDIT_TRAIL = "AUDIT-TRAIL.md"
    README = "README.md"
