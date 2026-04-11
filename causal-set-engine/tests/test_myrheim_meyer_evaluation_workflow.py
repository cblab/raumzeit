"""Tests for focused Myrheim-Meyer evaluation workflow."""

from causal_set_engine.evaluation.myrheim_meyer_study import evaluate_myrheim_meyer_study


def test_myrheim_meyer_evaluation_schema_and_core_signals() -> None:
    result = evaluate_myrheim_meyer_study(
        dimensions=(2, 3, 4),
        n_values=(24, 32),
        runs=3,
        seed_start=14,
        interval_samples=10,
        null_p=0.2,
        null_edge_density=0.2,
    )

    assert len(result.per_dimension_n) == 3 * 2
    assert len(result.separation_rows) == 3 * 2 * 2
    assert len(result.dimension_trends) == 3
    assert len(result.monotone_by_n) == 2

    assert all(value > 0.0 for value in [
        result.conservative_min_effect_myrheim_meyer,
        result.conservative_min_effect_chain_proxy,
    ])

    trend_by_dimension = {row.dimension: row.myrheim_meyer_means for row in result.dimension_trends}
    assert trend_by_dimension[2][0] < trend_by_dimension[3][0] < trend_by_dimension[4][0]


def test_myrheim_meyer_evaluation_monotone_flags_use_requested_dimensions() -> None:
    result = evaluate_myrheim_meyer_study(
        dimensions=(2, 4),
        n_values=(20,),
        runs=2,
        seed_start=11,
        interval_samples=8,
    )

    assert len(result.per_dimension_n) == 2
    assert len(result.monotone_by_n) == 1
    assert result.monotone_by_n[0][0] == 20
