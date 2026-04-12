"""Headless plotting tests for visualization helpers."""

from pathlib import Path

from causal_set_engine.evaluation.interval_study import evaluate_global_interval_statistics
from causal_set_engine.evaluation.layer_profile_study import evaluate_layer_profiles_study
from causal_set_engine.evaluation.midpoint_scaling_study import evaluate_midpoint_scaling_study
from causal_set_engine.evaluation.myrheim_meyer_study import evaluate_myrheim_meyer_study
from causal_set_engine.visualization.distributions import write_interval_abundance_comparison_plots
from causal_set_engine.visualization.profiles import (
    write_layer_profile_sample_plots,
    write_layer_profile_summary_trend_plot,
)
from causal_set_engine.visualization.trends import (
    write_layer_profile_metric_trend_plot,
    write_midpoint_dimension_trend_plot,
    write_myrheim_meyer_trend_plot,
)


def _assert_png(path: Path) -> None:
    assert path.exists()
    assert path.suffix == ".png"
    assert path.stat().st_size > 0


def test_visualization_trend_plot_helpers_write_files(tmp_path: Path) -> None:
    myrheim = evaluate_myrheim_meyer_study(
        dimensions=(2, 3),
        n_values=(20, 24),
        runs=2,
        seed_start=9,
        interval_samples=8,
    )
    midpoint = evaluate_midpoint_scaling_study(
        dimensions=(2, 3),
        n_values=(20, 24),
        runs=2,
        seed_start=9,
        min_interval_size=2,
        max_sampled_intervals=6,
    )
    layers = evaluate_layer_profiles_study(
        dimensions=(2, 3),
        n_values=(20, 24),
        runs=2,
        seed_start=9,
        min_interval_size=2,
        max_sampled_intervals=6,
    )

    output_paths = (
        write_myrheim_meyer_trend_plot(myrheim, tmp_path / "myrheim.png"),
        write_midpoint_dimension_trend_plot(midpoint, tmp_path / "midpoint.png"),
        write_layer_profile_metric_trend_plot(layers, tmp_path / "layer_occ.png"),
        write_layer_profile_summary_trend_plot(layers, tmp_path / "layer_boundary.png"),
    )

    for path in output_paths:
        _assert_png(path)


def test_visualization_distribution_and_profile_helpers_write_files(tmp_path: Path) -> None:
    intervals = evaluate_global_interval_statistics(
        dimensions=(2,),
        n_values=(20,),
        runs=2,
        seed_start=11,
        k_max=3,
    )
    layers = evaluate_layer_profiles_study(
        dimensions=(2,),
        n_values=(20,),
        runs=2,
        seed_start=11,
        min_interval_size=2,
        max_sampled_intervals=5,
    )

    density_paths = write_interval_abundance_comparison_plots(intervals, tmp_path / "intervals", use_density=True)
    count_paths = write_interval_abundance_comparison_plots(intervals, tmp_path / "intervals", use_density=False)
    sample_paths = write_layer_profile_sample_plots(
        layers.sampled_profiles,
        tmp_path / "profiles",
        max_plots=3,
    )

    assert density_paths
    assert count_paths
    assert sample_paths

    for path in (*density_paths, *count_paths, *sample_paths):
        _assert_png(path)
