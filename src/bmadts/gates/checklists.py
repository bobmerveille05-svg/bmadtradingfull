from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GateCriterion:
    id: str
    description: str


GATE_CHECKLISTS: dict[int, list[GateCriterion]] = {
    1: [
        GateCriterion("G1-01", "All mandatory sections present in STRATEGY-SPEC"),
        GateCriterion("G1-02", "Each rule has a unique Rule_ID"),
        GateCriterion("G1-03", "Entry rules clearly defined"),
        GateCriterion("G1-04", "Exit rules clearly defined"),
        GateCriterion("G1-05", "Risk management rules specified"),
        GateCriterion("G1-06", "Market context documented"),
        GateCriterion("G1-07", "Edge cases identified"),
        GateCriterion("G1-08", "Examples provided for key rules"),
        GateCriterion("G1-09", "Artifact saved with correct filename"),
    ],
    2: [
        GateCriterion(
            "G2-01", "All rules from STRATEGY-SPEC represented in LOGIC-MODEL"
        ),
        GateCriterion("G2-02", "All formulas mathematically valid"),
        GateCriterion("G2-03", "State machine has no unreachable states"),
        GateCriterion("G2-04", "All variables defined with types and ranges"),
        GateCriterion("G2-05", "BMAD_PC pseudo-code syntactically correct"),
        GateCriterion("G2-06", "Truth tables cover all input combinations"),
        GateCriterion("G2-07", "Artifact saved with correct filename"),
    ],
    3: [
        GateCriterion("G3-01", "Code compiles without errors on target platform"),
        GateCriterion(
            "G3-02", "All Rule_IDs from LOGIC-MODEL present in code comments"
        ),
        GateCriterion("G3-03", "Code structure follows standardized template"),
        GateCriterion("G3-04", "Error handling implemented"),
        GateCriterion("G3-05", "All variables from LOGIC-MODEL declared in code"),
        GateCriterion("G3-06", "Artifact saved with correct filename"),
    ],
    4: [
        GateCriterion("G4-01", "All unit tests passed"),
        GateCriterion("G4-02", "All integration tests passed"),
        GateCriterion("G4-03", "Backtest includes at least min trades"),
        GateCriterion("G4-04", "All 18 backtest metrics calculated"),
        GateCriterion("G4-05", "Walk-Forward Analysis performed"),
        GateCriterion("G4-06", "Monte Carlo Simulation performed"),
        GateCriterion("G4-07", "Artifact saved with correct filename"),
    ],
}
