"""Regression-style test for phase-2a probe output shape."""

from causal_set_engine.experiments.phase2a_probe import (
    evaluate_minimal_growth_probe,
    evaluate_phase2_family_comparison,
)


def test_phase2a_probe_output_schema_is_stable() -> None:
    result = evaluate_minimal_growth_probe(
        n_values=[20, 24],
        runs=3,
        seed_start=10,
        interval_samples=10,
        null_p=0.2,
        null_edge_density=0.2,
        growth_link_probability=0.2,
    )

    assert isinstance(result.gate_decision.go, bool)
    assert isinstance(result.gate_decision.primary_metrics, tuple)
    assert isinstance(result.gate_decision.failures, tuple)
    assert isinstance(result.diagnostic_bands, tuple)
    assert isinstance(result.combined_min_effect, float)
    assert isinstance(result.best_single_worst_case_effect, float)
    assert isinstance(result.minimal_growth_mean_score, float)
    assert isinstance(result.minkowski_mean_score, float)
    assert isinstance(result.random_mean_score, float)
    assert isinstance(result.fixed_edge_mean_score, float)
    assert result.relative_to_minkowski in {
        "above-minkowski-reference",
        "below-minkowski-reference",
        "tied-minkowski-reference",
    }
    assert result.relative_to_nulls in {
        "toward-manifold-like-vs-nulls",
        "away-from-manifold-like-vs-nulls",
        "neutral-vs-nulls",
    }


def test_phase2b_family_comparison_schema_is_stable() -> None:
    result = evaluate_phase2_family_comparison(
        n_values=[20, 24],
        runs=3,
        seed_start=10,
        interval_samples=10,
        family_names=["bernoulli-forward", "sparse-forward", "age-biased-forward", "window-forward"],
    )

    assert isinstance(result.gate_decision.go, bool)
    assert isinstance(result.family_rows, tuple)
    assert len(result.family_rows) == 4

    family_names = {row.family_name for row in result.family_rows}
    assert family_names == {
        "bernoulli-forward",
        "sparse-forward",
        "age-biased-forward",
        "window-forward",
    }

    for row in result.family_rows:
        assert row.gate_decision in {"GO", "NO-GO"}
        assert isinstance(row.parameters, tuple)
        assert isinstance(row.mechanism, str)
        assert isinstance(row.artifact_risk, str)
        assert row.relative_to_minkowski in {
            "above-minkowski-reference",
            "below-minkowski-reference",
            "tied-minkowski-reference",
        }
        assert row.relative_to_nulls in {
            "toward-manifold-like-vs-nulls",
            "away-from-manifold-like-vs-nulls",
            "neutral-vs-nulls",
        }
