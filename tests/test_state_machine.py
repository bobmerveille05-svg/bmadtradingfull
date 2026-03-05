from __future__ import annotations

import pytest

from bmadts.exceptions import GateNotPassedError, InvalidTransitionError
from bmadts.models.enums import GateStatus, Phase
from bmadts.models.session import SessionState
from bmadts.orchestrator.state_machine import StateMachine


def test_forward_transition_requires_gate_passed():
    sm = StateMachine()
    state = SessionState(current_phase=Phase.SPEC, gate_status=GateStatus.PENDING)

    with pytest.raises(GateNotPassedError):
        sm.transition_forward(state)


def test_forward_transition_from_idle_allowed():
    sm = StateMachine()
    state = SessionState(current_phase=Phase.IDLE, gate_status=GateStatus.PENDING)
    next_state = sm.transition_forward(state)
    assert next_state.current_phase == Phase.SPEC


def test_forward_transition_from_proof_allowed_without_gate():
    sm = StateMachine()
    state = SessionState(current_phase=Phase.PROOF, gate_status=GateStatus.PENDING)
    next_state = sm.transition_forward(state)
    assert next_state.current_phase == Phase.COMPLETE


def test_rollback_moves_to_previous_phase_and_resets_gate():
    sm = StateMachine()
    state = SessionState(current_phase=Phase.CODE, gate_status=GateStatus.FAILED)
    rolled = sm.rollback(state)
    assert rolled.current_phase == Phase.LOGIC
    assert rolled.gate_status == GateStatus.PENDING


def test_rollback_from_spec_invalid():
    sm = StateMachine()
    state = SessionState(current_phase=Phase.SPEC)
    with pytest.raises(InvalidTransitionError):
        sm.rollback(state)
