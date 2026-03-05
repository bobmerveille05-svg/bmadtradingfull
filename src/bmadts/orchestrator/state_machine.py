from __future__ import annotations

from bmadts.exceptions import GateNotPassedError, InvalidTransitionError
from bmadts.models.enums import AgentType, GateStatus, Phase
from bmadts.models.session import SessionState


_PHASE_AGENT: dict[Phase, AgentType | None] = {
    Phase.IDLE: None,
    Phase.SPEC: AgentType.ANALYST,
    Phase.LOGIC: AgentType.QUANT,
    Phase.CODE: AgentType.CODER,
    Phase.TEST: AgentType.TESTER,
    Phase.PROOF: AgentType.AUDITOR,
    Phase.COMPLETE: None,
}


_ROLLBACK_TARGET: dict[Phase, Phase] = {
    Phase.LOGIC: Phase.SPEC,
    Phase.CODE: Phase.LOGIC,
    Phase.TEST: Phase.CODE,
    Phase.PROOF: Phase.TEST,
    Phase.COMPLETE: Phase.PROOF,
}


_FORWARD_TARGET: dict[Phase, Phase] = {
    Phase.IDLE: Phase.SPEC,
    Phase.SPEC: Phase.LOGIC,
    Phase.LOGIC: Phase.CODE,
    Phase.CODE: Phase.TEST,
    Phase.TEST: Phase.PROOF,
    Phase.PROOF: Phase.COMPLETE,
}


def _gate_for_phase(phase: Phase) -> int:
    return {
        Phase.IDLE: 0,
        Phase.SPEC: 1,
        Phase.LOGIC: 2,
        Phase.CODE: 3,
        Phase.TEST: 4,
        Phase.PROOF: 0,
        Phase.COMPLETE: 0,
    }[phase]


class StateMachine:
    def transition_forward(self, state: SessionState) -> SessionState:
        if state.current_phase not in _FORWARD_TARGET:
            raise InvalidTransitionError(
                f"No forward transition from {state.current_phase}"
            )

        target = _FORWARD_TARGET[state.current_phase]
        if (
            _gate_for_phase(state.current_phase) > 0
            and state.gate_status != GateStatus.PASSED
        ):
            raise GateNotPassedError(f"Gate not passed for {state.current_phase}")

        return self._enter_phase(state, target)

    def rollback(self, state: SessionState) -> SessionState:
        if state.current_phase not in _ROLLBACK_TARGET:
            raise InvalidTransitionError(
                f"No rollback transition from {state.current_phase}"
            )

        target = _ROLLBACK_TARGET[state.current_phase]
        rolled = state.model_copy(
            update={
                "current_phase": target,
                "gate_status": GateStatus.PENDING,
                "current_gate": _gate_for_phase(target),
                "active_agent": _PHASE_AGENT[target],
            }
        )
        return rolled

    def _enter_phase(self, state: SessionState, phase: Phase) -> SessionState:
        return state.model_copy(
            update={
                "current_phase": phase,
                "gate_status": GateStatus.PENDING,
                "current_gate": _gate_for_phase(phase),
                "active_agent": _PHASE_AGENT[phase],
            }
        )
