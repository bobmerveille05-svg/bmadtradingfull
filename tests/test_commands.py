from __future__ import annotations

import pytest

from bmadts.exceptions import CommandError
from bmadts.orchestrator.commands import Command, parse_command


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("/status", Command.STATUS),
        ("status", Command.STATUS),
        ("STATUS", Command.STATUS),
        ("/start", Command.START),
        ("rollback", Command.ROLLBACK),
        ("/checklist", Command.CHECKLIST),
    ],
)
def test_parse_command_recognizes_commands(raw, expected):
    cmd, args = parse_command(raw)
    assert cmd == expected
    assert args == []


def test_parse_command_rejects_empty():
    with pytest.raises(CommandError):
        parse_command(" ")


def test_parse_command_rejects_unknown():
    with pytest.raises(CommandError):
        parse_command("/nope")
