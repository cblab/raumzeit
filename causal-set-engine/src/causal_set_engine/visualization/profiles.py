"""Layer-profile plotting helpers for sampled interval structures."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt

from causal_set_engine.evaluation.layer_profile_study import (
    LayerProfileEvaluationResult,
    LayerProfileSample,
)


def plot_layer_profile(profile: tuple[int, ...], output_path: Path, *, title: str) -> Path:
    """Write a single interval layer-profile plot as a line chart."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 3.8))

    x_values = tuple(range(len(profile)))
    ax.plot(x_values, profile, marker="o", linewidth=1.5)
    ax.set_xlabel("layer index")
    ax.set_ylabel("element count")
    ax.set_title(title)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=140)
    plt.close(fig)
    return output_path


def write_layer_profile_sample_plots(
    samples: tuple[LayerProfileSample, ...],
    output_dir: Path,
    *,
    max_plots: int = 12,
) -> tuple[Path, ...]:
    """Write plots for a deterministic prefix of sampled interval profiles."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths: list[Path] = []

    for sample in samples[:max_plots]:
        if not sample.profile:
            continue
        filename = (
            f"layer_profile_{sample.model}_n{sample.n}_seed{sample.seed}_"
            f"interval{sample.interval_index}.png"
        )
        output_paths.append(
            plot_layer_profile(
                sample.profile,
                output_dir / filename,
                title=(
                    f"{sample.model} N={sample.n} seed={sample.seed} "
                    f"interval#{sample.interval_index}"
                ),
            )
        )

    return tuple(output_paths)


def write_layer_profile_summary_trend_plot(
    result: LayerProfileEvaluationResult,
    output_path: Path,
) -> Path:
    """Write a compact trend plot for boundary-fraction summary over N."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    grouped: dict[str, list[tuple[int, float]]] = {}
    for row in result.per_model_n:
        grouped.setdefault(row.model, []).append((row.n, row.boundary_fraction.mean))

    n_values = tuple(sorted({row.n for row in result.per_model_n}))

    fig, ax = plt.subplots(figsize=(7, 4))
    for model, pairs in grouped.items():
        y_values = [value for _, value in sorted(pairs, key=lambda item: item[0])]
        ax.plot(n_values, y_values, marker="o", linewidth=1.5, label=model)

    ax.set_xlabel("N")
    ax.set_ylabel("mean first/last layer mass fraction")
    ax.set_title("Layer-profile boundary-mass trend by model")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=140)
    plt.close(fig)
    return output_path
