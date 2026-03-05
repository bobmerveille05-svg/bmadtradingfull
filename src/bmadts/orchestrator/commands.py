from __future__ import annotations

import shlex
from enum import Enum

from bmadts.exceptions import CommandError


class Command(str, Enum):
    START = "/start"
    STATUS = "/status"
    GATE = "/gate"
    ROLLBACK = "/rollback"
    AGENT = "/agent"
    SPEC = "/spec"
    LOGIC = "/logic"
    CODE = "/code"
    TEST = "/test"
    PROOF = "/proof"
    EXPORT = "/export"
    AUDIT = "/audit"
    CHECKLIST = "/checklist"
    SPEC_WIZARD = "/spec-wizard"
    CODE_WIZARD = "/code-wizard"
    LOGIC_WIZARD = "/logic-wizard"
    TEST_WIZARD = "/test-wizard"
    VERIFY = "/verify"
    BMAD_HELP = "/bmad-help"
    PARTY = "/party"
    HELP = "/help"
    EXIT = "/exit"
    QUIT = "/quit"


def parse_command(text: str) -> tuple[Command, list[str]]:
    parts = shlex.split(text.strip())
    if not parts:
        raise CommandError("Empty command")

    head = parts[0].strip()
    if not head:
        raise CommandError("Empty command")

    head_lc = head.lower().replace("\\", "/")
    # MSYS (Git Bash) often rewrites "/status" into a Windows path like
    # "C:/Program Files/Git/status". Recover the intended command by
    # taking the basename.
    head_lc = head_lc.rsplit("/", 1)[-1]
    if not head_lc.startswith("/"):
        head_lc = "/" + head_lc

    for cmd in Command:
        if head_lc == cmd.value:
            return cmd, parts[1:]
    raise CommandError(f"Unknown command: {parts[0]}")
