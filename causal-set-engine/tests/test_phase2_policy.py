"""Deterministic tests for strict phase-2a policy gate."""

from causal_set_engine.experiments.decision_metrics import DiagnosticQuality
from causal_set_engine.experiments.phase2_policy import Phase2GateInput, evaluate_phase2_gate


def test_phase2_gate_go_with_primary_diagnostic_and_robust_coverage() -> None:
    ranked = [
        DiagnosticQuality(
            metric="dimension_estimate",
            mean_difference_abs=0.7,
            effect_size_abs=1.2,
            interval_separation=0.7,
            sign_consistency=0.9,
            trend_consistency=0.8,
            usefulness_score=0.8,
            band="strong discriminator",
        )
    ]

    decision = evaluate_phase2_gate(
        Phase2GateInput(
            ranked_diagnostics=ranked,
            null_model_count=2,
            seeds_per_model=8,
            n_values_count=2,
        )
    )

    assert decision.go is True
    assert decision.primary_metrics == ("dimension_estimate",)
    assert decision.failures == ()


def test_phase2_gate_no_go_when_coverage_or_quality_is_missing() -> None:
    ranked = [
        DiagnosticQuality(
            metric="interval_mean",
            mean_difference_abs=0.2,
            effect_size_abs=0.4,
            interval_separation=0.2,
            sign_consistency=0.6,
            trend_consistency=0.5,
            usefulness_score=0.3,
            band="exploratory signal",
        )
    ]

    decision = evaluate_phase2_gate(
        Phase2GateInput(
            ranked_diagnostics=ranked,
            null_model_count=1,
            seeds_per_model=4,
            n_values_count=1,
        )
    )

    assert decision.go is False
    assert decision.primary_metrics == ()
    assert set(decision.failures) == {
        "insufficient-primary-diagnostics",
        "insufficient-null-model-coverage",
        "insufficient-seed-coverage",
        "insufficient-size-trend-coverage",
    }
