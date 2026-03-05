from __future__ import annotations

import re


_VERSION_RE = re.compile(r"^v(?P<major>\d+)\.(?P<minor>\d+)$")


def parse_version(version: str) -> tuple[int, int]:
    m = _VERSION_RE.match(version.strip())
    if not m:
        raise ValueError(f"Invalid version: {version}")
    return int(m.group("major")), int(m.group("minor"))


def format_version(major: int, minor: int) -> str:
    if major < 0 or minor < 0:
        raise ValueError("major/minor must be >= 0")
    return f"v{major}.{minor}"


def bump_minor(version: str) -> str:
    major, minor = parse_version(version)
    return format_version(major, minor + 1)
