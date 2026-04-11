"""Run focused Myrheim-Meyer evaluation across reference and null generators."""

from __future__ import annotations

import argparse
import statistics
import sys
from collections.abc import Sequence

from causal_set_engine.config.loaders import load_myrheim_meyer_evaluation_config
from causal_set_engine.evaluation.myrheim_meyer_study import evaluate_myrheim_meyer_study


def _trend_label(values: tuple[float, ...]) -> str:
    if len(values) < 2:
        return "single-size"
    nondecreasing = all(values[idx] <= values[idx + 1] for idx in range(len(values) - 1))
    nonincreasing = all(values[idx] >= values[idx + 1] for idx in range(len(values) - 1))
    if nondecreasing and not nonincreasing:
        return "nondecreasing"
    if nonincreasing and not nondecreasing:
        return "nonincreasing"
    if nonincreasing and nondecreasing:
        return "flat"
    return "mixed"


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
    parser.add_argument("--interval-samples", type=int, default=50)
    parser.add_argument("--null-p", type=float, default=0.2)
    parser.add_argument("--null-edge-density", type=float, default=0.2)
    args = parser.parse_args(argv)
    raw_cli_args = list(argv) if argv is not None else sys.argv[1:]
    config = load_myrheim_meyer_evaluation_config(args, raw_cli_args)

    result = evaluate_myrheim_meyer_study(
        dimensions=config.dimensions,
        n_values=config.n_values,
        runs=config.runs,
        seed_start=config.seed_start,
        interval_samples=config.interval_samples,
        null_p=config.null_p,
        null_edge_density=config.null_edge_density,
    )

    print("myrheim-meyer evaluation study")
    print(
        " ".join(
            [
                f"dimensions={list(config.dimensions)}",
                f"n_values={list(config.n_values)}",
                f"runs={config.runs}",
                f"seed_start={config.seed_start}",
                f"null_p={config.null_p}",
                f"null_edge_density={config.null_edge_density}",
            ]
        )
    )

    print("\nper-dimension summaries")
    print("dimension N   mm(mean±sd)    chain_proxy(mean±sd)")
    for row in result.per_dimension_n:
        print(
            f"{row.dimension:<9} {row.n:<3} "
            f"{row.myrheim_meyer.mean:>6.3f}±{row.myrheim_meyer.stdev:<6.3f} "
            f"{row.chain_height_proxy.mean:>8.3f}±{row.chain_height_proxy.stdev:<6.3f}"
        )

    print("\nmyrheim-meyer N-trend by dimension")
    for trend in result.dimension_trends:
        trend_text = ", ".join(
            f"N={n}:{value:.3f}" for n, value in zip(trend.n_values, trend.myrheim_meyer_means)
        )
        print(
            f"minkowski{trend.dimension}d: {trend_text} ({_trend_label(trend.myrheim_meyer_means)})"
        )

    print("\nseparation vs null models (effect sizes; larger magnitude is stronger)")
    print("dimension N   null_model         mm_effect  chain_proxy_effect")
    for row in result.separation_rows:
        print(
            f"{row.dimension:<9} {row.n:<3} {row.null_model:<18} "
            f"{row.myrheim_meyer_effect_size:+.3f}     {row.chain_proxy_effect_size:+.3f}"
        )

    monotone_count = sum(1 for _, flag in result.monotone_by_n if flag)
    print("\ncompact conclusions")
    print(
        "q: does Myrheim-Meyer distinguish 2D/3D/4D references? "
        f"a: strict monotone ordering held for {monotone_count}/{len(result.monotone_by_n)} N values."
    )

    mm_abs = [abs(row.myrheim_meyer_effect_size) for row in result.separation_rows]
    chain_abs = [abs(row.chain_proxy_effect_size) for row in result.separation_rows]
    print(
        "q: does it separate Minkowski references from null models? "
        f"a: conservative min |effect|={result.conservative_min_effect_myrheim_meyer:.3f}, "
        f"mean |effect|={statistics.fmean(mm_abs):.3f}."
    )
    print(
        "q: does it add different/better information than chain-height proxy? "
        f"a: conservative min |effect| mm={result.conservative_min_effect_myrheim_meyer:.3f} "
        f"vs chain={result.conservative_min_effect_chain_proxy:.3f}; "
        f"mean |effect| mm={statistics.fmean(mm_abs):.3f} vs chain={statistics.fmean(chain_abs):.3f}."
    )

    noisy_rows = [
        row for row in result.per_dimension_n if row.myrheim_meyer.stdev > row.chain_height_proxy.stdev
    ]
    print(
        "q: where is it unstable/noisy? "
        f"a: mm stdev exceeded chain-proxy stdev in {len(noisy_rows)}/{len(result.per_dimension_n)} "
        "dimension-N cells; inspect per-dimension summaries above."
    )


if __name__ == "__main__":
    main()
