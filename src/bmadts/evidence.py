from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from bmadts._time import utcnow


class EvidenceType(str, Enum):
    """What kind of proof a gate criterion accepts."""

    FILE_EXISTS = "file_exists"
    FILE_HASH = "file_hash"
    NUMERIC_THRESHOLD = "numeric_threshold"
    LOG_CONTAINS = "log_contains"
    EXTERNAL_REPORT = "external_report"
    COMPUTED = "computed"


class EvidenceStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class Evidence:
    """A single piece of machine-verifiable proof."""

    criterion_id: str
    evidence_type: EvidenceType
    description: str
    status: EvidenceStatus
    value: str | float | int | None = None
    threshold: str | float | int | None = None
    source_path: str | None = None
    source_hash: str | None = None
    timestamp: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict:
        return {
            "criterion_id": self.criterion_id,
            "type": self.evidence_type.value,
            "status": self.status.value,
            "description": self.description,
            "value": self.value,
            "threshold": self.threshold,
            "source": self.source_path,
            "hash": self.source_hash,
            "timestamp": self.timestamp.isoformat(),
        }


def hash_file(path: Path) -> str:
    """SHA-256 hash of a file."""

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_file_evidence(criterion_id: str, description: str, path: Path) -> Evidence:
    """Verify a file exists; if it does, attach a SHA-256 hash."""

    if not path.exists():
        return Evidence(
            criterion_id=criterion_id,
            evidence_type=EvidenceType.FILE_EXISTS,
            description=description,
            status=EvidenceStatus.UNVERIFIED,
            source_path=str(path),
        )

    return Evidence(
        criterion_id=criterion_id,
        evidence_type=EvidenceType.FILE_HASH,
        description=description,
        status=EvidenceStatus.VERIFIED,
        value=str(path),
        source_path=str(path),
        source_hash=hash_file(path),
    )


def verify_log_contains(
    criterion_id: str,
    description: str,
    *,
    log_path: Path,
    expected_substring: str,
    ignore_case: bool = True,
) -> Evidence:
    if not log_path.exists():
        return Evidence(
            criterion_id=criterion_id,
            evidence_type=EvidenceType.LOG_CONTAINS,
            description=description,
            status=EvidenceStatus.UNVERIFIED,
            threshold=expected_substring,
            source_path=str(log_path),
        )

    text = log_path.read_text(encoding="utf-8", errors="replace")
    haystack = text.lower() if ignore_case else text
    needle = expected_substring.lower() if ignore_case else expected_substring
    ok = needle in haystack

    return Evidence(
        criterion_id=criterion_id,
        evidence_type=EvidenceType.LOG_CONTAINS,
        description=description,
        status=EvidenceStatus.VERIFIED if ok else EvidenceStatus.FAILED,
        value=expected_substring if ok else None,
        threshold=expected_substring,
        source_path=str(log_path),
        source_hash=hash_file(log_path),
    )


def verify_numeric_threshold(
    criterion_id: str,
    description: str,
    *,
    value: float | int | None,
    threshold: float | int,
    operator: str = ">=",
) -> Evidence:
    """Verify a numeric value satisfies a threshold.

    If value is None, the criterion is UNVERIFIED (no computed evidence).
    """

    if value is None:
        return Evidence(
            criterion_id=criterion_id,
            evidence_type=EvidenceType.NUMERIC_THRESHOLD,
            description=description,
            status=EvidenceStatus.UNVERIFIED,
            threshold=threshold,
        )

    ops = {
        ">=": lambda v, t: v >= t,
        "<=": lambda v, t: v <= t,
        ">": lambda v, t: v > t,
        "<": lambda v, t: v < t,
        "==": lambda v, t: v == t,
        "!=": lambda v, t: v != t,
    }
    if operator not in ops:
        raise ValueError(f"Unsupported operator: {operator}")

    ok = ops[operator](value, threshold)
    return Evidence(
        criterion_id=criterion_id,
        evidence_type=EvidenceType.NUMERIC_THRESHOLD,
        description=description,
        status=EvidenceStatus.VERIFIED if ok else EvidenceStatus.FAILED,
        value=value,
        threshold=threshold,
    )
