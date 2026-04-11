"""Deterministic tests for the policy gate."""

from causal_set_engine.evaluation.scoring import DiagnosticQuality
from causal_set_engine.policies.policy_gate import PolicyGateInput, evaluate_policy_gate


def test_policy_gate_go_with_primary_diagnostic_and_robust_coverage() -> None:
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

    decision = evaluate_policy_gate(
        PolicyGateInput(
            ranked_diagnostics=ranked,
            null_model_count=2,
            seeds_per_model=8,
            n_values_count=2,
        )
    )

    assert decision.go is True
    assert decision.primary_metrics == ("dimension_estimate",)
    assert decision.failures == ()


def test_policy_gate_no_go_when_coverage_or_quality_is_missing() -> None:
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

    decision = evaluate_policy_gate(
        PolicyGateInput(
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

