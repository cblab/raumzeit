"""Reusable metric extraction for Myrheim-Meyer evaluation studies."""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.evaluation.metrics import MetricRow, run_once
from causal_set_engine.evaluation.sampling import edge_count_from_density
from causal_set_engine.evaluation.scoring import standardized_effect_size
from causal_set_engine.generators.minkowski_2d import generate_minkowski_2d
from causal_set_engine.generators.minkowski_3d import generate_minkowski_3d
from causal_set_engine.generators.minkowski_4d import generate_minkowski_4d
from causal_set_engine.generators.null_models import generate_fixed_edge_count_poset
from causal_set_engine.generators.random_poset import generate_random_poset


@dataclass(frozen=True)
class MetricSummary:
    mean: float
    stdev: float


@dataclass(frozen=True)
class DimensionNRow:
    dimension: int
    n: int
    myrheim_meyer: MetricSummary
    chain_height_proxy: MetricSummary


@dataclass(frozen=True)
class SeparationRow:
    dimension: int
    n: int
    null_model: str
    myrheim_meyer_effect_size: float
    chain_proxy_effect_size: float


@dataclass(frozen=True)
class DimensionTrendRow:
    dimension: int
    n_values: tuple[int, ...]
    myrheim_meyer_means: tuple[float, ...]


@dataclass(frozen=True)
class MyrheimMeyerEvaluationResult:
    per_dimension_n: tuple[DimensionNRow, ...]
    separation_rows: tuple[SeparationRow, ...]
    dimension_trends: tuple[DimensionTrendRow, ...]
    monotone_by_n: tuple[tuple[int, bool], ...]
    conservative_min_effect_myrheim_meyer: float
    conservative_min_effect_chain_proxy: float


def _batch_rows(
    generator,
    n: int,
    runs: int,
    seed_start: int,
    interval_samples: int,
) -> list[MetricRow]:
    return [
        run_once(generator(n, seed), interval_samples, seed)
        for seed in range(seed_start, seed_start + runs)
    ]


def _minkowski_generator(dimension: int):
    if dimension == 2:
        return lambda n, seed: generate_minkowski_2d(n=n, seed=seed)[0]
    if dimension == 3:
        return lambda n, seed: generate_minkowski_3d(n=n, seed=seed)[0]
    if dimension == 4:
        return lambda n, seed: generate_minkowski_4d(n=n, seed=seed)[0]
    raise ValueError("dimension must be one of {2, 3, 4}")


def _summary(values: list[float]) -> MetricSummary:
    return MetricSummary(
        mean=statistics.fmean(values),
        stdev=statistics.stdev(values) if len(values) > 1 else 0.0,
    )


def evaluate_myrheim_meyer_study(
    *,
    dimensions: tuple[int, ...],
    n_values: tuple[int, ...],
    runs: int = 8,
    seed_start: int = 100,
    interval_samples: int = 50,
    null_p: float = 0.2,
    null_edge_density: float = 0.2,
) -> MyrheimMeyerEvaluationResult:
    """Evaluate Myrheim-Meyer behavior across Minkowski references and null models."""
    mk_rows_by_dim_n: dict[tuple[int, int], list[MetricRow]] = {}
    random_rows_by_n: dict[int, list[MetricRow]] = {}
    fixed_rows_by_n: dict[int, list[MetricRow]] = {}

    for n in n_values:
        random_rows_by_n[n] = _batch_rows(
            lambda n_val, seed: generate_random_poset(
                n=n_val,
                relation_probability=null_p,
                seed=seed,
            ),
            n,
            runs,
            seed_start,
            interval_samples,
        )
        fixed_edge_count = edge_count_from_density(n, null_edge_density)
        fixed_rows_by_n[n] = _batch_rows(
            lambda n_val, seed: generate_fixed_edge_count_poset(
                n=n_val,
                edge_count=fixed_edge_count,
                seed=seed,
            ),
            n,
            runs,
            seed_start,
            interval_samples,
        )

        for dimension in dimensions:
            mk_rows_by_dim_n[(dimension, n)] = _batch_rows(
                _minkowski_generator(dimension),
                n,
                runs,
                seed_start,
                interval_samples,
            )

    per_dimension_n: list[DimensionNRow] = []
    separation_rows: list[SeparationRow] = []
    trends: list[DimensionTrendRow] = []
    monotone_by_n: list[tuple[int, bool]] = []
    mm_effects: list[float] = []
    chain_effects: list[float] = []

    for dimension in dimensions:
        means_by_n: list[float] = []
        for n in n_values:
            mk_rows = mk_rows_by_dim_n[(dimension, n)]
            mm_values = [row["myrheim_meyer_dimension"] for row in mk_rows]
            chain_values = [row["dimension_estimate"] for row in mk_rows]
            means_by_n.append(statistics.fmean(mm_values))

            per_dimension_n.append(
                DimensionNRow(
                    dimension=dimension,
                    n=n,
                    myrheim_meyer=_summary(mm_values),
                    chain_height_proxy=_summary(chain_values),
                )
            )

            random_mm = [row["myrheim_meyer_dimension"] for row in random_rows_by_n[n]]
            fixed_mm = [row["myrheim_meyer_dimension"] for row in fixed_rows_by_n[n]]
            random_chain = [row["dimension_estimate"] for row in random_rows_by_n[n]]
            fixed_chain = [row["dimension_estimate"] for row in fixed_rows_by_n[n]]

            random_mm_effect = standardized_effect_size(mm_values, random_mm)
            fixed_mm_effect = standardized_effect_size(mm_values, fixed_mm)
            random_chain_effect = standardized_effect_size(chain_values, random_chain)
            fixed_chain_effect = standardized_effect_size(chain_values, fixed_chain)

            mm_effects.extend([random_mm_effect, fixed_mm_effect])
            chain_effects.extend([random_chain_effect, fixed_chain_effect])

            separation_rows.append(
                SeparationRow(
                    dimension=dimension,
                    n=n,
                    null_model="random-poset",
                    myrheim_meyer_effect_size=random_mm_effect,
                    chain_proxy_effect_size=random_chain_effect,
                )
            )
            separation_rows.append(
                SeparationRow(
                    dimension=dimension,
                    n=n,
                    null_model="fixed-edge-poset",
                    myrheim_meyer_effect_size=fixed_mm_effect,
                    chain_proxy_effect_size=fixed_chain_effect,
                )
            )

        trends.append(
            DimensionTrendRow(
                dimension=dimension,
                n_values=n_values,
                myrheim_meyer_means=tuple(means_by_n),
            )
        )

    for n in n_values:
        dim_means = [
            statistics.fmean(
                row["myrheim_meyer_dimension"]
                for row in mk_rows_by_dim_n[(dimension, n)]
            )
            for dimension in dimensions
        ]
        monotone = all(dim_means[idx] < dim_means[idx + 1] for idx in range(len(dim_means) - 1))
        monotone_by_n.append((n, monotone))

    return MyrheimMeyerEvaluationResult(
        per_dimension_n=tuple(per_dimension_n),
        separation_rows=tuple(separation_rows),
        dimension_trends=tuple(trends),
        monotone_by_n=tuple(monotone_by_n),
        conservative_min_effect_myrheim_meyer=min(abs(value) for value in mm_effects),
        conservative_min_effect_chain_proxy=min(abs(value) for value in chain_effects),
    )
