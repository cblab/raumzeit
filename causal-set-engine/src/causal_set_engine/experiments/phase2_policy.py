"""Explicit, conservative phase-2a evaluation gate policy.

This module keeps phase-2a decision logic narrow and auditable:
- fixed thresholds only
- no hidden tuning
- deterministic pass/fail criteria
"""

from __future__ import annotations

from dataclasses import dataclass

from causal_set_engine.evaluation.scoring import DiagnosticQuality


@dataclass(frozen=True)
class Phase2GateThresholds:
    """Fixed thresholds for opening phase-2a dynamics evaluation."""

    # Primary diagnostic minimums.
    min_usefulness_score: float = 0.70
    min_effect_size_abs: float = 0.90
    min_interval_separation: float = 0.60

    # Discriminator quality minimums.
    min_sign_consistency: float = 0.75
    min_trend_consistency: float = 0.65

    # Robustness minimums across calibration checks.
    min_primary_metric_count: int = 1
    min_null_models: int = 2
    min_seeds: int = 6
    min_n_values: int = 2


@dataclass(frozen=True)
class Phase2GateInput:
    """Observed calibration evidence needed to evaluate candidate dynamics."""

    ranked_diagnostics: list[DiagnosticQuality]
    null_model_count: int
    seeds_per_model: int
    n_values_count: int


@dataclass(frozen=True)
class Phase2GateDecision:
    """Go/no-go decision and transparent reason list."""

    go: bool
    primary_metrics: tuple[str, ...]
    failures: tuple[str, ...]


def _is_primary(diagnostic: DiagnosticQuality, thresholds: Phase2GateThresholds) -> bool:
    """Whether one diagnostic is primary enough for phase-2 evaluation."""

    return (
        diagnostic.usefulness_score >= thresholds.min_usefulness_score
        and diagnostic.effect_size_abs >= thresholds.min_effect_size_abs
        and diagnostic.interval_separation >= thresholds.min_interval_separation
        and diagnostic.sign_consistency >= thresholds.min_sign_consistency
        and diagnostic.trend_consistency >= thresholds.min_trend_consistency
    )


def evaluate_phase2_gate(
    gate_input: Phase2GateInput,
    thresholds: Phase2GateThresholds | None = None,
) -> Phase2GateDecision:
    """Apply explicit phase-2a go/no-go criteria.

    Go only if:
    1) enough diagnostics qualify as primary;
    2) calibration robustness coverage is sufficient across null models,
       seeds, and size trends.
    """

    threshold_values = thresholds or Phase2GateThresholds()

    primary = [
        row.metric
        for row in gate_input.ranked_diagnostics
        if _is_primary(row, threshold_values)
    ]

    failures: list[str] = []
    if len(primary) < threshold_values.min_primary_metric_count:
        failures.append(
            "insufficient-primary-diagnostics"
        )
    if gate_input.null_model_count < threshold_values.min_null_models:
        failures.append("insufficient-null-model-coverage")
    if gate_input.seeds_per_model < threshold_values.min_seeds:
        failures.append("insufficient-seed-coverage")
    if gate_input.n_values_count < threshold_values.min_n_values:
        failures.append("insufficient-size-trend-coverage")

    return Phase2GateDecision(
        go=not failures,
        primary_metrics=tuple(primary),
        failures=tuple(failures),
    )
