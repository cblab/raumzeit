"""Run phase-2c age-biased-forward controlled mechanism scan."""

from __future__ import annotations

import argparse

from causal_set_engine.experiments.phase2c_scan import evaluate_age_biased_phase2c_scan
from causal_set_engine.experiments.run_phase2a_probe import _parse_n_values


def _parse_grid(text: str) -> tuple[float, ...]:
    values = tuple(float(token.strip()) for token in text.split(",") if token.strip())
    if not values:
        raise ValueError("grid cannot be empty")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
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

    result = evaluate_age_biased_phase2c_scan(
        n_values=_parse_n_values(args.n_values),
        runs=args.runs,
        seed_start=args.seed_start,
        interval_samples=args.interval_samples,
        null_p=args.null_p,
        null_edge_density=args.null_edge_density,
        link_density_grid=_parse_grid(args.link_density_grid),
        bias_strength_grid=_parse_grid(args.bias_strength_grid),
        age_bias_mode=args.age_bias_mode,
    )

    print("phase-2 gate:", "GO" if result.gate_decision.go else "NO-GO")
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
