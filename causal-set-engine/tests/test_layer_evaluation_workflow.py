"""Tests for focused layer-profile workflow evaluation helpers."""

from causal_set_engine.evaluation.layer_profile_study import evaluate_layer_profiles_study


def test_layer_profile_evaluation_schema_and_rows_present() -> None:
    result = evaluate_layer_profiles_study(
        dimensions=(2, 3),
        n_values=(20,),
        runs=2,
        seed_start=11,
        null_p=0.2,
        null_edge_density=0.2,
        min_interval_size=2,
        max_sampled_intervals=8,
    )

    assert len(result.per_model_n) == 4
    assert len(result.separation_rows) == 4
    assert result.conservative_min_effect_layers >= 0.0
    assert result.conservative_min_effect_midpoint >= 0.0
    assert result.conservative_min_effect_myrheim_meyer >= 0.0
    assert result.sampled_profiles

    for row in result.per_model_n:
        assert row.n == 20
        assert row.sampled_interval_count_mean >= 0.0
        assert row.qualifying_interval_count_mean >= row.sampled_interval_count_mean
