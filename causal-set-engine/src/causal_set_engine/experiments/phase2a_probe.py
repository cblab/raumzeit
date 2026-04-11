"""Phase-2a minimal dynamics probe wiring through phase-1.75 discriminators."""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.diagnostics.basic import (
    estimate_dimension_chain_height,
    longest_chain_length,
    relation_density,
    sampled_interval_statistics,
)
from causal_set_engine.experiments.decision_metrics import (
    PairQuality,
    aggregate_diagnostic_quality,
    build_combined_score,
    interval_overlap_fraction,
    mean_difference,
    sign_consistency_fraction,
    standardized_effect_size,
)
from causal_set_engine.experiments.phase2_policy import (
    Phase2GateDecision,
    Phase2GateInput,
    evaluate_phase2_gate,
)
from causal_set_engine.generators.minkowski_2d import generate_minkowski_2d
from causal_set_engine.generators.null_models import generate_fixed_edge_count_poset
from causal_set_engine.generators.phase2_minimal_growth import generate_minimal_growth_causal_set
from causal_set_engine.generators.random_poset import generate_random_poset

MetricRow = dict[str, float]
METRICS: tuple[str, ...] = (
    "dimension_estimate",
    "longest_chain_length",
    "interval_mean",
    "relation_density",
)


@dataclass(frozen=True)
class Phase2ProbeResult:
    """Compact and testable result schema for phase-2a probing."""

    gate_decision: Phase2GateDecision
    diagnostic_bands: tuple[tuple[str, str], ...]
    combined_min_effect: float
    best_single_worst_case_effect: float
    minimal_growth_mean_score: float
    minkowski_mean_score: float
    random_mean_score: float
    fixed_edge_mean_score: float
    relative_to_minkowski: str
    relative_to_nulls: str


def _run_once(cset: CausalSet, interval_samples: int, seed: int) -> MetricRow:
    interval_stats = sampled_interval_statistics(cset, pairs=interval_samples, seed=seed)
    return {
        "relation_density": relation_density(cset),
        "longest_chain_length": float(longest_chain_length(cset)),
        "dimension_estimate": estimate_dimension_chain_height(cset),
        "interval_mean": float(interval_stats["mean"] or 0.0),
    }


def _batch_rows(
    generator,
    n: int,
    runs: int,
    seed_start: int,
    interval_samples: int,
) -> list[MetricRow]:
    rows: list[MetricRow] = []
    for seed in range(seed_start, seed_start + runs):
        rows.append(_run_once(generator(n, seed), interval_samples, seed))
    return rows


def _edge_count_from_density(n: int, density: float) -> int:
    max_forward_edges = n * (n - 1) // 2
    return int(round(density * max_forward_edges))


def _pair_quality_rows(
    n_values: list[int],
    mk_rows_by_n: dict[int, list[MetricRow]],
    null_rows_by_n: dict[int, list[MetricRow]],
    null_model_name: str,
) -> list[PairQuality]:
    rows: list[PairQuality] = []
    for n in n_values:
        mk_rows = mk_rows_by_n[n]
        null_rows = null_rows_by_n[n]
        for metric in METRICS:
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


def evaluate_minimal_growth_probe(
    *,
    n_values: list[int],
    runs: int = 8,
    seed_start: int = 100,
    interval_samples: int = 50,
    null_p: float = 0.2,
    null_edge_density: float = 0.2,
    growth_link_probability: float = 0.2,
) -> Phase2ProbeResult:
    """Run phase-2a probe with conservative claims.

    The gate is built from phase-1.75 discriminator quality only.
    Minimal growth is then scored against Minkowski and null baselines.
    """

    mk_by_n: dict[int, list[MetricRow]] = {}
    random_by_n: dict[int, list[MetricRow]] = {}
    fixed_by_n: dict[int, list[MetricRow]] = {}
    growth_by_n: dict[int, list[MetricRow]] = {}

    for n in n_values:
        mk_by_n[n] = _batch_rows(lambda n_val, seed: generate_minkowski_2d(n=n_val, seed=seed)[0], n, runs, seed_start, interval_samples)
        random_by_n[n] = _batch_rows(
            lambda n_val, seed: generate_random_poset(n=n_val, relation_probability=null_p, seed=seed),
            n,
            runs,
            seed_start,
            interval_samples,
        )
        fixed_edge_count = _edge_count_from_density(n, null_edge_density)
        fixed_by_n[n] = _batch_rows(
            lambda n_val, seed: generate_fixed_edge_count_poset(n=n_val, edge_count=fixed_edge_count, seed=seed),
            n,
            runs,
            seed_start,
            interval_samples,
        )
        growth_by_n[n] = _batch_rows(
            lambda n_val, seed: generate_minimal_growth_causal_set(
                n=n_val,
                link_probability=growth_link_probability,
                seed=seed,
            ),
            n,
            runs,
            seed_start,
            interval_samples,
        )

    pair_quality = _pair_quality_rows(n_values, mk_by_n, random_by_n, "random-poset")
    pair_quality.extend(_pair_quality_rows(n_values, mk_by_n, fixed_by_n, "fixed-edge-poset"))
    ranked = aggregate_diagnostic_quality(pair_quality)

    gate = evaluate_phase2_gate(
        Phase2GateInput(
            ranked_diagnostics=ranked,
            null_model_count=2,
            seeds_per_model=runs,
            n_values_count=len(n_values),
        )
    )

    combined = build_combined_score(METRICS, mk_by_n, random_by_n, fixed_by_n)
    single_best_min_effect = max(
        min(abs(item.effect_size) for item in pair_quality if item.metric == metric_name)
        for metric_name in METRICS
    )
    combined_min_effect = min(abs(combined.mk_vs_random_effect), abs(combined.mk_vs_fixed_effect))

    score_orientation = combined.orientation

    def _score_rows(rows_by_n: dict[int, list[MetricRow]]) -> list[float]:
        all_rows = [rows for rows in mk_by_n.values()] + [rows for rows in random_by_n.values()] + [rows for rows in fixed_by_n.values()]
        center: dict[str, float] = {}
        scale: dict[str, float] = {}
        for metric in METRICS:
            values = [row[metric] for rows in all_rows for row in rows]
            center[metric] = statistics.fmean(values)
            scale[metric] = statistics.stdev(values) if len(values) > 1 else 1.0
            if scale[metric] <= 0:
                scale[metric] = 1.0

        scores: list[float] = []
        for n in sorted(rows_by_n):
            for row in rows_by_n[n]:
                weighted = [
                    score_orientation[metric] * ((row[metric] - center[metric]) / scale[metric])
                    for metric in METRICS
                ]
                scores.append(statistics.fmean(weighted))
        return scores

    growth_scores = _score_rows(growth_by_n)
    growth_mean = statistics.fmean(growth_scores)

    if growth_mean > combined.minkowski_mean:
        relative_to_minkowski = "above-minkowski-reference"
    elif growth_mean < combined.minkowski_mean:
        relative_to_minkowski = "below-minkowski-reference"
    else:
        relative_to_minkowski = "tied-minkowski-reference"

    null_mean = statistics.fmean([combined.random_mean, combined.fixed_edge_mean])
    if growth_mean > null_mean:
        relative_to_nulls = "toward-manifold-like-vs-nulls"
    elif growth_mean < null_mean:
        relative_to_nulls = "away-from-manifold-like-vs-nulls"
    else:
        relative_to_nulls = "neutral-vs-nulls"

    return Phase2ProbeResult(
        gate_decision=gate,
        diagnostic_bands=tuple((row.metric, row.band) for row in ranked),
        combined_min_effect=combined_min_effect,
        best_single_worst_case_effect=single_best_min_effect,
        minimal_growth_mean_score=growth_mean,
        minkowski_mean_score=combined.minkowski_mean,
        random_mean_score=combined.random_mean,
        fixed_edge_mean_score=combined.fixed_edge_mean,
        relative_to_minkowski=relative_to_minkowski,
        relative_to_nulls=relative_to_nulls,
    )
