"""Run compact batch calibration and conservative discriminator ranking."""

from __future__ import annotations

import argparse
import statistics
import sys
from collections.abc import Callable
from collections.abc import Sequence
from dataclasses import dataclass

from causal_set_engine.core.causal_set import CausalSet
from causal_set_engine.config.loaders import load_batch_calibration_config
from causal_set_engine.evaluation.metrics import (
    DEFAULT_METRICS,
    MetricRow,
    pair_quality_rows,
    run_once,
)
from causal_set_engine.evaluation.sampling import batch_rows, edge_count_from_density
from causal_set_engine.evaluation.scoring import (
    PairQuality,
    aggregate_diagnostic_quality,
    build_combined_score,
)
from causal_set_engine.generators.minkowski_2d import generate_minkowski_2d
from causal_set_engine.generators.minkowski_3d import generate_minkowski_3d
from causal_set_engine.generators.minkowski_4d import generate_minkowski_4d
from causal_set_engine.generators.null_models import generate_fixed_edge_count_poset
from causal_set_engine.generators.random_poset import generate_random_poset


METRICS: tuple[str, ...] = DEFAULT_METRICS


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


def _parse_n_values(n_text: str | None, fallback_n: int) -> list[int]:
    if not n_text:
        return [fallback_n]
    raw_values = [token.strip() for token in n_text.split(",") if token.strip()]
    if not raw_values:
        return [fallback_n]
    values = sorted({int(token) for token in raw_values})
    if any(value <= 1 for value in values):
        raise ValueError("all N values must be integers > 1")
    return values


def _run_once(cset: CausalSet, interval_samples: int, seed: int) -> MetricRow:
    return run_once(cset, interval_samples, seed)


def _edge_count_from_density(n: int, density: float) -> int:
    return edge_count_from_density(n, density)


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
    return batch_rows(run_fn, n, runs, seed_start, interval_samples)


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


def _pair_quality_rows(
    n_values: list[int],
    mk_rows_by_n: dict[int, list[MetricRow]],
    null_rows_by_n: dict[int, list[MetricRow]],
    null_model_name: str,
) -> list[PairQuality]:
    return pair_quality_rows(
        n_values=n_values,
        mk_rows_by_n=mk_rows_by_n,
        null_rows_by_n=null_rows_by_n,
        null_model_name=null_model_name,
        metrics=METRICS,
    )


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="optional path to JSON/TOML/YAML config file (CLI flags override file values)",
    )
    parser.add_argument("--dimension", type=int, default=2, choices=[2, 3, 4])
    parser.add_argument("--n", type=int, default=80, help="number of elements per run")
    parser.add_argument(
        "--n-values",
        type=str,
        default=None,
        help="comma-separated size sweep (e.g., 60,80,100); overrides --n when provided",
    )
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
    args = parser.parse_args(argv)
    raw_cli_args = list(argv) if argv is not None else sys.argv[1:]
    config = load_batch_calibration_config(args, raw_cli_args)

    n_values = _parse_n_values(config.n_values_text, config.n)
    minkowski_gen = _minkowski_generator(config.dimension)

    mk_by_n: dict[int, list[MetricRow]] = {}
    random_by_n: dict[int, list[MetricRow]] = {}
    fixed_by_n: dict[int, list[MetricRow]] = {}

    print("batch calibration run")
    print(
        " ".join(
            [
                f"dimension={config.dimension}",
                f"runs={config.runs}",
                f"n_values={n_values}",
                f"seed_start={config.seed_start}",
                f"null_p={config.null_p}",
                f"null_edge_density={config.null_edge_density}",
            ]
        )
    )
    print(
        "model            dim_est(mean±sd)[min,max]     rel_density(mean±sd)   "
        "chain_len(mean±sd)[min,max]   interval_mean(mean±sd)"
    )

    for n in n_values:
        mk_by_n[n] = _batch_rows(
            minkowski_gen, n, config.runs, config.seed_start, config.interval_samples
        )
        random_by_n[n] = _batch_rows(
            lambda n_val, seed: generate_random_poset(
                n=n_val,
                relation_probability=config.null_p,
                seed=seed,
            ),
            n,
            config.runs,
            config.seed_start,
            config.interval_samples,
        )
        fixed_edge_count = _edge_count_from_density(n, config.null_edge_density)
        fixed_by_n[n] = _batch_rows(
            lambda n_val, seed: generate_fixed_edge_count_poset(
                n=n_val,
                edge_count=fixed_edge_count,
                seed=seed,
            ),
            n,
            config.runs,
            config.seed_start,
            config.interval_samples,
        )

        print(f"\nN={n}")
        _print_model_row(ModelSummary(model_name=f"minkowski{config.dimension}d", rows=mk_by_n[n]))
        _print_model_row(ModelSummary(model_name="random-poset", rows=random_by_n[n]))
        _print_model_row(ModelSummary(model_name="fixed-edge-poset", rows=fixed_by_n[n]))

    pair_quality = _pair_quality_rows(n_values, mk_by_n, random_by_n, "random-poset")
    pair_quality.extend(_pair_quality_rows(n_values, mk_by_n, fixed_by_n, "fixed-edge-poset"))
    ranked = aggregate_diagnostic_quality(pair_quality)

    print("\nconservative discriminator ranking")
    print(
        "metric                band                    score   |effect|  interval_sep sign_cons trend "
        "(weights: effect=0.35, overlap=0.25, sign=0.20, trend=0.20)"
    )
    for row in ranked:
        print(
            f"{row.metric:<21}{row.band:<24}{row.usefulness_score:.3f}   "
            f"{row.effect_size_abs:.3f}     {row.interval_separation:.3f}       "
            f"{row.sign_consistency:.3f}    {row.trend_consistency:.3f}"
        )

    combined = build_combined_score(METRICS, mk_by_n, random_by_n, fixed_by_n)
    single_best_min_effect = max(
        min(
            abs(item.effect_size)
            for item in pair_quality
            if item.metric == metric_name
        )
        for metric_name in METRICS
    )
    combined_min_effect = min(abs(combined.mk_vs_random_effect), abs(combined.mk_vs_fixed_effect))

    print("\ncombined manifold-likeness score (linear, diagnostics-only)")
    print(
        f"metrics={combined.metric_names} orientation={combined.orientation} "
        f"means: mk={combined.minkowski_mean:+.3f}, random={combined.random_mean:+.3f}, "
        f"fixed={combined.fixed_edge_mean:+.3f}"
    )
    print(
        f"combined_effects: mk-vs-random={combined.mk_vs_random_effect:+.3f}, "
        f"mk-vs-fixed={combined.mk_vs_fixed_effect:+.3f}"
    )
    print(
        f"robustness check: combined_worst_case_effect={combined_min_effect:.3f}, "
        f"best_single_worst_case_effect={single_best_min_effect:.3f}"
    )
    if combined_min_effect > single_best_min_effect:
        print("assessment: combined score improves conservative worst-case separation.")
    else:
        print("assessment: combined score does not beat best single metric in worst-case separation.")

    print(
        "\nlimitations: rankings are heuristic and calibration-only; thresholds are explicit and fixed "
        "for conservative diagnostics, not theory claims or fitted decision boundaries."
    )


if __name__ == "__main__":
    main()
