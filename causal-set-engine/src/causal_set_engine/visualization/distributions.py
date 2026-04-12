"""Distribution plotting helpers for global interval-abundance results."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt

from causal_set_engine.evaluation.interval_study import IntervalStudyResult


def write_interval_abundance_comparison_plots(
    result: IntervalStudyResult,
    output_dir: Path,
    *,
    use_density: bool = True,
) -> tuple[Path, ...]:
    """Write one grouped bar plot per N for interval abundance by k across models."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths: list[Path] = []

    n_values = sorted({row.n for row in result.rows})
    for n in n_values:
        rows_for_n = [row for row in result.rows if row.n == n]
        if not rows_for_n:
            continue

        models = [row.model for row in rows_for_n]
        k_values = [summary.k for summary in rows_for_n[0].k_summaries]
        width = 0.8 / max(len(models), 1)

        fig, ax = plt.subplots(figsize=(8, 4.5))
        for model_idx, row in enumerate(rows_for_n):
            offsets = [k + (model_idx - (len(models) - 1) / 2.0) * width for k in k_values]
            values = [
                summary.mean_density if use_density else summary.mean_count
                for summary in row.k_summaries
            ]
            ax.bar(offsets, values, width=width, label=row.model)

        ax.set_xticks(k_values)
        ax.set_xlabel("interval size k")
        ax.set_ylabel("mean density" if use_density else "mean count")
        ax.set_title(f"Interval abundance comparison at N={n}")
        ax.grid(True, axis="y", alpha=0.25)
        ax.legend(loc="best", fontsize=8)
        fig.tight_layout()

        metric_name = "density" if use_density else "count"
        output_path = output_dir / f"interval_abundance_n{n}_{metric_name}.png"
        fig.savefig(output_path, dpi=140)
        plt.close(fig)
        output_paths.append(output_path)

    return tuple(output_paths)
