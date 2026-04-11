"""Shared metric schemas and extraction helpers for evaluation workflows."""

from __future__ import annotations

from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.diagnostics.basic import (
    estimate_dimension_chain_height,
    longest_chain_length,
    relation_density,
    sampled_interval_statistics,
)
from causal_set_engine.observables.cst import estimate_myrheim_meyer_dimension
from causal_set_engine.evaluation.scoring import (
    PairQuality,
    interval_overlap_fraction,
    mean_difference,
    sign_consistency_fraction,
    standardized_effect_size,
)

MetricRow = dict[str, float]
DEFAULT_METRICS: tuple[str, ...] = (
    "dimension_estimate",
    "longest_chain_length",
    "interval_mean",
    "relation_density",
)


def run_once(cset: CausalSet, interval_samples: int, seed: int) -> MetricRow:
    """Extract the shared default metric row for one generated causal set."""
    interval_stats = sampled_interval_statistics(cset, pairs=interval_samples, seed=seed)
    return {
        "relation_density": relation_density(cset),
        "longest_chain_length": float(longest_chain_length(cset)),
        "dimension_estimate": estimate_dimension_chain_height(cset),
        "myrheim_meyer_dimension": estimate_myrheim_meyer_dimension(cset),
        "interval_mean": float(interval_stats["mean"] or 0.0),
        "interval_median": float(interval_stats["median"] or 0.0),
    }


def pair_quality_rows(
    *,
    n_values: list[int],
    mk_rows_by_n: dict[int, list[MetricRow]],
    null_rows_by_n: dict[int, list[MetricRow]],
    null_model_name: str,
    metrics: tuple[str, ...] = DEFAULT_METRICS,
) -> list[PairQuality]:
    """Build per-metric quality rows for Minkowski-vs-null comparisons."""
    rows: list[PairQuality] = []
    for n in n_values:
        mk_rows = mk_rows_by_n[n]
        null_rows = null_rows_by_n[n]
        for metric in metrics:
            mk_values = [row[metric] for row in mk_rows]
            null_values = [row[metric] for row in null_rows]
            rows.append(
                PairQuality(
                    metric=metric,
                    n=n,
                    null_model=null_model_name,
                    mean_difference=mean_difference(mk_values, null_values),
                    effect_size=standardized_effect_size(mk_values, null_values),
                    interval_overlap=interval_overlap_fraction(mk_values, null_values),
                    sign_consistency=sign_consistency_fraction(mk_values, null_values),
                )
            )
    return rows
