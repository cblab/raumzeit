"""Run focused interval layer-profile evaluation across reference and null generators."""

from __future__ import annotations

import argparse
import statistics
import sys
from collections.abc import Sequence
from pathlib import Path

from causal_set_engine.config.loaders import load_layer_profile_evaluation_config
from causal_set_engine.evaluation.layer_profile_study import evaluate_layer_profiles_study
from causal_set_engine.visualization.profiles import (
    write_layer_profile_sample_plots,
    write_layer_profile_summary_trend_plot,
)
from causal_set_engine.visualization.trends import write_layer_profile_metric_trend_plot


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="optional path to JSON/TOML/YAML config file (CLI flags override file values)",
    )
    parser.add_argument(
        "--dimensions",
        type=str,
        default="2,3,4",
        help="comma-separated Minkowski dimensions to evaluate (allowed: 2,3,4)",
    )
    parser.add_argument("--n-values", type=str, default="40,80,120", help="comma-separated size sweep values")
    parser.add_argument("--runs", type=int, default=8, help="number of seeds per model")
    parser.add_argument("--seed-start", type=int, default=100)
    parser.add_argument("--null-p", type=float, default=0.2)
    parser.add_argument("--null-edge-density", type=float, default=0.2)
    parser.add_argument("--min-interval-size", type=int, default=8)
    parser.add_argument("--max-sampled-intervals", type=int, default=64)
    parser.add_argument("--interval-seed-offset", type=int, default=10_000)
    parser.add_argument("--plot", action="store_true", help="write static layer-profile plots")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/plots/evaluate-layers"),
        help="directory for optional plot output files",
    )
    parser.add_argument(
        "--max-profile-plots",
        type=int,
        default=12,
        help="maximum number of sampled interval profiles to plot",
    )

    args = parser.parse_args(argv)
    raw_cli_args = list(argv) if argv is not None else sys.argv[1:]
    config = load_layer_profile_evaluation_config(args, raw_cli_args)

    result = evaluate_layer_profiles_study(
        dimensions=config.dimensions,
        n_values=config.n_values,
        runs=config.runs,
        seed_start=config.seed_start,
        null_p=config.null_p,
        null_edge_density=config.null_edge_density,
        min_interval_size=config.min_interval_size,
        max_sampled_intervals=config.max_sampled_intervals,
        interval_seed_offset=config.interval_seed_offset,
    )

    print("layer-profile evaluation study")
    print(
        " ".join(
            [
                f"dimensions={list(config.dimensions)}",
                f"n_values={list(config.n_values)}",
                f"runs={config.runs}",
                f"seed_start={config.seed_start}",
                f"null_p={config.null_p}",
                f"null_edge_density={config.null_edge_density}",
                f"min_interval_size={config.min_interval_size}",
                f"max_sampled_intervals={config.max_sampled_intervals}",
                f"interval_seed_offset={config.interval_seed_offset}",
            ]
        )
    )

    print("\nper-model summaries")
    print(
        "model                 N   occ_layers(mean±sd) peak_size(mean±sd) "
        "peak_idx(mean±sd) boundary_frac(mean±sd) midpoint_d(mean±sd) mm(mean±sd) sampled/qualifying under"
    )
    for row in result.per_model_n:
        print(
            f"{row.model:<21} {row.n:<3} "
            f"{row.occupied_layers.mean:>6.2f}±{row.occupied_layers.stdev:<5.2f} "
            f"{row.peak_layer_size.mean:>6.2f}±{row.peak_layer_size.stdev:<5.2f} "
            f"{row.peak_layer_index.mean:>6.2f}±{row.peak_layer_index.stdev:<5.2f} "
            f"{row.boundary_fraction.mean:>6.3f}±{row.boundary_fraction.stdev:<5.3f} "
            f"{row.midpoint_dimension_estimate.mean:>6.3f}±{row.midpoint_dimension_estimate.stdev:<5.3f} "
            f"{row.myrheim_meyer.mean:>6.3f}±{row.myrheim_meyer.stdev:<5.3f} "
            f"{row.sampled_interval_count_mean:>6.2f}/{row.qualifying_interval_count_mean:<6.2f} "
            f"{row.under_sampled_runs}"
        )

    print("\nseparation vs null models (effect sizes; larger magnitude is stronger)")
    print("model                 N   null_model         occ_layers boundary_frac peak_idx midpoint_d myrheim")
    for row in result.separation_rows:
        print(
            f"{row.model:<21} {row.n:<3} {row.null_model:<18} "
            f"{row.occupied_layers_effect_size:+.3f}     "
            f"{row.boundary_fraction_effect_size:+.3f}       "
            f"{row.peak_index_effect_size:+.3f}   "
            f"{row.midpoint_effect_size:+.3f}    "
            f"{row.myrheim_meyer_effect_size:+.3f}"
        )

    print("\ncompact conclusions")
    print(
        "q: how do layer-profile summaries behave across reference dimensions? "
        "a: inspect per-model means/stdevs by minkowski-2d/3d/4d; the workflow reports structure changes "
        "without imposing directional assumptions."
    )

    occ_abs = [abs(row.occupied_layers_effect_size) for row in result.separation_rows]
    bnd_abs = [abs(row.boundary_fraction_effect_size) for row in result.separation_rows]
    peak_abs = [abs(row.peak_index_effect_size) for row in result.separation_rows]
    midpoint_abs = [abs(row.midpoint_effect_size) for row in result.separation_rows]
    mm_abs = [abs(row.myrheim_meyer_effect_size) for row in result.separation_rows]
    print(
        "q: does it separate Minkowski references from current null models? "
        f"a: conservative min |effect| over layer metrics={result.conservative_min_effect_layers:.3f}; "
        f"mean |effect| occ/boundary/peak={statistics.fmean(occ_abs):.3f}/"
        f"{statistics.fmean(bnd_abs):.3f}/{statistics.fmean(peak_abs):.3f}."
    )
    print(
        "q: where is it noisy, unstable, or under-sampled? "
        f"a: {len([row for row in result.per_model_n if row.under_sampled_runs > 0])}/"
        f"{len(result.per_model_n)} model-N cells had under-sampled runs; use sampled/qualifying and stdev columns to"
        " identify unstable cells."
    )
    print(
        "q: does it add structure information beyond midpoint scaling / Myrheim-Meyer? "
        f"a: compare conservative min |effect| layer/midpoint/mm = "
        f"{result.conservative_min_effect_layers:.3f}/"
        f"{result.conservative_min_effect_midpoint:.3f}/"
        f"{result.conservative_min_effect_myrheim_meyer:.3f}; "
        f"mean |effect| midpoint/mm = {statistics.fmean(midpoint_abs):.3f}/{statistics.fmean(mm_abs):.3f}."
    )

    if args.plot:
        trend_dir = args.output_dir
        generated = [
            write_layer_profile_metric_trend_plot(result, trend_dir / "layer_occupied_layers_trend.png"),
            write_layer_profile_summary_trend_plot(result, trend_dir / "layer_boundary_fraction_trend.png"),
        ]
        generated.extend(
            write_layer_profile_sample_plots(
                result.sampled_profiles,
                trend_dir / "sampled_profiles",
                max_plots=args.max_profile_plots,
            )
        )
        print("\nplot outputs:")
        for path in generated:
            print(path)


if __name__ == "__main__":
    main()
