"""Schema regression test for phase-2c age-biased scan."""

from causal_set_engine.experiments.phase2c_scan import evaluate_age_biased_phase2c_scan


def test_phase2c_scan_output_schema_is_stable() -> None:
    result = evaluate_age_biased_phase2c_scan(
        n_values=[20, 24],
        runs=3,
        seed_start=11,
        interval_samples=10,
        link_density_grid=(0.16, 0.22),
        bias_strength_grid=(0.0, 1.0),
    )

    assert isinstance(result.gate_decision.go, bool)
    assert isinstance(result.settings, tuple)
    assert isinstance(result.rows, tuple)
    assert len(result.settings) == 4
    assert len(result.rows) == 4

    for row in result.rows:
        assert row.gate_decision in {"GO", "NO-GO"}
        assert row.primary_diagnostic_profile in {
            "closer-than-null-average-on-primary",
            "farther-than-null-average-on-primary",
            "tied-with-null-average-on-primary",
            "no-primary-metrics",
        }
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
        assert 0.0 <= row.birth_order_dominance_proxy <= 1.0
        assert 0.0 <= row.age_layering_stratification_proxy <= 1.0
        assert row.interpretation_label in {
            "improved but artifact-dominated",
            "mixed",
            "no meaningful improvement",
            "unstable",
        }
        assert isinstance(row.mean_score, float)
        assert isinstance(row.score_stddev, float)
