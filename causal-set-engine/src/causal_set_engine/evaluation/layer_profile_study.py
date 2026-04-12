"""Reusable interval layer-profile evaluation helpers."""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from causal_set_engine.evaluation.metrics import run_once
from causal_set_engine.evaluation.sampling import edge_count_from_density
from causal_set_engine.evaluation.scoring import standardized_effect_size
from causal_set_engine.generators.minkowski_2d import generate_minkowski_2d
from causal_set_engine.generators.minkowski_3d import generate_minkowski_3d
from causal_set_engine.generators.minkowski_4d import generate_minkowski_4d
from causal_set_engine.generators.null_models import generate_fixed_edge_count_poset
from causal_set_engine.generators.random_poset import generate_random_poset
from causal_set_engine.observables.cst import (
    compute_layer_profile,
    summarize_layer_profile,
    compute_midpoint_scaling_statistic,
    sampled_qualifying_intervals,
)


@dataclass(frozen=True)
class MetricSummary:
    mean: float
    stdev: float


@dataclass(frozen=True)
class LayerProfileModelNRow:
    model: str
    n: int
    occupied_layers: MetricSummary
    peak_layer_size: MetricSummary
    peak_layer_index: MetricSummary
    boundary_fraction: MetricSummary
    midpoint_dimension_estimate: MetricSummary
    myrheim_meyer: MetricSummary
    sampled_interval_count_mean: float
    qualifying_interval_count_mean: float
    under_sampled_runs: int




@dataclass(frozen=True)
class LayerProfileSample:
    """One sampled interval profile retained for researcher-facing plotting."""

    model: str
    n: int
    seed: int
    interval_index: int
    profile: tuple[int, ...]

@dataclass(frozen=True)
class LayerProfileSeparationRow:
    model: str
    n: int
    null_model: str
    occupied_layers_effect_size: float
    boundary_fraction_effect_size: float
    peak_index_effect_size: float
    midpoint_effect_size: float
    myrheim_meyer_effect_size: float


@dataclass(frozen=True)
class LayerProfileEvaluationResult:
    per_model_n: tuple[LayerProfileModelNRow, ...]
    separation_rows: tuple[LayerProfileSeparationRow, ...]
    sampled_profiles: tuple[LayerProfileSample, ...]
    conservative_min_effect_layers: float
    conservative_min_effect_midpoint: float
    conservative_min_effect_myrheim_meyer: float


def _summary(values: list[float]) -> MetricSummary:
    return MetricSummary(
        mean=statistics.fmean(values),
        stdev=statistics.stdev(values) if len(values) > 1 else 0.0,
    )


def _minkowski_generator(dimension: int):
    if dimension == 2:
        return lambda n, seed: generate_minkowski_2d(n=n, seed=seed)[0]
    if dimension == 3:
        return lambda n, seed: generate_minkowski_3d(n=n, seed=seed)[0]
    if dimension == 4:
        return lambda n, seed: generate_minkowski_4d(n=n, seed=seed)[0]
    raise ValueError("dimension must be one of {2, 3, 4}")


def _model_rows(
    *,
    model: str,
    generator,
    n: int,
    runs: int,
    seed_start: int,
    min_interval_size: int,
    max_sampled_intervals: int,
    interval_seed_offset: int,
) -> tuple[LayerProfileModelNRow, list[dict[str, float]], list[LayerProfileSample]]:
    rows: list[dict[str, float]] = []
    sampled_profiles: list[LayerProfileSample] = []
    for seed in range(seed_start, seed_start + runs):
        cset = generator(n, seed)
        metrics = run_once(cset, interval_samples=50, seed=seed)
        sampling = sampled_qualifying_intervals(
            cset,
            min_interval_size=min_interval_size,
            max_sampled_intervals=max_sampled_intervals,
            seed=seed + interval_seed_offset,
        )

        occupied_layers: list[float] = []
        peak_layer_sizes: list[float] = []
        peak_layer_indices: list[float] = []
        boundary_fractions: list[float] = []
        midpoint_dimensions: list[float] = []
        for interval_index, (x, y) in enumerate(sampling.sampled_pairs):
            profile = compute_layer_profile(cset, x, y)
            summary = summarize_layer_profile(profile)
            occupied_layers.append(float(summary.occupied_layer_count))
            peak_layer_sizes.append(float(summary.peak_layer_size))
            peak_layer_indices.append(float(summary.peak_layer_index))
            boundary_fractions.append(summary.first_last_layer_fraction)
            midpoint_dimensions.append(
                compute_midpoint_scaling_statistic(cset, x, y).derived_dimension_estimate
            )
            sampled_profiles.append(
                LayerProfileSample(
                    model=model,
                    n=n,
                    seed=seed,
                    interval_index=interval_index,
                    profile=profile,
                )
            )

        rows.append(
            {
                "occupied_layers": statistics.fmean(occupied_layers) if occupied_layers else 0.0,
                "peak_layer_size": statistics.fmean(peak_layer_sizes) if peak_layer_sizes else 0.0,
                "peak_layer_index": statistics.fmean(peak_layer_indices) if peak_layer_indices else 0.0,
                "boundary_fraction": statistics.fmean(boundary_fractions) if boundary_fractions else 0.0,
                "midpoint_dimension_estimate": statistics.fmean(midpoint_dimensions)
                if midpoint_dimensions
                else 0.0,
                "myrheim_meyer": metrics["myrheim_meyer_dimension"],
                "sampled_interval_count": float(sampling.sampled_interval_count),
                "qualifying_interval_count": float(sampling.qualifying_interval_count),
                "under_sampled": 1.0
                if sampling.sampled_interval_count < max_sampled_intervals
                else 0.0,
            }
        )

    model_row = LayerProfileModelNRow(
        model=model,
        n=n,
        occupied_layers=_summary([row["occupied_layers"] for row in rows]),
        peak_layer_size=_summary([row["peak_layer_size"] for row in rows]),
        peak_layer_index=_summary([row["peak_layer_index"] for row in rows]),
        boundary_fraction=_summary([row["boundary_fraction"] for row in rows]),
        midpoint_dimension_estimate=_summary([row["midpoint_dimension_estimate"] for row in rows]),
        myrheim_meyer=_summary([row["myrheim_meyer"] for row in rows]),
        sampled_interval_count_mean=statistics.fmean(row["sampled_interval_count"] for row in rows),
        qualifying_interval_count_mean=statistics.fmean(row["qualifying_interval_count"] for row in rows),
        under_sampled_runs=int(sum(row["under_sampled"] for row in rows)),
    )
    return model_row, rows, sampled_profiles


def evaluate_layer_profiles_study(
    *,
    dimensions: tuple[int, ...],
    n_values: tuple[int, ...],
    runs: int = 8,
    seed_start: int = 100,
    null_p: float = 0.2,
    null_edge_density: float = 0.2,
    min_interval_size: int = 8,
    max_sampled_intervals: int = 64,
    interval_seed_offset: int = 10_000,
) -> LayerProfileEvaluationResult:
    """Evaluate layer-profile summaries on sampled qualifying intervals."""
    per_model_n: list[LayerProfileModelNRow] = []
    mk_rows_by_dim_n: dict[tuple[int, int], list[dict[str, float]]] = {}
    random_rows_by_n: dict[int, list[dict[str, float]]] = {}
    fixed_rows_by_n: dict[int, list[dict[str, float]]] = {}
    sampled_profiles: list[LayerProfileSample] = []

    for n in n_values:
        random_row, random_runs, random_samples = _model_rows(
            model="null-random-poset",
            generator=lambda n_val, seed: generate_random_poset(
                n=n_val,
                relation_probability=null_p,
                seed=seed,
            ),
            n=n,
            runs=runs,
            seed_start=seed_start,
            min_interval_size=min_interval_size,
            max_sampled_intervals=max_sampled_intervals,
            interval_seed_offset=interval_seed_offset,
        )
        per_model_n.append(random_row)
        random_rows_by_n[n] = random_runs
        sampled_profiles.extend(random_samples)

        fixed_edge_count = edge_count_from_density(n, null_edge_density)
        fixed_row, fixed_runs, fixed_samples = _model_rows(
            model="null-fixed-edge-poset",
            generator=lambda n_val, seed: generate_fixed_edge_count_poset(
                n=n_val,
                edge_count=fixed_edge_count,
                seed=seed,
            ),
            n=n,
            runs=runs,
            seed_start=seed_start,
            min_interval_size=min_interval_size,
            max_sampled_intervals=max_sampled_intervals,
            interval_seed_offset=interval_seed_offset,
        )
        per_model_n.append(fixed_row)
        fixed_rows_by_n[n] = fixed_runs
        sampled_profiles.extend(fixed_samples)

        for dimension in dimensions:
            row, rows, model_samples = _model_rows(
                model=f"minkowski-{dimension}d",
                generator=_minkowski_generator(dimension),
                n=n,
                runs=runs,
                seed_start=seed_start,
                min_interval_size=min_interval_size,
                max_sampled_intervals=max_sampled_intervals,
                interval_seed_offset=interval_seed_offset,
            )
            per_model_n.append(row)
            mk_rows_by_dim_n[(dimension, n)] = rows
            sampled_profiles.extend(model_samples)

    separation_rows: list[LayerProfileSeparationRow] = []
    layer_effects: list[float] = []
    midpoint_effects: list[float] = []
    mm_effects: list[float] = []
    for n in n_values:
        for dimension in dimensions:
            mk_rows = mk_rows_by_dim_n[(dimension, n)]
            random_rows = random_rows_by_n[n]
            fixed_rows = fixed_rows_by_n[n]
            for null_name, null_rows in (("random-poset", random_rows), ("fixed-edge-poset", fixed_rows)):
                occupied_effect = standardized_effect_size(
                    [row["occupied_layers"] for row in mk_rows],
                    [row["occupied_layers"] for row in null_rows],
                )
                boundary_effect = standardized_effect_size(
                    [row["boundary_fraction"] for row in mk_rows],
                    [row["boundary_fraction"] for row in null_rows],
                )
                peak_index_effect = standardized_effect_size(
                    [row["peak_layer_index"] for row in mk_rows],
                    [row["peak_layer_index"] for row in null_rows],
                )
                midpoint_effect = standardized_effect_size(
                    [row["midpoint_dimension_estimate"] for row in mk_rows],
                    [row["midpoint_dimension_estimate"] for row in null_rows],
                )
                mm_effect = standardized_effect_size(
                    [row["myrheim_meyer"] for row in mk_rows],
                    [row["myrheim_meyer"] for row in null_rows],
                )

                layer_effects.extend([occupied_effect, boundary_effect, peak_index_effect])
                midpoint_effects.append(midpoint_effect)
                mm_effects.append(mm_effect)

                separation_rows.append(
                    LayerProfileSeparationRow(
                        model=f"minkowski-{dimension}d",
                        n=n,
                        null_model=null_name,
                        occupied_layers_effect_size=occupied_effect,
                        boundary_fraction_effect_size=boundary_effect,
                        peak_index_effect_size=peak_index_effect,
                        midpoint_effect_size=midpoint_effect,
                        myrheim_meyer_effect_size=mm_effect,
                    )
                )

    return LayerProfileEvaluationResult(
        per_model_n=tuple(per_model_n),
        separation_rows=tuple(separation_rows),
        sampled_profiles=tuple(sampled_profiles),
        conservative_min_effect_layers=min(abs(value) for value in layer_effects),
        conservative_min_effect_midpoint=min(abs(value) for value in midpoint_effects),
        conservative_min_effect_myrheim_meyer=min(abs(value) for value in mm_effects),
    )
