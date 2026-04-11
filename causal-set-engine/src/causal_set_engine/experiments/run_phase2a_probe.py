"""Run strict phase-2 gate check and primitive dynamics comparison probe."""

from __future__ import annotations

import argparse
import sys

from causal_set_engine.config.loaders import load_phase2a_probe_config
from causal_set_engine.experiments.phase2a_probe import (
    evaluate_minimal_growth_probe,
    evaluate_phase2_family_comparison,
)


def _parse_n_values(n_values: tuple[int, ...]) -> list[int]:
    values = sorted(set(n_values))
    if any(value <= 1 for value in values):
        raise ValueError("all N values must be integers > 1")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="optional path to JSON/TOML/YAML config file (CLI flags override file values)",
    )
    parser.add_argument("--n-values", type=str, default="60,80")
    parser.add_argument("--runs", type=int, default=8)
    parser.add_argument("--seed-start", type=int, default=100)
    parser.add_argument("--interval-samples", type=int, default=50)
    parser.add_argument("--null-p", type=float, default=0.2)
    parser.add_argument("--null-edge-density", type=float, default=0.2)
    parser.add_argument("--growth-link-probability", type=float, default=0.2)
    parser.add_argument("--sparse-base-link-probability", type=float, default=0.25)
    parser.add_argument("--age-bias-mode", choices=("older", "newer"), default="older")
    parser.add_argument("--lookback-window", type=int, default=8)
    parser.add_argument(
        "--dynamics-family",
        type=str,
        default="bernoulli-forward",
        help="bernoulli-forward|sparse-forward|age-biased-forward|window-forward|all",
    )
    args = parser.parse_args()
    config = load_phase2a_probe_config(args, sys.argv[1:])

    if config.dynamics_family == "all":
        result = evaluate_phase2_family_comparison(
            n_values=_parse_n_values(config.n_values),
            runs=config.runs,
            seed_start=config.seed_start,
            interval_samples=config.interval_samples,
            null_p=config.null_p,
            null_edge_density=config.null_edge_density,
            growth_link_probability=config.growth_link_probability,
            sparse_base_link_probability=config.sparse_base_link_probability,
            age_bias_mode=config.age_bias_mode,
            lookback_window=config.lookback_window,
        )

        print("phase-2 gate:", "GO" if result.gate_decision.go else "NO-GO")
        print("primary diagnostics:", result.gate_decision.primary_metrics)
        print("gate failures:", result.gate_decision.failures)
        print("comparison matrix:")
        print(
            "family | gate | primary-performance | vs-minkowski | vs-nulls | N-trend | mean-score | artifact-warning"
        )
        for row in result.family_rows:
            print(
                f"{row.family_name} | {row.gate_decision} | {row.primary_diagnostic_performance} | "
                f"{row.relative_to_minkowski} | {row.relative_to_nulls} | {row.n_trend_behavior} | "
                f"{row.mean_score:+.3f} | {row.artifact_risk}"
            )
        return

    result = evaluate_minimal_growth_probe(
        n_values=_parse_n_values(config.n_values),
        runs=config.runs,
        seed_start=config.seed_start,
        interval_samples=config.interval_samples,
        null_p=config.null_p,
        null_edge_density=config.null_edge_density,
        growth_link_probability=config.growth_link_probability,
    )

    print("phase-2a gate:", "GO" if result.gate_decision.go else "NO-GO")
    print("primary diagnostics:", result.gate_decision.primary_metrics)
    print("gate failures:", result.gate_decision.failures)
    print("diagnostic bands:", result.diagnostic_bands)
    print(
        "reference means:",
        f"minkowski={result.minkowski_mean_score:+.3f}",
        f"random={result.random_mean_score:+.3f}",
        f"fixed={result.fixed_edge_mean_score:+.3f}",
        f"minimal-growth={result.minimal_growth_mean_score:+.3f}",
    )
    print(
        "relative position:",
        result.relative_to_minkowski,
        "/",
        result.relative_to_nulls,
    )
    print(
        "robustness snapshot:",
        f"combined_min_effect={result.combined_min_effect:.3f}",
        f"best_single_worst_case_effect={result.best_single_worst_case_effect:.3f}",
    )
    print(
        "note: interpretation is conservative and calibration-driven; "
        "this probe does not establish physical dynamics claims."
    )


if __name__ == "__main__":
    main()
