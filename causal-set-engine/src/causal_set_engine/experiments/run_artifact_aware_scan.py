"""Run artifact-aware scan for age-biased-forward controlled settings."""

from __future__ import annotations

import argparse
import sys

from causal_set_engine.config.loaders import load_artifact_aware_scan_config
from causal_set_engine.experiments.artifact_aware_scan import evaluate_age_biased_scan


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
    parser.add_argument("--link-density-grid", type=str, default="0.16,0.22,0.28")
    parser.add_argument("--bias-strength-grid", type=str, default="0.0,0.5,1.0")
    parser.add_argument("--age-bias-mode", choices=("older", "newer"), default="older")
    args = parser.parse_args()
    config = load_artifact_aware_scan_config(args, sys.argv[1:])

    result = evaluate_age_biased_scan(
        n_values=_parse_n_values(config.n_values),
        runs=config.runs,
        seed_start=config.seed_start,
        interval_samples=config.interval_samples,
        null_p=config.null_p,
        null_edge_density=config.null_edge_density,
        link_density_grid=config.link_density_grid,
        bias_strength_grid=config.bias_strength_grid,
        age_bias_mode=config.age_bias_mode,
    )

    print("policy gate:", "GO" if result.gate_decision.go else "NO-GO")
    print("primary diagnostics:", result.gate_decision.primary_metrics)
    print("gate failures:", result.gate_decision.failures)
    print(
        "link-density | bias-strength | gate | primary-profile | vs-minkowski | vs-nulls | "
        "birth-order-proxy | layering-proxy | score(mean±sd) | interpretation"
    )
    for row in result.rows:
        print(
            f"{row.setting.link_density:.3f} | {row.setting.bias_strength:.2f} | {row.gate_decision} | "
            f"{row.primary_diagnostic_profile} | {row.relative_to_minkowski} | {row.relative_to_nulls} | "
            f"{row.birth_order_dominance_proxy:.3f} | {row.age_layering_stratification_proxy:.3f} | "
            f"{row.mean_score:+.3f}±{row.score_stddev:.3f} | {row.interpretation_label}"
        )

    print(
        "note: this scan is conservative and artifact-aware; it identifies least-misleading "
        "regions rather than optimized winners."
    )


if __name__ == "__main__":
    main()
