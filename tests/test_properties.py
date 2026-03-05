from __future__ import annotations

import tempfile
from pathlib import Path
from datetime import timezone

from hypothesis import given, settings, strategies as st

from bmadts.models.enums import AgentType, GateStatus, Phase
from bmadts.models.session import SessionState
from bmadts.orchestrator.session_manager import SessionManager
from bmadts.orchestrator.state_machine import StateMachine


def _aware_datetimes():
    return st.datetimes(timezones=st.just(timezone.utc))


@given(
    phase=st.sampled_from(list(Phase)),
    gate_status=st.sampled_from(list(GateStatus)),
)
def test_property_phase_and_gate_status_validity(phase, gate_status):
    state = SessionState(current_phase=phase, gate_status=gate_status)
    assert state.current_phase in Phase
    assert state.gate_status in GateStatus


@given(
    phase=st.sampled_from(
        [Phase.LOGIC, Phase.CODE, Phase.TEST, Phase.PROOF, Phase.COMPLETE]
    ),
    gate_status=st.sampled_from(list(GateStatus)),
)
def test_property_rollback_resets_gate_status(phase, gate_status):
    sm = StateMachine()
    state = SessionState(current_phase=phase, gate_status=gate_status)
    rolled = sm.rollback(state)
    assert rolled.gate_status == GateStatus.PENDING
    assert rolled.current_phase in Phase


@given(
    current_phase=st.sampled_from(list(Phase)),
    gate_status=st.sampled_from(list(GateStatus)),
    current_gate=st.integers(min_value=0, max_value=4),
    active_agent=st.one_of(st.none(), st.sampled_from(list(AgentType))),
    language=st.sampled_from(["en", "fr"]),
    created_at=_aware_datetimes(),
    updated_at=_aware_datetimes(),
)
@settings(deadline=None)
def test_property_session_persistence_round_trip(
    current_phase,
    gate_status,
    current_gate,
    active_agent,
    language,
    created_at,
    updated_at,
):
    with tempfile.TemporaryDirectory() as td:
        mgr = SessionManager(Path(td) / ".bmad-session.json")
        state = SessionState(
            current_phase=current_phase,
            gate_status=gate_status,
            current_gate=current_gate,
            active_agent=active_agent,
            language=language,
            created_at=created_at,
            updated_at=updated_at,
        )

        mgr.persist_state(state)
        restored = mgr.restore_state()
        assert restored.model_dump() == state.model_dump()


def test_property_session_id_uniqueness():
    ids = {SessionState().session_id for _ in range(50)}
    assert len(ids) == 50
