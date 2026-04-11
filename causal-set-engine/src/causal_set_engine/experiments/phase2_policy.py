"""Legacy compatibility shim for phase-2 gate policy.

Prefer importing from ``causal_set_engine.policies.policy_gate``.
"""

from causal_set_engine.policies.policy_gate import (
    Phase2GateDecision,
    Phase2GateInput,
    Phase2GateThresholds,
    evaluate_phase2_gate,
)

__all__ = [
    "Phase2GateThresholds",
    "Phase2GateInput",
    "Phase2GateDecision",
    "evaluate_phase2_gate",
]
