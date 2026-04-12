"""Trend plotting helpers for scalar workflow summaries over cardinality N."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt

from causal_set_engine.evaluation.layer_profile_study import LayerProfileEvaluationResult
from causal_set_engine.evaluation.midpoint_scaling_study import MidpointEvaluationResult
from causal_set_engine.evaluation.myrheim_meyer_study import MyrheimMeyerEvaluationResult


def _save_line_plot(
    *,
    x_values: tuple[int, ...],
    y_series: dict[str, tuple[float, ...]],
    title: str,
    y_label: str,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    for label, y_values in y_series.items():
        ax.plot(x_values, y_values, marker="o", linewidth=1.5, label=label)

    ax.set_xlabel("N")
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=140)
    plt.close(fig)
    return output_path


def write_myrheim_meyer_trend_plot(
    result: MyrheimMeyerEvaluationResult,
    output_path: Path,
) -> Path:
    """Plot Myrheim-Meyer mean summaries over N by Minkowski dimension."""
    series = {
        f"minkowski-{row.dimension}d": row.myrheim_meyer_means
        for row in result.dimension_trends
    }
    n_values = result.dimension_trends[0].n_values if result.dimension_trends else ()
    return _save_line_plot(
        x_values=n_values,
        y_series=series,
        title="Myrheim-Meyer trend by reference dimension",
        y_label="mean Myrheim-Meyer estimate",
        output_path=output_path,
    )


def write_midpoint_dimension_trend_plot(
    result: MidpointEvaluationResult,
    output_path: Path,
) -> Path:
    """Plot midpoint-derived dimension summaries over N for all models."""
    grouped: dict[str, list[tuple[int, float]]] = {}
    for row in result.per_model_n:
        grouped.setdefault(row.model, []).append((row.n, row.midpoint_dimension_estimate.mean))

    sorted_grouped = {
        model: tuple(value for _, value in sorted(model_rows, key=lambda item: item[0]))
        for model, model_rows in grouped.items()
    }
    n_values = tuple(sorted({row.n for row in result.per_model_n}))
    return _save_line_plot(
        x_values=n_values,
        y_series=sorted_grouped,
        title="Midpoint-derived dimension trend by model",
        y_label="mean midpoint-derived dimension",
        output_path=output_path,
    )


def write_layer_profile_metric_trend_plot(
    result: LayerProfileEvaluationResult,
    output_path: Path,
) -> Path:
    """Plot occupied-layer summary means over N for all models."""
    grouped: dict[str, list[tuple[int, float]]] = {}
    for row in result.per_model_n:
        grouped.setdefault(row.model, []).append((row.n, row.occupied_layers.mean))

    series = {
        model: tuple(value for _, value in sorted(model_rows, key=lambda item: item[0]))
        for model, model_rows in grouped.items()
    }
    n_values = tuple(sorted({row.n for row in result.per_model_n}))

    return _save_line_plot(
        x_values=n_values,
        y_series=series,
        title="Layer-profile occupied-layer trend by model",
        y_label="mean occupied layer count",
        output_path=output_path,
    )
