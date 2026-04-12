"""Run focused midpoint-scaling evaluation across reference and null generators."""

from __future__ import annotations

import argparse
import statistics
import sys
from collections.abc import Sequence
from pathlib import Path

from causal_set_engine.config.loaders import load_midpoint_evaluation_config
from causal_set_engine.evaluation.midpoint_scaling_study import evaluate_midpoint_scaling_study
from causal_set_engine.visualization.trends import write_midpoint_dimension_trend_plot


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
    parser.add_argument(
        "--n-values",
        type=str,
        default="40,80,120",
        help="comma-separated size sweep values",
    )
    parser.add_argument("--runs", type=int, default=8, help="number of seeds per model")
    parser.add_argument("--seed-start", type=int, default=100)
    parser.add_argument("--null-p", type=float, default=0.2)
    parser.add_argument("--null-edge-density", type=float, default=0.2)
    parser.add_argument("--min-interval-size", type=int, default=8)
    parser.add_argument("--max-sampled-intervals", type=int, default=64)
    parser.add_argument("--interval-seed-offset", type=int, default=10_000)
    parser.add_argument("--plot", action="store_true", help="write a static trend plot")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/plots/evaluate-midpoint"),
        help="directory for optional plot output files",
    )

    args = parser.parse_args(argv)
    raw_cli_args = list(argv) if argv is not None else sys.argv[1:]
    config = load_midpoint_evaluation_config(args, raw_cli_args)

    result = evaluate_midpoint_scaling_study(
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

    print("midpoint scaling evaluation study")
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
        "model                 N   midpoint_S(mean±sd) midpoint_d(mean±sd) "
        "mm(mean±sd) chain(mean±sd) sampled/qualifying(mean) under_sampled"
    )
    for row in result.per_model_n:
        print(
            f"{row.model:<21} {row.n:<3} "
            f"{row.midpoint_scaling.mean:>7.3f}±{row.midpoint_scaling.stdev:<6.3f} "
            f"{row.midpoint_dimension_estimate.mean:>7.3f}±{row.midpoint_dimension_estimate.stdev:<6.3f} "
            f"{row.myrheim_meyer.mean:>6.3f}±{row.myrheim_meyer.stdev:<6.3f} "
            f"{row.chain_height_proxy.mean:>6.3f}±{row.chain_height_proxy.stdev:<6.3f} "
            f"{row.sampled_interval_count_mean:>6.2f}/{row.qualifying_interval_count_mean:<8.2f} "
            f"{row.under_sampled_runs}"
        )

    print("\nseparation vs null models (effect sizes; larger magnitude is stronger)")
    print("model                 N   null_model         midpoint_d  myrheim   chain_proxy")
    for row in result.separation_rows:
        print(
            f"{row.model:<21} {row.n:<3} {row.null_model:<18} "
            f"{row.midpoint_effect_size:+.3f}      {row.myrheim_meyer_effect_size:+.3f}    "
            f"{row.chain_proxy_effect_size:+.3f}"
        )

    monotone_count = sum(1 for _, flag in result.monotone_by_n if flag)
    print("\ncompact conclusions")
    print(
        "q: does midpoint scaling distinguish 2D/3D/4D references? "
        f"a: strict monotone ordering of midpoint-derived dimension held for "
        f"{monotone_count}/{len(result.monotone_by_n)} N values."
    )
    midpoint_abs = [abs(row.midpoint_effect_size) for row in result.separation_rows]
    mm_abs = [abs(row.myrheim_meyer_effect_size) for row in result.separation_rows]
    chain_abs = [abs(row.chain_proxy_effect_size) for row in result.separation_rows]
    print(
        "q: does it separate Minkowski references from current null models? "
        f"a: conservative min |effect| midpoint={result.conservative_min_effect_midpoint:.3f}, "
        f"mean |effect| midpoint={statistics.fmean(midpoint_abs):.3f}."
    )
    print(
        "q: how does it compare to Myrheim-Meyer and chain-height proxy? "
        f"a: min |effect| midpoint/mm/chain = "
        f"{result.conservative_min_effect_midpoint:.3f}/"
        f"{result.conservative_min_effect_myrheim_meyer:.3f}/"
        f"{result.conservative_min_effect_chain_proxy:.3f}; "
        f"mean |effect| midpoint/mm/chain = "
        f"{statistics.fmean(midpoint_abs):.3f}/"
        f"{statistics.fmean(mm_abs):.3f}/"
        f"{statistics.fmean(chain_abs):.3f}."
    )

    under_sampled = [row for row in result.per_model_n if row.under_sampled_runs > 0]
    print(
        "q: where is it unstable or under-sampled? "
        f"a: {len(under_sampled)}/{len(result.per_model_n)} model-N cells had one or more "
        "runs with fewer sampled intervals than requested; inspect sampled/qualifying and "
        "under_sampled columns above."
    )

    if args.plot:
        plot_path = write_midpoint_dimension_trend_plot(
            result,
            args.output_dir / "midpoint_dimension_trend.png",
        )
        print(f"\nplot output: {plot_path}")


if __name__ == "__main__":
    main()
