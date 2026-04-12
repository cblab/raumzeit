"""Reusable midpoint-scaling evaluation helpers."""

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
    compute_midpoint_scaling_statistic,
    sampled_qualifying_intervals,
)


@dataclass(frozen=True)
class MetricSummary:
    mean: float
    stdev: float


@dataclass(frozen=True)
class MidpointModelNRow:
    model: str
    n: int
    midpoint_scaling: MetricSummary
    midpoint_dimension_estimate: MetricSummary
    myrheim_meyer: MetricSummary
    chain_height_proxy: MetricSummary
    sampled_interval_count_mean: float
    qualifying_interval_count_mean: float
    under_sampled_runs: int


@dataclass(frozen=True)
class MidpointSeparationRow:
    model: str
    n: int
    null_model: str
    midpoint_effect_size: float
    myrheim_meyer_effect_size: float
    chain_proxy_effect_size: float


@dataclass(frozen=True)
class MidpointEvaluationResult:
    per_model_n: tuple[MidpointModelNRow, ...]
    separation_rows: tuple[MidpointSeparationRow, ...]
    monotone_by_n: tuple[tuple[int, bool], ...]
    conservative_min_effect_midpoint: float
    conservative_min_effect_myrheim_meyer: float
    conservative_min_effect_chain_proxy: float


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
) -> tuple[MidpointModelNRow, list[dict[str, float]]]:
    rows: list[dict[str, float]] = []
    for seed in range(seed_start, seed_start + runs):
        cset = generator(n, seed)
        metrics = run_once(cset, interval_samples=50, seed=seed)
        sampling = sampled_qualifying_intervals(
            cset,
            min_interval_size=min_interval_size,
            max_sampled_intervals=max_sampled_intervals,
            seed=seed + interval_seed_offset,
        )

        scaling_values: list[float] = []
        dimension_values: list[float] = []
        for x, y in sampling.sampled_pairs:
            stat = compute_midpoint_scaling_statistic(cset, x, y)
            scaling_values.append(stat.scaling_statistic)
            dimension_values.append(stat.derived_dimension_estimate)

        midpoint_scaling_mean = statistics.fmean(scaling_values) if scaling_values else 0.0
        midpoint_dimension_mean = statistics.fmean(dimension_values) if dimension_values else 0.0

        rows.append(
            {
                "midpoint_scaling": midpoint_scaling_mean,
                "midpoint_dimension_estimate": midpoint_dimension_mean,
                "myrheim_meyer": metrics["myrheim_meyer_dimension"],
                "chain_height_proxy": metrics["dimension_estimate"],
                "sampled_interval_count": float(sampling.sampled_interval_count),
                "qualifying_interval_count": float(sampling.qualifying_interval_count),
                "under_sampled": 1.0
                if sampling.sampled_interval_count < max_sampled_intervals
                else 0.0,
            }
        )

    model_row = MidpointModelNRow(
        model=model,
        n=n,
        midpoint_scaling=_summary([row["midpoint_scaling"] for row in rows]),
        midpoint_dimension_estimate=_summary([row["midpoint_dimension_estimate"] for row in rows]),
        myrheim_meyer=_summary([row["myrheim_meyer"] for row in rows]),
        chain_height_proxy=_summary([row["chain_height_proxy"] for row in rows]),
        sampled_interval_count_mean=statistics.fmean(row["sampled_interval_count"] for row in rows),
        qualifying_interval_count_mean=statistics.fmean(row["qualifying_interval_count"] for row in rows),
        under_sampled_runs=int(sum(row["under_sampled"] for row in rows)),
    )

    return model_row, rows


def evaluate_midpoint_scaling_study(
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
) -> MidpointEvaluationResult:
    """Evaluate midpoint scaling on deterministic sampled qualifying intervals."""
    per_model_n: list[MidpointModelNRow] = []
    mk_rows_by_dim_n: dict[tuple[int, int], list[dict[str, float]]] = {}
    random_rows_by_n: dict[int, list[dict[str, float]]] = {}
    fixed_rows_by_n: dict[int, list[dict[str, float]]] = {}

    for n in n_values:
        random_row, random_runs = _model_rows(
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

        fixed_edge_count = edge_count_from_density(n, null_edge_density)
        fixed_row, fixed_runs = _model_rows(
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

        for dimension in dimensions:
            row, runs_rows = _model_rows(
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
            mk_rows_by_dim_n[(dimension, n)] = runs_rows

    monotone_by_n: list[tuple[int, bool]] = []
    separation_rows: list[MidpointSeparationRow] = []
    midpoint_effects: list[float] = []
    mm_effects: list[float] = []
    chain_effects: list[float] = []

    for n in n_values:
        dim_means = [
            statistics.fmean(row["midpoint_dimension_estimate"] for row in mk_rows_by_dim_n[(d, n)])
            for d in dimensions
        ]
        monotone_by_n.append(
            (n, all(dim_means[idx] < dim_means[idx + 1] for idx in range(len(dim_means) - 1)))
        )

        for dimension in dimensions:
            mk_rows = mk_rows_by_dim_n[(dimension, n)]
            random_rows = random_rows_by_n[n]
            fixed_rows = fixed_rows_by_n[n]

            for null_name, null_rows in (("random-poset", random_rows), ("fixed-edge-poset", fixed_rows)):
                midpoint_effect = standardized_effect_size(
                    [row["midpoint_dimension_estimate"] for row in mk_rows],
                    [row["midpoint_dimension_estimate"] for row in null_rows],
                )
                mm_effect = standardized_effect_size(
                    [row["myrheim_meyer"] for row in mk_rows],
                    [row["myrheim_meyer"] for row in null_rows],
                )
                chain_effect = standardized_effect_size(
                    [row["chain_height_proxy"] for row in mk_rows],
                    [row["chain_height_proxy"] for row in null_rows],
                )

                midpoint_effects.append(midpoint_effect)
                mm_effects.append(mm_effect)
                chain_effects.append(chain_effect)

                separation_rows.append(
                    MidpointSeparationRow(
                        model=f"minkowski-{dimension}d",
                        n=n,
                        null_model=null_name,
                        midpoint_effect_size=midpoint_effect,
                        myrheim_meyer_effect_size=mm_effect,
                        chain_proxy_effect_size=chain_effect,
                    )
                )

    return MidpointEvaluationResult(
        per_model_n=tuple(per_model_n),
        separation_rows=tuple(separation_rows),
        monotone_by_n=tuple(monotone_by_n),
        conservative_min_effect_midpoint=min(abs(value) for value in midpoint_effects),
        conservative_min_effect_myrheim_meyer=min(abs(value) for value in mm_effects),
        conservative_min_effect_chain_proxy=min(abs(value) for value in chain_effects),
    )
