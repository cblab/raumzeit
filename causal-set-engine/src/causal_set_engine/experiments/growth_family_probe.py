"""Phase-2 probing wired through strict phase-1.75 discriminators."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Callable

from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.evaluation.metrics import (
    DEFAULT_METRICS,
    MetricRow,
    pair_quality_rows,
    run_once,
)
from causal_set_engine.evaluation.sampling import edge_count_from_density
from causal_set_engine.evaluation.scoring import (
    PairQuality,
    aggregate_diagnostic_quality,
    build_combined_score,
)
from causal_set_engine.policies.policy_gate import (
    Phase2GateDecision,
    Phase2GateInput,
    evaluate_phase2_gate,
)
from causal_set_engine.generators.minkowski_2d import generate_minkowski_2d
from causal_set_engine.generators.null_models import generate_fixed_edge_count_poset
from causal_set_engine.generators.phase2_minimal_growth import generate_minimal_growth_causal_set
from causal_set_engine.generators.phase2_minimal_growth import (
    PRIMITIVE_DYNAMICS_FAMILIES,
    PrimitiveDynamicsFamily,
    generate_age_biased_growth_causal_set,
    generate_bernoulli_forward_growth_causal_set,
    generate_sparse_forward_growth_causal_set,
    generate_window_forward_growth_causal_set,
)
from causal_set_engine.generators.random_poset import generate_random_poset

METRICS: tuple[str, ...] = DEFAULT_METRICS


@dataclass(frozen=True)
class GrowthFamilyProbeResult:
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


@dataclass(frozen=True)
class FamilyComparisonRow:
    family_name: str
    parameters: tuple[tuple[str, str], ...]
    mechanism: str
    artifact_risk: str
    gate_decision: str
    primary_diagnostic_performance: str
    relative_to_minkowski: str
    relative_to_nulls: str
    n_trend_behavior: str
    mean_score: float


@dataclass(frozen=True)
class GrowthFamilyComparisonResult:
    gate_decision: Phase2GateDecision
    family_rows: tuple[FamilyComparisonRow, ...]


def _run_once(cset: CausalSet, interval_samples: int, seed: int) -> MetricRow:
    row = run_once(cset, interval_samples, seed)
    row.pop("interval_median", None)
    return row


def _batch_rows(
    generator,
    n: int,
    runs: int,
    seed_start: int,
    interval_samples: int,
) -> list[MetricRow]:
    return [
        _run_once(generator(n, seed), interval_samples, seed)
        for seed in range(seed_start, seed_start + runs)
    ]


def _edge_count_from_density(n: int, density: float) -> int:
    return edge_count_from_density(n, density)


def _family_catalog() -> dict[str, PrimitiveDynamicsFamily]:
    return {item.name: item for item in PRIMITIVE_DYNAMICS_FAMILIES}


def _family_generators(
    *,
    growth_link_probability: float,
    sparse_base_link_probability: float,
    age_bias_mode: str,
    lookback_window: int,
) -> dict[str, tuple[dict[str, str], Callable[[int, int], CausalSet]]]:
    return {
        "bernoulli-forward": (
            {"link_probability": f"{growth_link_probability:.3f}"},
            lambda n_val, seed: generate_bernoulli_forward_growth_causal_set(
                n=n_val,
                link_probability=growth_link_probability,
                seed=seed,
            ),
        ),
        "sparse-forward": (
            {"base_link_probability": f"{sparse_base_link_probability:.3f}"},
            lambda n_val, seed: generate_sparse_forward_growth_causal_set(
                n=n_val,
                base_link_probability=sparse_base_link_probability,
                seed=seed,
            ),
        ),
        "age-biased-forward": (
            {
                "link_probability": f"{growth_link_probability:.3f}",
                "age_bias": age_bias_mode,
            },
            lambda n_val, seed: generate_age_biased_growth_causal_set(
                n=n_val,
                link_probability=growth_link_probability,
                age_bias=age_bias_mode,
                seed=seed,
            ),
        ),
        "window-forward": (
            {
                "link_probability": f"{growth_link_probability:.3f}",
                "lookback_window": str(lookback_window),
            },
            lambda n_val, seed: generate_window_forward_growth_causal_set(
                n=n_val,
                link_probability=growth_link_probability,
                lookback_window=lookback_window,
                seed=seed,
            ),
        ),
    }


def _pair_quality_rows(
    n_values: list[int],
    mk_rows_by_n: dict[int, list[MetricRow]],
    null_rows_by_n: dict[int, list[MetricRow]],
    null_model_name: str,
) -> list[PairQuality]:
    return pair_quality_rows(
        n_values=n_values,
        mk_rows_by_n=mk_rows_by_n,
        null_rows_by_n=null_rows_by_n,
        null_model_name=null_model_name,
        metrics=METRICS,
    )


def evaluate_growth_family_probe(
    *,
    n_values: list[int],
    runs: int = 8,
    seed_start: int = 100,
    interval_samples: int = 50,
    null_p: float = 0.2,
    null_edge_density: float = 0.2,
    growth_link_probability: float = 0.2,
) -> GrowthFamilyProbeResult:
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
        growth_by_n[n] = _batch_rows(lambda n_val, seed: generate_minimal_growth_causal_set(n=n_val, link_probability=growth_link_probability, seed=seed), n, runs, seed_start, interval_samples)

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

    return GrowthFamilyProbeResult(
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


def evaluate_growth_family_comparison(
    *,
    n_values: list[int],
    runs: int = 8,
    seed_start: int = 100,
    interval_samples: int = 50,
    null_p: float = 0.2,
    null_edge_density: float = 0.2,
    growth_link_probability: float = 0.2,
    sparse_base_link_probability: float = 0.25,
    age_bias_mode: str = "older",
    lookback_window: int = 8,
    family_names: list[str] | None = None,
) -> GrowthFamilyComparisonResult:
    """Compare primitive dynamics families under one strict gate workflow."""
    mk_by_n: dict[int, list[MetricRow]] = {}
    random_by_n: dict[int, list[MetricRow]] = {}
    fixed_by_n: dict[int, list[MetricRow]] = {}

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
    primary = set(gate.primary_metrics)

    all_rows = [rows for rows in mk_by_n.values()] + [rows for rows in random_by_n.values()] + [rows for rows in fixed_by_n.values()]
    center: dict[str, float] = {}
    scale: dict[str, float] = {}
    for metric in METRICS:
        values = [row[metric] for rows in all_rows for row in rows]
        center[metric] = statistics.fmean(values)
        scale[metric] = statistics.stdev(values) if len(values) > 1 else 1.0
        if scale[metric] <= 0:
            scale[metric] = 1.0

    family_specs = _family_catalog()
    generators = _family_generators(
        growth_link_probability=growth_link_probability,
        sparse_base_link_probability=sparse_base_link_probability,
        age_bias_mode=age_bias_mode,
        lookback_window=lookback_window,
    )
    selected = family_names or list(generators.keys())
    invalid = [name for name in selected if name not in generators]
    if invalid:
        raise ValueError(f"unknown family names: {', '.join(sorted(invalid))}")

    rows: list[FamilyComparisonRow] = []
    for family_name in selected:
        parameters, generator = generators[family_name]
        family_by_n: dict[int, list[MetricRow]] = {}
        for n in n_values:
            family_by_n[n] = _batch_rows(generator, n, runs, seed_start, interval_samples)

        family_scores: list[float] = []
        score_by_n: dict[int, float] = {}
        for n in sorted(family_by_n):
            batch_scores: list[float] = []
            for row in family_by_n[n]:
                weighted = [
                    combined.orientation[metric] * ((row[metric] - center[metric]) / scale[metric])
                    for metric in METRICS
                ]
                batch_scores.append(statistics.fmean(weighted))
            score_by_n[n] = statistics.fmean(batch_scores)
            family_scores.extend(batch_scores)
        family_mean = statistics.fmean(family_scores)

        if family_mean > combined.minkowski_mean:
            relative_to_mk = "above-minkowski-reference"
        elif family_mean < combined.minkowski_mean:
            relative_to_mk = "below-minkowski-reference"
        else:
            relative_to_mk = "tied-minkowski-reference"

        null_mean = statistics.fmean([combined.random_mean, combined.fixed_edge_mean])
        if family_mean > null_mean:
            relative_to_nulls = "toward-manifold-like-vs-nulls"
        elif family_mean < null_mean:
            relative_to_nulls = "away-from-manifold-like-vs-nulls"
        else:
            relative_to_nulls = "neutral-vs-nulls"

        ordered_n = sorted(score_by_n)
        if len(ordered_n) > 1:
            drift = score_by_n[ordered_n[-1]] - score_by_n[ordered_n[0]]
            if drift > 0.1:
                n_trend = "upward-score-drift-with-N"
            elif drift < -0.1:
                n_trend = "downward-score-drift-with-N"
            else:
                n_trend = "flat-score-vs-N"
        else:
            n_trend = "insufficient-N-range"

        mk_primary_gap = statistics.fmean(
            abs(
                statistics.fmean([row[metric] for row in family_by_n[n]])
                - statistics.fmean([row[metric] for row in mk_by_n[n]])
            )
            for n in n_values
            for metric in primary
        ) if primary else 0.0
        null_primary_gap = statistics.fmean(
            abs(
                statistics.fmean([row[metric] for row in random_by_n[n]] + [row[metric] for row in fixed_by_n[n]])
                - statistics.fmean([row[metric] for row in mk_by_n[n]])
            )
            for n in n_values
            for metric in primary
        ) if primary else 0.0
        if mk_primary_gap < null_primary_gap:
            primary_perf = "closer-than-null-average-on-primary"
        elif mk_primary_gap > null_primary_gap:
            primary_perf = "farther-than-null-average-on-primary"
        else:
            primary_perf = "tied-with-null-average-on-primary"

        metadata = family_specs[family_name]
        rows.append(
            FamilyComparisonRow(
                family_name=family_name,
                parameters=tuple((k, v) for k, v in sorted(parameters.items())),
                mechanism=metadata.mechanism,
                artifact_risk=metadata.anticipated_artifact_risk,
                gate_decision="GO" if gate.go else "NO-GO",
                primary_diagnostic_performance=primary_perf,
                relative_to_minkowski=relative_to_mk,
                relative_to_nulls=relative_to_nulls,
                n_trend_behavior=n_trend,
                mean_score=family_mean,
            )
        )

    return GrowthFamilyComparisonResult(
        gate_decision=gate,
        family_rows=tuple(rows),
    )
