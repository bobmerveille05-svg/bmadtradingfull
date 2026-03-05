from __future__ import annotations

from bmadts.models.session import SessionState
from bmadts.orchestrator.session_manager import SessionManager


def test_persist_and_restore_round_trip(tmp_path):
    session_file = tmp_path / ".bmad-session.json"
    mgr = SessionManager(session_file)

    state = SessionState()
    mgr.persist_state(state)
    restored = mgr.restore_state()

    assert restored.model_dump() == state.model_dump()


def test_session_exists(tmp_path):
    session_file = tmp_path / ".bmad-session.json"
    mgr = SessionManager(session_file)
    assert mgr.session_exists() is False

    mgr.persist_state(SessionState())
    assert mgr.session_exists() is True
