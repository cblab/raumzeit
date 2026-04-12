"""Reusable global interval-statistics study helpers."""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from causal_set_engine.evaluation.sampling import edge_count_from_density
from causal_set_engine.generators.minkowski_2d import generate_minkowski_2d
from causal_set_engine.generators.minkowski_3d import generate_minkowski_3d
from causal_set_engine.generators.minkowski_4d import generate_minkowski_4d
from causal_set_engine.generators.null_models import generate_fixed_edge_count_poset
from causal_set_engine.generators.random_poset import generate_random_poset
from causal_set_engine.observables.cst.intervals import compute_interval_abundances


@dataclass(frozen=True)
class IntervalAbundanceSummary:
    """Summary statistics for one interval-size bin across repeated runs."""

    k: int
    mean_count: float
    stdev_count: float
    mean_density: float


@dataclass(frozen=True)
class ModelNIntervalRow:
    """Interval abundance summaries for one model at one cardinality."""

    model: str
    n: int
    k_summaries: tuple[IntervalAbundanceSummary, ...]
    mean_comparable_pairs: float


@dataclass(frozen=True)
class IntervalStudyResult:
    """Structured result for focused global interval-evaluation studies."""

    rows: tuple[ModelNIntervalRow, ...]


def _generator_rows(
    *,
    model: str,
    generator,
    n: int,
    runs: int,
    seed_start: int,
    k_max: int,
) -> ModelNIntervalRow:
    histograms: list[dict[int, int]] = []
    totals: list[int] = []

    for seed in range(seed_start, seed_start + runs):
        cset = generator(n, seed)
        histogram = compute_interval_abundances(cset, k_max=k_max)
        total = sum(histogram.values())
        histograms.append(histogram)
        totals.append(total)

    summaries: list[IntervalAbundanceSummary] = []
    for k in range(k_max + 1):
        counts = [hist[k] for hist in histograms]
        densities = [count / total if total > 0 else 0.0 for count, total in zip(counts, totals)]
        summaries.append(
            IntervalAbundanceSummary(
                k=k,
                mean_count=statistics.fmean(counts),
                stdev_count=statistics.stdev(counts) if len(counts) > 1 else 0.0,
                mean_density=statistics.fmean(densities),
            )
        )

    return ModelNIntervalRow(
        model=model,
        n=n,
        k_summaries=tuple(summaries),
        mean_comparable_pairs=statistics.fmean(totals),
    )


def _minkowski_generator(dimension: int):
    if dimension == 2:
        return lambda n, seed: generate_minkowski_2d(n=n, seed=seed)[0]
    if dimension == 3:
        return lambda n, seed: generate_minkowski_3d(n=n, seed=seed)[0]
    if dimension == 4:
        return lambda n, seed: generate_minkowski_4d(n=n, seed=seed)[0]
    raise ValueError("dimension must be one of {2, 3, 4}")


def evaluate_global_interval_statistics(
    *,
    dimensions: tuple[int, ...],
    n_values: tuple[int, ...],
    runs: int = 8,
    seed_start: int = 100,
    null_p: float = 0.2,
    null_edge_density: float = 0.2,
    k_max: int = 5,
) -> IntervalStudyResult:
    """Evaluate global interval abundances for Minkowski references vs null baselines.

    Scope is intentionally global and descriptive:
    - counts and densities of interval sizes among ordered comparable pairs,
    - links identified as ``k=0`` (0-element intervals),
    - no local curvature interpretation and no action-based logic.
    """
    rows: list[ModelNIntervalRow] = []

    for n in n_values:
        fixed_edge_count = edge_count_from_density(n, null_edge_density)
        rows.append(
            _generator_rows(
                model="null-random-poset",
                generator=lambda n_val, seed: generate_random_poset(
                    n=n_val,
                    relation_probability=null_p,
                    seed=seed,
                ),
                n=n,
                runs=runs,
                seed_start=seed_start,
                k_max=k_max,
            )
        )
        rows.append(
            _generator_rows(
                model="null-fixed-edge-poset",
                generator=lambda n_val, seed: generate_fixed_edge_count_poset(
                    n=n_val,
                    edge_count=fixed_edge_count,
                    seed=seed,
                ),
                n=n,
                runs=runs,
                seed_start=seed_start,
                k_max=k_max,
            )
        )

        for dimension in dimensions:
            rows.append(
                _generator_rows(
                    model=f"minkowski-{dimension}d",
                    generator=_minkowski_generator(dimension),
                    n=n,
                    runs=runs,
                    seed_start=seed_start,
                    k_max=k_max,
                )
            )

    return IntervalStudyResult(rows=tuple(rows))
