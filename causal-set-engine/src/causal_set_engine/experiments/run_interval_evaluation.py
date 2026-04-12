"""Run focused global interval-abundance evaluation across reference and null generators."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from causal_set_engine.config.loaders import load_interval_evaluation_config
from causal_set_engine.evaluation.interval_study import evaluate_global_interval_statistics


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
    parser.add_argument("--k-max", type=int, default=5)

    args = parser.parse_args(argv)
    raw_cli_args = list(argv) if argv is not None else sys.argv[1:]
    config = load_interval_evaluation_config(args, raw_cli_args)

    result = evaluate_global_interval_statistics(
        dimensions=config.dimensions,
        n_values=config.n_values,
        runs=config.runs,
        seed_start=config.seed_start,
        null_p=config.null_p,
        null_edge_density=config.null_edge_density,
        k_max=config.k_max,
    )

    print("global interval statistics evaluation")
    print(
        " ".join(
            [
                f"dimensions={list(config.dimensions)}",
                f"n_values={list(config.n_values)}",
                f"runs={config.runs}",
                f"seed_start={config.seed_start}",
                f"k_max={config.k_max}",
                f"null_p={config.null_p}",
                f"null_edge_density={config.null_edge_density}",
            ]
        )
    )

    print("\ninterval abundance summary by model")
    print("model                 N    comparable_pairs(mean)   k   count(mean±sd)     density(mean)")
    for row in result.rows:
        for summary in row.k_summaries:
            print(
                f"{row.model:<21} {row.n:<4} {row.mean_comparable_pairs:>8.2f}               "
                f"{summary.k:<2}  {summary.mean_count:>8.2f}±{summary.stdev_count:<8.2f} "
                f"{summary.mean_density:>8.4f}"
            )

    print("\nlink-focused view (N0 intervals where k=0)")
    for row in result.rows:
        link_summary = row.k_summaries[0]
        print(
            f"{row.model:<21} N={row.n:<4} links(mean count)={link_summary.mean_count:.2f} "
            f"links(mean density)={link_summary.mean_density:.4f}"
        )


if __name__ == "__main__":
    main()
