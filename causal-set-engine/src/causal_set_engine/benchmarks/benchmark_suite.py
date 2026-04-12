"""Lightweight benchmark suite for interval and CST-observable runtime measurement.

This module is intentionally measurement-only:
- consumes existing engine APIs,
- does not alter scientific logic,
- does not introduce optimization machinery.
"""

from __future__ import annotations

import math
import statistics
import time
from dataclasses import dataclass

from causal_set_engine.evaluation.layer_profile_study import evaluate_layer_profiles_study
from causal_set_engine.evaluation.midpoint_scaling_study import evaluate_midpoint_scaling_study
from causal_set_engine.evaluation.myrheim_meyer_study import evaluate_myrheim_meyer_study
from causal_set_engine.generators.minkowski_3d import generate_minkowski_3d
from causal_set_engine.observables.cst.intervals import (
    compute_interval_abundances,
    interval_elements,
    interval_size,
    is_link,
)
from causal_set_engine.observables.cst.layer_profiles import compute_layer_profile_summary
from causal_set_engine.observables.cst.midpoint_scaling import (
    compute_midpoint_scaling_statistic,
    sampled_qualifying_intervals,
)
from causal_set_engine.observables.cst.myrheim_meyer import estimate_myrheim_meyer_dimension


@dataclass(frozen=True)
class BenchmarkConfig:
    """Configuration for deterministic, reproducible benchmark sweeps."""

    n_values: tuple[int, ...] = (40, 80, 120)
    repeats: int = 3
    seeds: tuple[int, ...] = (100, 101, 102)
    k_max: int = 5
    min_interval_size: int = 8
    max_sampled_intervals: int = 64
    include_workflow_benchmarks: bool = True


@dataclass(frozen=True)
class BenchmarkRow:
    """Aggregate timing for one benchmark target at one N."""

    target: str
    n: int
    runs: int
    mean_seconds: float
    stdev_seconds: float


@dataclass(frozen=True)
class ScalingRow:
    """Conservative empirical scaling summary for one target across N."""

    target: str
    n_min: int
    n_max: int
    empirical_exponent: float
    trend_label: str


@dataclass(frozen=True)
class BenchmarkReport:
    """Complete benchmark output payload."""

    config: BenchmarkConfig
    rows: tuple[BenchmarkRow, ...]
    scaling_rows: tuple[ScalingRow, ...]
    top_runtime_targets: tuple[str, ...]


def _validate_config(config: BenchmarkConfig) -> None:
    if not config.n_values or any(n <= 1 for n in config.n_values):
        raise ValueError("n_values must be non-empty and contain only values > 1")
    if config.repeats <= 0:
        raise ValueError("repeats must be positive")
    if not config.seeds:
        raise ValueError("seeds must be non-empty")
    if config.k_max < 0:
        raise ValueError("k_max must be non-negative")
    if config.min_interval_size < 0:
        raise ValueError("min_interval_size must be non-negative")
    if config.max_sampled_intervals <= 0:
        raise ValueError("max_sampled_intervals must be positive")


def _time_call(fn) -> float:
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start


def _choose_interval_pair(cset, seed: int, min_interval_size: int) -> tuple[int, int]:
    sampling = sampled_qualifying_intervals(
        cset,
        min_interval_size=min_interval_size,
        max_sampled_intervals=1,
        seed=seed,
    )
    if sampling.sampled_pairs:
        return sampling.sampled_pairs[0]

    elements = sorted(cset.elements)
    for x in elements:
        for y in elements:
            if x != y and cset.is_related(x, y):
                return (x, y)

    raise ValueError("causal set has no comparable pair; cannot benchmark interval operations")


def _choose_midpoint_pair(cset, seed: int, min_interval_size: int) -> tuple[int, int] | None:
    sampling = sampled_qualifying_intervals(
        cset,
        min_interval_size=max(1, min_interval_size),
        max_sampled_intervals=1,
        seed=seed,
    )
    if sampling.sampled_pairs:
        return sampling.sampled_pairs[0]
    return None


def _run_target_timings(config: BenchmarkConfig) -> list[BenchmarkRow]:
    rows: list[BenchmarkRow] = []
    for n in config.n_values:
        csets = [generate_minkowski_3d(n=n, seed=seed)[0] for seed in config.seeds]
        pairs = [
            _choose_interval_pair(cset, seed, config.min_interval_size)
            for cset, seed in zip(csets, config.seeds)
        ]
        midpoint_pairs = [
            _choose_midpoint_pair(cset, seed, config.min_interval_size)
            for cset, seed in zip(csets, config.seeds)
        ]

        target_samples: dict[str, list[float]] = {
            "interval_elements": [],
            "interval_size": [],
            "link_detection": [],
            "global_interval_abundances": [],
            "myrheim_meyer_evaluation": [],
            "midpoint_scaling_evaluation": [],
            "layer_profile_evaluation": [],
        }

        if config.include_workflow_benchmarks:
            target_samples["workflow_myrheim_e2e"] = []
            target_samples["workflow_midpoint_e2e"] = []
            target_samples["workflow_layers_e2e"] = []

        for _ in range(config.repeats):
            for cset, seed, (x, y), midpoint_pair in zip(csets, config.seeds, pairs, midpoint_pairs):
                target_samples["interval_elements"].append(
                    _time_call(lambda: interval_elements(cset, x, y))
                )
                target_samples["interval_size"].append(_time_call(lambda: interval_size(cset, x, y)))
                target_samples["link_detection"].append(_time_call(lambda: is_link(cset, x, y)))
                target_samples["global_interval_abundances"].append(
                    _time_call(lambda: compute_interval_abundances(cset, config.k_max))
                )
                target_samples["myrheim_meyer_evaluation"].append(
                    _time_call(lambda: estimate_myrheim_meyer_dimension(cset))
                )

                sampled = sampled_qualifying_intervals(
                    cset,
                    min_interval_size=config.min_interval_size,
                    max_sampled_intervals=config.max_sampled_intervals,
                    seed=seed + 10_000,
                )
                interval_pairs = sampled.sampled_pairs or ((midpoint_pair,) if midpoint_pair else ())

                target_samples["midpoint_scaling_evaluation"].append(
                    _time_call(
                        lambda: [compute_midpoint_scaling_statistic(cset, a, b) for a, b in interval_pairs]
                    )
                )
                target_samples["layer_profile_evaluation"].append(
                    _time_call(
                        lambda: [compute_layer_profile_summary(cset, a, b) for a, b in interval_pairs]
                    )
                )

                if config.include_workflow_benchmarks:
                    target_samples["workflow_myrheim_e2e"].append(
                        _time_call(
                            lambda: evaluate_myrheim_meyer_study(
                                dimensions=(3,),
                                n_values=(n,),
                                runs=1,
                                seed_start=seed,
                                interval_samples=10,
                            )
                        )
                    )
                    target_samples["workflow_midpoint_e2e"].append(
                        _time_call(
                            lambda: evaluate_midpoint_scaling_study(
                                dimensions=(3,),
                                n_values=(n,),
                                runs=1,
                                seed_start=seed,
                                min_interval_size=max(1, config.min_interval_size // 2),
                                max_sampled_intervals=min(8, config.max_sampled_intervals),
                            )
                        )
                    )
                    target_samples["workflow_layers_e2e"].append(
                        _time_call(
                            lambda: evaluate_layer_profiles_study(
                                dimensions=(3,),
                                n_values=(n,),
                                runs=1,
                                seed_start=seed,
                                min_interval_size=max(1, config.min_interval_size // 2),
                                max_sampled_intervals=min(8, config.max_sampled_intervals),
                            )
                        )
                    )

        for target, samples in target_samples.items():
            rows.append(
                BenchmarkRow(
                    target=target,
                    n=n,
                    runs=len(samples),
                    mean_seconds=statistics.fmean(samples),
                    stdev_seconds=statistics.stdev(samples) if len(samples) > 1 else 0.0,
                )
            )

    return rows


def _trend_label(exponent: float) -> str:
    if exponent < 0.5:
        return "weak-growth"
    if exponent < 1.5:
        return "approximately-linear"
    if exponent < 2.5:
        return "superlinear"
    return "steeper-than-quadratic"


def _scaling_rows(rows: list[BenchmarkRow]) -> list[ScalingRow]:
    by_target: dict[str, list[BenchmarkRow]] = {}
    for row in rows:
        by_target.setdefault(row.target, []).append(row)

    summaries: list[ScalingRow] = []
    for target, target_rows in by_target.items():
        ordered = sorted(target_rows, key=lambda row: row.n)
        if len(ordered) < 2:
            continue

        first = ordered[0]
        last = ordered[-1]
        if first.mean_seconds <= 0.0 or first.n == last.n:
            continue

        exponent = math.log(last.mean_seconds / first.mean_seconds) / math.log(last.n / first.n)
        summaries.append(
            ScalingRow(
                target=target,
                n_min=first.n,
                n_max=last.n,
                empirical_exponent=exponent,
                trend_label=_trend_label(exponent),
            )
        )

    return summaries


def run_benchmark_suite(config: BenchmarkConfig) -> BenchmarkReport:
    """Run the benchmark suite and return auditable timing summaries."""
    _validate_config(config)
    rows = _run_target_timings(config)
    scaling_rows = _scaling_rows(rows)

    by_target_total: dict[str, float] = {}
    for row in rows:
        by_target_total[row.target] = by_target_total.get(row.target, 0.0) + row.mean_seconds

    top_runtime_targets = tuple(
        target
        for target, _ in sorted(by_target_total.items(), key=lambda item: item[1], reverse=True)[:3]
    )

    return BenchmarkReport(
        config=config,
        rows=tuple(sorted(rows, key=lambda row: (row.target, row.n))),
        scaling_rows=tuple(sorted(scaling_rows, key=lambda row: row.target)),
        top_runtime_targets=top_runtime_targets,
    )


def format_report(report: BenchmarkReport) -> str:
    """Render a compact, text-first benchmark report."""
    lines: list[str] = []
    lines.append("causal-set-engine benchmark report")
    lines.append(
        "config "
        + " ".join(
            [
                f"n_values={list(report.config.n_values)}",
                f"repeats={report.config.repeats}",
                f"seeds={list(report.config.seeds)}",
                f"k_max={report.config.k_max}",
                f"min_interval_size={report.config.min_interval_size}",
                f"max_sampled_intervals={report.config.max_sampled_intervals}",
                f"include_workflow_benchmarks={report.config.include_workflow_benchmarks}",
            ]
        )
    )

    lines.append("\ntiming table (seconds)")
    lines.append("target                        N    runs  mean      stdev")
    for row in report.rows:
        lines.append(
            f"{row.target:<28} {row.n:<4} {row.runs:<5} {row.mean_seconds:>8.6f} {row.stdev_seconds:>8.6f}"
        )

    lines.append("\nmajor runtime contributors")
    for rank, target in enumerate(report.top_runtime_targets, start=1):
        lines.append(f"{rank}. {target}")

    lines.append("\nempirical scaling summary (conservative)")
    lines.append("target                        n_min n_max exponent trend")
    for row in report.scaling_rows:
        lines.append(
            f"{row.target:<28} {row.n_min:<5} {row.n_max:<5} {row.empirical_exponent:>8.3f} {row.trend_label}"
        )

    return "\n".join(lines)
