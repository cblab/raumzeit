"""Run strict phase-2a gate check and minimal dynamics sandbox probe."""

from __future__ import annotations

import argparse

from causal_set_engine.experiments.phase2a_probe import evaluate_minimal_growth_probe


def _parse_n_values(n_text: str) -> list[int]:
    values = sorted({int(token.strip()) for token in n_text.split(",") if token.strip()})
    if any(value <= 1 for value in values):
        raise ValueError("all N values must be integers > 1")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-values", type=str, default="60,80")
    parser.add_argument("--runs", type=int, default=8)
    parser.add_argument("--seed-start", type=int, default=100)
    parser.add_argument("--interval-samples", type=int, default=50)
    parser.add_argument("--null-p", type=float, default=0.2)
    parser.add_argument("--null-edge-density", type=float, default=0.2)
    parser.add_argument("--growth-link-probability", type=float, default=0.2)
    args = parser.parse_args()

    result = evaluate_minimal_growth_probe(
        n_values=_parse_n_values(args.n_values),
        runs=args.runs,
        seed_start=args.seed_start,
        interval_samples=args.interval_samples,
        null_p=args.null_p,
        null_edge_density=args.null_edge_density,
        growth_link_probability=args.growth_link_probability,
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
