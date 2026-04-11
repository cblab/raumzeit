"""Deterministic tests for phase-1.75 decision utilities."""

from causal_set_engine.evaluation.scoring import (
    PairQuality,
    aggregate_diagnostic_quality,
    build_combined_score,
    interval_overlap_fraction,
    mean_difference,
    sign_consistency_fraction,
    standardized_effect_size,
    trend_consistency,
)


def test_basic_quality_functions_are_deterministic() -> None:
    mk = [3.0, 4.0, 5.0, 6.0]
    null = [1.0, 2.0, 2.0, 3.0]

    assert mean_difference(mk, null) == 2.5
    assert standardized_effect_size(mk, null) > 2.0
    assert interval_overlap_fraction(mk, null) == 0.0
    assert sign_consistency_fraction(mk, null) == 1.0
    assert trend_consistency({40: 0.8, 60: 1.2, 80: 1.3}) == 1.0


def test_aggregate_ranking_prefers_stable_strong_signal() -> None:
    rows = [
        PairQuality("dimension_estimate", 40, "random-poset", 0.9, 1.8, 0.1, 1.0),
        PairQuality("dimension_estimate", 80, "random-poset", 1.1, 2.0, 0.0, 1.0),
        PairQuality("dimension_estimate", 40, "fixed-edge-poset", 0.8, 1.6, 0.1, 1.0),
        PairQuality("dimension_estimate", 80, "fixed-edge-poset", 1.0, 1.9, 0.0, 1.0),
        PairQuality("relation_density", 40, "random-poset", 0.02, 0.15, 0.9, 0.5),
        PairQuality("relation_density", 80, "random-poset", 0.01, 0.10, 0.95, 0.5),
        PairQuality("relation_density", 40, "fixed-edge-poset", 0.01, 0.08, 0.9, 0.5),
        PairQuality("relation_density", 80, "fixed-edge-poset", 0.01, 0.07, 0.95, 0.5),
    ]

    ranked = aggregate_diagnostic_quality(rows)
    assert ranked[0].metric == "dimension_estimate"
    assert ranked[0].band in {"moderate discriminator", "strong discriminator"}
    assert ranked[-1].metric == "relation_density"


def test_combined_score_and_effect_stability_across_size_sweep() -> None:
    metrics = ("dimension_estimate", "longest_chain_length", "interval_mean", "relation_density")

    mk_by_n = {
        40: [
            {"dimension_estimate": 2.2, "longest_chain_length": 8.0, "interval_mean": 1.9, "relation_density": 0.20},
            {"dimension_estimate": 2.3, "longest_chain_length": 8.2, "interval_mean": 2.0, "relation_density": 0.21},
        ],
        80: [
            {"dimension_estimate": 2.7, "longest_chain_length": 10.0, "interval_mean": 2.5, "relation_density": 0.20},
            {"dimension_estimate": 2.8, "longest_chain_length": 10.1, "interval_mean": 2.6, "relation_density": 0.21},
        ],
    }
    random_by_n = {
        40: [
            {"dimension_estimate": 1.5, "longest_chain_length": 11.5, "interval_mean": 3.1, "relation_density": 0.20},
            {"dimension_estimate": 1.4, "longest_chain_length": 11.7, "interval_mean": 3.0, "relation_density": 0.19},
        ],
        80: [
            {"dimension_estimate": 1.2, "longest_chain_length": 14.0, "interval_mean": 4.0, "relation_density": 0.20},
            {"dimension_estimate": 1.1, "longest_chain_length": 14.2, "interval_mean": 4.1, "relation_density": 0.19},
        ],
    }
    fixed_by_n = {
        40: [
            {"dimension_estimate": 1.6, "longest_chain_length": 11.0, "interval_mean": 2.9, "relation_density": 0.20},
            {"dimension_estimate": 1.5, "longest_chain_length": 11.1, "interval_mean": 2.8, "relation_density": 0.19},
        ],
        80: [
            {"dimension_estimate": 1.3, "longest_chain_length": 13.2, "interval_mean": 3.7, "relation_density": 0.20},
            {"dimension_estimate": 1.2, "longest_chain_length": 13.3, "interval_mean": 3.8, "relation_density": 0.19},
        ],
    }

    combined = build_combined_score(metrics, mk_by_n, random_by_n, fixed_by_n)

    assert combined.minkowski_mean > combined.random_mean
    assert combined.minkowski_mean > combined.fixed_edge_mean
    assert combined.mk_vs_random_effect > 1.0
    assert combined.mk_vs_fixed_effect > 1.0
