"""Artifact-aware controlled mechanism scan for age-biased-forward dynamics.

This scan is falsification-first: it preserves a strict policy gate derived from
discriminator quality metrics, then tests a small auditable parameter grid while reporting
artifact proxies alongside score behavior.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass

from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.evaluation.metrics import DEFAULT_METRICS, MetricRow, pair_quality_rows, run_once
from causal_set_engine.evaluation.sampling import batch_rows, edge_count_from_density
from causal_set_engine.diagnostics.artifact_proxies import compute_artifact_proxies
from causal_set_engine.policies.policy_gate import PolicyGateDecision, PolicyGateInput, evaluate_policy_gate
from causal_set_engine.generators.minkowski_2d import generate_minkowski_2d
from causal_set_engine.generators.null_models import generate_fixed_edge_count_poset
from causal_set_engine.generators.growth_family import generate_age_biased_growth_causal_set
from causal_set_engine.generators.random_poset import generate_random_poset
from causal_set_engine.evaluation.scoring import aggregate_diagnostic_quality, build_combined_score


METRICS: tuple[str, ...] = DEFAULT_METRICS


@dataclass(frozen=True)
class AgeBiasedScanSetting:
    link_density: float
    bias_strength: float


@dataclass(frozen=True)
class AgeBiasedScanRow:
    setting: AgeBiasedScanSetting
    gate_decision: str
    primary_diagnostic_profile: str
    relative_to_minkowski: str
    relative_to_nulls: str
    birth_order_dominance_proxy: float
    age_layering_stratification_proxy: float
    interpretation_label: str
    mean_score: float
    score_stddev: float


@dataclass(frozen=True)
class ArtifactAwareScanResult:
    gate_decision: PolicyGateDecision
    settings: tuple[AgeBiasedScanSetting, ...]
    rows: tuple[AgeBiasedScanRow, ...]


def _score_rows(
    rows_by_n: dict[int, list[MetricRow]],
    center: dict[str, float],
    scale: dict[str, float],
    orientation: dict[str, float],
) -> list[float]:
    scores: list[float] = []
    for n in sorted(rows_by_n):
        for row in rows_by_n[n]:
            weighted = [orientation[metric] * ((row[metric] - center[metric]) / scale[metric]) for metric in METRICS]
            scores.append(statistics.fmean(weighted))
    return scores


def _primary_profile(
    *,
    family_by_n: dict[int, list[MetricRow]],
    mk_by_n: dict[int, list[MetricRow]],
    random_by_n: dict[int, list[MetricRow]],
    fixed_by_n: dict[int, list[MetricRow]],
    primary_metrics: tuple[str, ...],
) -> str:
    if not primary_metrics:
        return "no-primary-metrics"

    mk_gap = statistics.fmean(
        abs(statistics.fmean([r[m] for r in family_by_n[n]]) - statistics.fmean([r[m] for r in mk_by_n[n]]))
        for n in family_by_n
        for m in primary_metrics
    )
    null_gap = statistics.fmean(
        abs(
            statistics.fmean([r[m] for r in random_by_n[n]] + [r[m] for r in fixed_by_n[n]])
            - statistics.fmean([r[m] for r in mk_by_n[n]])
        )
        for n in family_by_n
        for m in primary_metrics
    )
    if mk_gap < null_gap:
        return "closer-than-null-average-on-primary"
    if mk_gap > null_gap:
        return "farther-than-null-average-on-primary"
    return "tied-with-null-average-on-primary"


def _interpretation_label(
    *,
    primary_profile: str,
    relative_to_nulls: str,
    score_stddev: float,
    birth_order_proxy: float,
    layering_proxy: float,
) -> str:
    max_artifact = max(birth_order_proxy, layering_proxy)
    if score_stddev > 0.5:
        return "unstable"
    improved = (
        relative_to_nulls == "toward-manifold-like-vs-nulls"
        and primary_profile == "closer-than-null-average-on-primary"
    )
    if improved and max_artifact >= 0.6:
        return "improved but artifact-dominated"
    if improved and max_artifact < 0.4:
        return "mixed"
    if improved:
        return "mixed"
    return "no meaningful improvement"


def evaluate_age_biased_scan(
    *,
    n_values: list[int],
    runs: int = 8,
    seed_start: int = 100,
    interval_samples: int = 50,
    null_p: float = 0.2,
    null_edge_density: float = 0.2,
    link_density_grid: tuple[float, ...] = (0.16, 0.22, 0.28),
    bias_strength_grid: tuple[float, ...] = (0.0, 0.5, 1.0),
    age_bias_mode: str = "older",
) -> ArtifactAwareScanResult:
    """Run age-biased-forward only over a small explicit parameter grid."""

    if not link_density_grid:
        raise ValueError("link_density_grid must be non-empty")
    if not bias_strength_grid:
        raise ValueError("bias_strength_grid must be non-empty")

    mk_by_n: dict[int, list[MetricRow]] = {}
    random_by_n: dict[int, list[MetricRow]] = {}
    fixed_by_n: dict[int, list[MetricRow]] = {}

    for n in n_values:
        mk_by_n[n] = batch_rows(lambda n_val, seed: generate_minkowski_2d(n=n_val, seed=seed)[0], n, runs, seed_start, interval_samples)
        random_by_n[n] = batch_rows(
            lambda n_val, seed: generate_random_poset(n=n_val, relation_probability=null_p, seed=seed),
            n,
            runs,
            seed_start,
            interval_samples,
        )
        fixed_edge_count = edge_count_from_density(n, null_edge_density)
        fixed_by_n[n] = batch_rows(
            lambda n_val, seed: generate_fixed_edge_count_poset(n=n_val, edge_count=fixed_edge_count, seed=seed),
            n,
            runs,
            seed_start,
            interval_samples,
        )

    pair_quality = pair_quality_rows(
        n_values=n_values,
        mk_rows_by_n=mk_by_n,
        null_rows_by_n=random_by_n,
        null_model_name="random-poset",
        metrics=METRICS,
    )
    pair_quality.extend(
        pair_quality_rows(
            n_values=n_values,
            mk_rows_by_n=mk_by_n,
            null_rows_by_n=fixed_by_n,
            null_model_name="fixed-edge-poset",
            metrics=METRICS,
        )
    )
    ranked = aggregate_diagnostic_quality(pair_quality)
    gate = evaluate_policy_gate(
        PolicyGateInput(
            ranked_diagnostics=ranked,
            null_model_count=2,
            seeds_per_model=runs,
            n_values_count=len(n_values),
        )
    )
    combined = build_combined_score(METRICS, mk_by_n, random_by_n, fixed_by_n)

    all_rows = [rows for rows in mk_by_n.values()] + [rows for rows in random_by_n.values()] + [rows for rows in fixed_by_n.values()]
    center: dict[str, float] = {}
    scale: dict[str, float] = {}
    for metric in METRICS:
        values = [row[metric] for rows in all_rows for row in rows]
        center[metric] = statistics.fmean(values)
        scale[metric] = statistics.stdev(values) if len(values) > 1 else 1.0
        if scale[metric] <= 0:
            scale[metric] = 1.0

    settings = tuple(
        AgeBiasedScanSetting(link_density=link_density, bias_strength=bias_strength)
        for link_density in link_density_grid
        for bias_strength in bias_strength_grid
    )

    rows: list[AgeBiasedScanRow] = []
    for setting in settings:
        family_by_n: dict[int, list[MetricRow]] = {}
        proxy_birth_values: list[float] = []
        proxy_layer_values: list[float] = []

        for n in n_values:
            run_rows: list[MetricRow] = []
            for seed in range(seed_start, seed_start + runs):
                cset: CausalSet = generate_age_biased_growth_causal_set(
                    n=n,
                    link_probability=setting.link_density,
                    age_bias=age_bias_mode,
                    age_bias_strength=setting.bias_strength,
                    seed=seed,
                )
                run_rows.append(run_once(cset, interval_samples, seed))
                proxies = compute_artifact_proxies(cset)
                proxy_birth_values.append(proxies.birth_order_dominance)
                proxy_layer_values.append(proxies.age_layering_stratification)
            family_by_n[n] = run_rows

        scores = _score_rows(family_by_n, center, scale, combined.orientation)
        mean_score = statistics.fmean(scores)
        score_stddev = statistics.stdev(scores) if len(scores) > 1 else 0.0

        if mean_score > combined.minkowski_mean:
            relative_to_mk = "above-minkowski-reference"
        elif mean_score < combined.minkowski_mean:
            relative_to_mk = "below-minkowski-reference"
        else:
            relative_to_mk = "tied-minkowski-reference"

        null_mean = statistics.fmean([combined.random_mean, combined.fixed_edge_mean])
        if mean_score > null_mean:
            relative_to_nulls = "toward-manifold-like-vs-nulls"
        elif mean_score < null_mean:
            relative_to_nulls = "away-from-manifold-like-vs-nulls"
        else:
            relative_to_nulls = "neutral-vs-nulls"

        primary_profile = _primary_profile(
            family_by_n=family_by_n,
            mk_by_n=mk_by_n,
            random_by_n=random_by_n,
            fixed_by_n=fixed_by_n,
            primary_metrics=gate.primary_metrics,
        )

        birth_proxy = statistics.fmean(proxy_birth_values)
        layering_proxy = statistics.fmean(proxy_layer_values)
        interpretation = _interpretation_label(
            primary_profile=primary_profile,
            relative_to_nulls=relative_to_nulls,
            score_stddev=score_stddev,
            birth_order_proxy=birth_proxy,
            layering_proxy=layering_proxy,
        )

        rows.append(
            AgeBiasedScanRow(
                setting=setting,
                gate_decision="GO" if gate.go else "NO-GO",
                primary_diagnostic_profile=primary_profile,
                relative_to_minkowski=relative_to_mk,
                relative_to_nulls=relative_to_nulls,
                birth_order_dominance_proxy=birth_proxy,
                age_layering_stratification_proxy=layering_proxy,
                interpretation_label=interpretation,
                mean_score=mean_score,
                score_stddev=score_stddev,
            )
        )

    return ArtifactAwareScanResult(gate_decision=gate, settings=settings, rows=tuple(rows))
