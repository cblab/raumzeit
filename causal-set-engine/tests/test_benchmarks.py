"""Tests for benchmark-suite instrumentation."""

from causal_set_engine.benchmarks.benchmark_suite import (
    BenchmarkConfig,
    format_report,
    run_benchmark_suite,
)


def test_benchmark_suite_returns_expected_targets() -> None:
    report = run_benchmark_suite(
        BenchmarkConfig(
            n_values=(12,),
            repeats=1,
            seeds=(7,),
            k_max=2,
            min_interval_size=1,
            max_sampled_intervals=4,
            include_workflow_benchmarks=False,
        )
    )

    targets = {row.target for row in report.rows}
    assert targets == {
        "interval_elements",
        "interval_size",
        "link_detection",
        "global_interval_abundances",
        "myrheim_meyer_evaluation",
        "midpoint_scaling_evaluation",
        "layer_profile_evaluation",
    }


def test_benchmark_report_text_contains_expected_sections() -> None:
    report = run_benchmark_suite(
        BenchmarkConfig(
            n_values=(12, 16),
            repeats=1,
            seeds=(7,),
            min_interval_size=1,
            max_sampled_intervals=4,
            include_workflow_benchmarks=False,
        )
    )

    text = format_report(report)
    assert "timing table (seconds)" in text
    assert "major runtime contributors" in text
    assert "empirical scaling summary (conservative)" in text


def test_benchmark_suite_small_case_including_workflows_does_not_crash() -> None:
    report = run_benchmark_suite(
        BenchmarkConfig(
            n_values=(10,),
            repeats=1,
            seeds=(3,),
            min_interval_size=1,
            max_sampled_intervals=3,
            include_workflow_benchmarks=True,
        )
    )

    assert report.top_runtime_targets
    assert all(row.mean_seconds >= 0.0 for row in report.rows)
