"""Tests for focused global interval-statistics workflow."""

from causal_set_engine.evaluation.interval_study import evaluate_global_interval_statistics


def test_interval_evaluation_schema_and_links_bin_present() -> None:
    result = evaluate_global_interval_statistics(
        dimensions=(2, 3),
        n_values=(20,),
        runs=2,
        seed_start=11,
        null_p=0.2,
        null_edge_density=0.2,
        k_max=3,
    )

    # 2 Minkowski references + 2 null baselines at one N
    assert len(result.rows) == 4

    for row in result.rows:
        assert row.n == 20
        assert len(row.k_summaries) == 4
        assert row.k_summaries[0].k == 0
        assert row.k_summaries[0].mean_count >= 0.0
        assert 0.0 <= row.k_summaries[0].mean_density <= 1.0
