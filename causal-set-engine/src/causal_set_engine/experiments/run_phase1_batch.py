"""Run compact phase-1.5 calibration robustness comparisons."""

from __future__ import annotations

import argparse
import statistics
from collections.abc import Callable
from dataclasses import dataclass

from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.diagnostics.basic import (
    estimate_dimension_chain_height,
    longest_chain_length,
    relation_density,
    sampled_interval_statistics,
)
from causal_set_engine.generators.minkowski_2d import generate_minkowski_2d
from causal_set_engine.generators.minkowski_3d import generate_minkowski_3d
from causal_set_engine.generators.minkowski_4d import generate_minkowski_4d
from causal_set_engine.generators.null_models import generate_fixed_edge_count_poset
from causal_set_engine.generators.random_poset import generate_random_poset


MetricRow = dict[str, float]


@dataclass(frozen=True)
class ModelSummary:
    """Summary statistics for one model over many runs."""

    model_name: str
    rows: list[MetricRow]

    def describe(self) -> dict[str, float]:
        keys = self.rows[0].keys()
        summary: dict[str, float] = {}
        for key in keys:
            values = [row[key] for row in self.rows]
            summary[f"{key}_mean"] = statistics.fmean(values)
            summary[f"{key}_stdev"] = statistics.stdev(values) if len(values) > 1 else 0.0
            summary[f"{key}_min"] = min(values)
            summary[f"{key}_max"] = max(values)
        return summary


def _run_once(cset: CausalSet, interval_samples: int, seed: int) -> MetricRow:
    interval_stats = sampled_interval_statistics(cset, pairs=interval_samples, seed=seed)
    return {
        "relation_density": relation_density(cset),
        "longest_chain_length": float(longest_chain_length(cset)),
        "dimension_estimate": estimate_dimension_chain_height(cset),
        "interval_mean": float(interval_stats["mean"] or 0.0),
        "interval_median": float(interval_stats["median"] or 0.0),
    }


def _edge_count_from_density(n: int, density: float) -> int:
    max_forward_edges = n * (n - 1) // 2
    return int(round(density * max_forward_edges))


def _minkowski_generator(dimension: int) -> Callable[[int, int], CausalSet]:
    if dimension == 2:
        return lambda n, seed: generate_minkowski_2d(n=n, seed=seed)[0]
    if dimension == 3:
        return lambda n, seed: generate_minkowski_3d(n=n, seed=seed)[0]
    if dimension == 4:
        return lambda n, seed: generate_minkowski_4d(n=n, seed=seed)[0]
    raise ValueError("dimension must be one of {2, 3, 4}")


def _batch_rows(
    run_fn: Callable[[int, int], CausalSet],
    n: int,
    runs: int,
    seed_start: int,
    interval_samples: int,
) -> list[MetricRow]:
    rows: list[MetricRow] = []
    for seed in range(seed_start, seed_start + runs):
        rows.append(_run_once(run_fn(n, seed), interval_samples, seed))
    return rows


def _separation_fraction(target: str, a_rows: list[MetricRow], b_rows: list[MetricRow]) -> float:
    a_values = [row[target] for row in a_rows]
    b_values = [row[target] for row in b_rows]
    separated = 0
    total = min(len(a_values), len(b_values))
    for i in range(total):
        if a_values[i] != b_values[i]:
            separated += 1
    return separated / total if total else 0.0


def _separable_text(
    minkowski: ModelSummary,
    null_model: ModelSummary,
) -> str:
    mk = minkowski.describe()
    nm = null_model.describe()

    dim_clear = (
        mk["dimension_estimate_min"] > nm["dimension_estimate_max"]
        or nm["dimension_estimate_min"] > mk["dimension_estimate_max"]
    )
    chain_clear = (
        mk["longest_chain_length_min"] > nm["longest_chain_length_max"]
        or nm["longest_chain_length_min"] > mk["longest_chain_length_max"]
    )
    interval_clear = (
        mk["interval_mean_min"] > nm["interval_mean_max"]
        or nm["interval_mean_min"] > mk["interval_mean_max"]
    )

    dim_sep = _separation_fraction("dimension_estimate", minkowski.rows, null_model.rows)
    chain_sep = _separation_fraction("longest_chain_length", minkowski.rows, null_model.rows)
    interval_sep = _separation_fraction("interval_mean", minkowski.rows, null_model.rows)

    dim_shift = mk["dimension_estimate_mean"] - nm["dimension_estimate_mean"]
    chain_shift = mk["longest_chain_length_mean"] - nm["longest_chain_length_mean"]
    interval_shift = mk["interval_mean_mean"] - nm["interval_mean_mean"]

    return (
        f"vs {null_model.model_name}: "
        f"dim({'clear' if dim_clear else 'overlap'}, Δmean={dim_shift:+.2f}, sep={dim_sep:.2f}) "
        f"chain({'clear' if chain_clear else 'overlap'}, Δmean={chain_shift:+.2f}, sep={chain_sep:.2f}) "
        f"interval({'clear' if interval_clear else 'overlap'}, Δmean={interval_shift:+.2f}, sep={interval_sep:.2f})"
    )


def _print_model_row(summary: ModelSummary) -> None:
    stats = summary.describe()
    print(
        f"{summary.model_name:<17}"
        f"{stats['dimension_estimate_mean']:.3f}±{stats['dimension_estimate_stdev']:.3f} "
        f"[{stats['dimension_estimate_min']:.3f},{stats['dimension_estimate_max']:.3f}]   "
        f"{stats['relation_density_mean']:.3f}±{stats['relation_density_stdev']:.3f}   "
        f"{stats['longest_chain_length_mean']:.2f}±{stats['longest_chain_length_stdev']:.2f} "
        f"[{stats['longest_chain_length_min']:.0f},{stats['longest_chain_length_max']:.0f}]   "
        f"{stats['interval_mean_mean']:.2f}±{stats['interval_mean_stdev']:.2f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dimension", type=int, default=2, choices=[2, 3, 4])
    parser.add_argument("--n", type=int, default=80, help="number of elements per run")
    parser.add_argument("--runs", type=int, default=8, help="number of seeds per model")
    parser.add_argument("--seed-start", type=int, default=100)
    parser.add_argument(
        "--null-p",
        type=float,
        default=0.2,
        help="edge probability for random-poset null model",
    )
    parser.add_argument(
        "--null-edge-density",
        type=float,
        default=0.2,
        help="direct-edge density for fixed-edge-count null baseline",
    )
    parser.add_argument(
        "--interval-samples",
        type=int,
        default=50,
        help="number of related pairs sampled for interval statistics",
    )
    args = parser.parse_args()

    minkowski_gen = _minkowski_generator(args.dimension)

    minkowski_summary = ModelSummary(
        model_name=f"minkowski{args.dimension}d",
        rows=_batch_rows(minkowski_gen, args.n, args.runs, args.seed_start, args.interval_samples),
    )
    random_summary = ModelSummary(
        model_name="random-poset",
        rows=_batch_rows(
            lambda n, seed: generate_random_poset(n=n, relation_probability=args.null_p, seed=seed),
            args.n,
            args.runs,
            args.seed_start,
            args.interval_samples,
        ),
    )
    fixed_edge_count = _edge_count_from_density(args.n, args.null_edge_density)
    fixed_edge_summary = ModelSummary(
        model_name="fixed-edge-poset",
        rows=_batch_rows(
            lambda n, seed: generate_fixed_edge_count_poset(
                n=n,
                edge_count=fixed_edge_count,
                seed=seed,
            ),
            args.n,
            args.runs,
            args.seed_start,
            args.interval_samples,
        ),
    )

    print("phase-1.5 robustness batch")
    print(
        " ".join(
            [
                f"dimension={args.dimension}",
                f"runs={args.runs}",
                f"n={args.n}",
                f"seed_start={args.seed_start}",
                f"null_p={args.null_p}",
                f"null_edge_density={args.null_edge_density}",
            ]
        )
    )
    print(
        "model            dim_est(mean±sd)[min,max]     rel_density(mean±sd)   "
        "chain_len(mean±sd)[min,max]   interval_mean(mean±sd)"
    )
    _print_model_row(minkowski_summary)
    _print_model_row(random_summary)
    _print_model_row(fixed_edge_summary)

    print("\nseparability summary")
    print(_separable_text(minkowski_summary, random_summary))
    print(_separable_text(minkowski_summary, fixed_edge_summary))
    print(
        "note: separability uses only empirical run-level overlap/dominance in this batch; "
        "it is not a proof of manifold-likeness."
    )


if __name__ == "__main__":
    main()
