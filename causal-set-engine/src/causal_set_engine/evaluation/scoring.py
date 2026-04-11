"""Conservative phase-1.75 decision utilities for discriminator quality."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

MetricRow = dict[str, float]


@dataclass(frozen=True)
class PairQuality:
    """Quality summary for one diagnostic against one null baseline at one size."""

    metric: str
    n: int
    null_model: str
    mean_difference: float
    effect_size: float
    interval_overlap: float
    sign_consistency: float


@dataclass(frozen=True)
class DiagnosticQuality:
    """Conservative quality summary aggregated over sizes and null baselines."""

    metric: str
    mean_difference_abs: float
    effect_size_abs: float
    interval_separation: float
    sign_consistency: float
    trend_consistency: float
    usefulness_score: float
    band: str


@dataclass(frozen=True)
class CombinedScoreResult:
    """Result of transparent linear combination of existing diagnostics."""

    metric_names: tuple[str, ...]
    orientation: dict[str, float]
    minkowski_mean: float
    random_mean: float
    fixed_edge_mean: float
    mk_vs_random_effect: float
    mk_vs_fixed_effect: float


def mean_difference(a_values: list[float], b_values: list[float]) -> float:
    return statistics.fmean(a_values) - statistics.fmean(b_values)


def standardized_effect_size(a_values: list[float], b_values: list[float]) -> float:
    """Simple Cohen-like effect size with pooled sample standard deviation."""

    mean_delta = mean_difference(a_values, b_values)
    if len(a_values) < 2 or len(b_values) < 2:
        return 0.0
    a_var = statistics.variance(a_values)
    b_var = statistics.variance(b_values)
    pooled_n = len(a_values) + len(b_values) - 2
    if pooled_n <= 0:
        return 0.0
    pooled_var = ((len(a_values) - 1) * a_var + (len(b_values) - 1) * b_var) / pooled_n
    if pooled_var <= 0:
        return 0.0
    return mean_delta / math.sqrt(pooled_var)


def interval_overlap_fraction(a_values: list[float], b_values: list[float]) -> float:
    """Range overlap proxy in [0, 1], where 0 means non-overlapping supports."""

    a_min, a_max = min(a_values), max(a_values)
    b_min, b_max = min(b_values), max(b_values)
    low = max(a_min, b_min)
    high = min(a_max, b_max)
    overlap = max(0.0, high - low)
    span = max(a_max, b_max) - min(a_min, b_min)
    if span <= 0:
        return 1.0
    return overlap / span


def sign_consistency_fraction(a_values: list[float], b_values: list[float]) -> float:
    """Consistency of the sign of paired differences across seeds/runs."""

    total = min(len(a_values), len(b_values))
    if total == 0:
        return 0.0
    pos = 0
    neg = 0
    for idx in range(total):
        delta = a_values[idx] - b_values[idx]
        if delta > 0:
            pos += 1
        elif delta < 0:
            neg += 1
    return max(pos, neg) / total


def trend_consistency(values_by_n: dict[int, float]) -> float:
    """Fraction of adjacent size steps that preserve non-decreasing absolute trend."""

    ordered = sorted(values_by_n.items())
    if len(ordered) < 2:
        return 1.0
    consistent = 0
    comparisons = 0
    for idx in range(1, len(ordered)):
        prev = abs(ordered[idx - 1][1])
        curr = abs(ordered[idx][1])
        comparisons += 1
        if curr + 1e-12 >= prev:
            consistent += 1
    return consistent / comparisons if comparisons else 1.0


def aggregate_diagnostic_quality(pair_rows: list[PairQuality]) -> list[DiagnosticQuality]:
    by_metric: dict[str, list[PairQuality]] = {}
    for row in pair_rows:
        by_metric.setdefault(row.metric, []).append(row)

    ranked: list[DiagnosticQuality] = []
    for metric, rows in by_metric.items():
        mean_abs = statistics.fmean(abs(row.mean_difference) for row in rows)
        effect_abs = statistics.fmean(abs(row.effect_size) for row in rows)
        interval_sep = statistics.fmean(1.0 - row.interval_overlap for row in rows)
        sign_consistency = statistics.fmean(row.sign_consistency for row in rows)

        trend_by_null: dict[str, float] = {}
        for null_name in {row.null_model for row in rows}:
            effects_by_n = {row.n: row.effect_size for row in rows if row.null_model == null_name}
            trend_by_null[null_name] = trend_consistency(effects_by_n)
        trend = min(trend_by_null.values()) if trend_by_null else 0.0

        usefulness = 0.35 * min(effect_abs / 1.5, 1.0) + 0.25 * interval_sep + 0.20 * sign_consistency + 0.20 * trend
        if usefulness >= 0.75:
            band = "strong discriminator"
        elif usefulness >= 0.50:
            band = "moderate discriminator"
        else:
            band = "exploratory signal"

        ranked.append(
            DiagnosticQuality(
                metric=metric,
                mean_difference_abs=mean_abs,
                effect_size_abs=effect_abs,
                interval_separation=interval_sep,
                sign_consistency=sign_consistency,
                trend_consistency=trend,
                usefulness_score=usefulness,
                band=band,
            )
        )

    return sorted(ranked, key=lambda row: row.usefulness_score, reverse=True)


def build_combined_score(
    metrics: tuple[str, ...],
    mk_rows_by_n: dict[int, list[MetricRow]],
    random_rows_by_n: dict[int, list[MetricRow]],
    fixed_rows_by_n: dict[int, list[MetricRow]],
) -> CombinedScoreResult:
    """Build linear combined manifold-likeness score from existing diagnostics only."""

    orientation: dict[str, float] = {}
    for metric in metrics:
        mk_values = [row[metric] for rows in mk_rows_by_n.values() for row in rows]
        null_values = [
            row[metric]
            for rows in random_rows_by_n.values()
            for row in rows
        ] + [row[metric] for rows in fixed_rows_by_n.values() for row in rows]
        orientation[metric] = 1.0 if statistics.fmean(mk_values) >= statistics.fmean(null_values) else -1.0

    all_rows = [rows for rows in mk_rows_by_n.values()] + [rows for rows in random_rows_by_n.values()] + [rows for rows in fixed_rows_by_n.values()]

    center: dict[str, float] = {}
    scale: dict[str, float] = {}
    for metric in metrics:
        values = [row[metric] for rows in all_rows for row in rows]
        center[metric] = statistics.fmean(values)
        scale[metric] = statistics.stdev(values) if len(values) > 1 else 1.0
        if scale[metric] <= 0:
            scale[metric] = 1.0

    def _score(rows_by_n: dict[int, list[MetricRow]]) -> list[float]:
        scores: list[float] = []
        for n in sorted(rows_by_n):
            for row in rows_by_n[n]:
                weighted = [
                    orientation[metric] * ((row[metric] - center[metric]) / scale[metric])
                    for metric in metrics
                ]
                scores.append(statistics.fmean(weighted))
        return scores

    mk_scores = _score(mk_rows_by_n)
    random_scores = _score(random_rows_by_n)
    fixed_scores = _score(fixed_rows_by_n)

    return CombinedScoreResult(
        metric_names=metrics,
        orientation=orientation,
        minkowski_mean=statistics.fmean(mk_scores),
        random_mean=statistics.fmean(random_scores),
        fixed_edge_mean=statistics.fmean(fixed_scores),
        mk_vs_random_effect=standardized_effect_size(mk_scores, random_scores),
        mk_vs_fixed_effect=standardized_effect_size(mk_scores, fixed_scores),
    )
