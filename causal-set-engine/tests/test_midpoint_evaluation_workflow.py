"""Tests for midpoint-scaling workflow evaluation helpers."""

from causal_set_engine.evaluation.midpoint_scaling_study import evaluate_midpoint_scaling_study


def test_midpoint_evaluation_schema_and_separation_rows_present() -> None:
    result = evaluate_midpoint_scaling_study(
        dimensions=(2, 3),
        n_values=(20,),
        runs=2,
        seed_start=11,
        null_p=0.2,
        null_edge_density=0.2,
        min_interval_size=2,
        max_sampled_intervals=8,
    )

    # 2 Minkowski references + 2 null baselines at one N
    assert len(result.per_model_n) == 4
    assert len(result.separation_rows) == 4
    assert len(result.monotone_by_n) == 1

    for row in result.per_model_n:
        assert row.n == 20
        assert row.sampled_interval_count_mean >= 0.0
        assert row.qualifying_interval_count_mean >= row.sampled_interval_count_mean
