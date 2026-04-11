"""Run a compact phase-1 batch calibration comparison."""

from __future__ import annotations

import argparse
import statistics

from causal_set_engine.diagnostics.basic import (
    estimate_dimension_chain_height,
    longest_chain_length,
    relation_density,
    sampled_interval_statistics,
)
from causal_set_engine.generators.minkowski_2d import generate_minkowski_2d
from causal_set_engine.generators.random_poset import generate_random_poset


def _run_minkowski_once(n: int, seed: int, interval_samples: int) -> dict[str, float]:
    cset, _ = generate_minkowski_2d(n=n, seed=seed)
    interval_stats = sampled_interval_statistics(cset, pairs=interval_samples, seed=seed)
    return {
        "relation_density": relation_density(cset),
        "longest_chain_length": float(longest_chain_length(cset)),
        "dimension_estimate": estimate_dimension_chain_height(cset),
        "interval_mean": float(interval_stats["mean"] or 0.0),
    }


def _run_random_poset_once(
    n: int,
    seed: int,
    relation_probability: float,
    interval_samples: int,
) -> dict[str, float]:
    cset = generate_random_poset(n=n, relation_probability=relation_probability, seed=seed)
    interval_stats = sampled_interval_statistics(cset, pairs=interval_samples, seed=seed)
    return {
        "relation_density": relation_density(cset),
        "longest_chain_length": float(longest_chain_length(cset)),
        "dimension_estimate": estimate_dimension_chain_height(cset),
        "interval_mean": float(interval_stats["mean"] or 0.0),
    }


def _summarize(rows: list[dict[str, float]]) -> dict[str, float]:
    keys = rows[0].keys()
    summary: dict[str, float] = {}
    for key in keys:
        values = [row[key] for row in rows]
        summary[f"{key}_mean"] = statistics.fmean(values)
        summary[f"{key}_stdev"] = statistics.stdev(values) if len(values) > 1 else 0.0
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=80, help="number of elements per run")
    parser.add_argument("--runs", type=int, default=8, help="number of seeds per model")
    parser.add_argument(
        "--seed-start",
        type=int,
        default=100,
        help="first seed; subsequent seeds increment by 1",
    )
    parser.add_argument(
        "--null-p",
        type=float,
        default=0.2,
        help="edge probability for random-poset null model",
    )
    parser.add_argument(
        "--interval-samples",
        type=int,
        default=50,
        help="number of related pairs sampled for interval statistics",
    )
    args = parser.parse_args()

    minkowski_rows = []
    null_rows = []

    for seed in range(args.seed_start, args.seed_start + args.runs):
        minkowski_rows.append(_run_minkowski_once(args.n, seed, args.interval_samples))
        null_rows.append(
            _run_random_poset_once(args.n, seed, args.null_p, args.interval_samples)
        )

    minkowski_summary = _summarize(minkowski_rows)
    null_summary = _summarize(null_rows)

    print("phase-1 batch comparison")
    print(f"runs={args.runs} n={args.n} seed_start={args.seed_start} null_p={args.null_p}")
    print("model          dim_est(mean±sd)   rel_density(mean±sd)   chain_len(mean±sd)")
    print(
        "minkowski2d    "
        f"{minkowski_summary['dimension_estimate_mean']:.3f}±{minkowski_summary['dimension_estimate_stdev']:.3f}   "
        f"{minkowski_summary['relation_density_mean']:.3f}±{minkowski_summary['relation_density_stdev']:.3f}   "
        f"{minkowski_summary['longest_chain_length_mean']:.2f}±{minkowski_summary['longest_chain_length_stdev']:.2f}"
    )
    print(
        "random-poset   "
        f"{null_summary['dimension_estimate_mean']:.3f}±{null_summary['dimension_estimate_stdev']:.3f}   "
        f"{null_summary['relation_density_mean']:.3f}±{null_summary['relation_density_stdev']:.3f}   "
        f"{null_summary['longest_chain_length_mean']:.2f}±{null_summary['longest_chain_length_stdev']:.2f}"
    )


if __name__ == "__main__":
    main()
