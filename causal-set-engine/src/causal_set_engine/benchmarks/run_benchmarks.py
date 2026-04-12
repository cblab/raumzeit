"""CLI entrypoint for benchmark-suite execution."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from causal_set_engine.benchmarks.benchmark_suite import (
    BenchmarkConfig,
    format_report,
    run_benchmark_suite,
)


def _parse_int_csv(raw: str) -> tuple[int, ...]:
    values = tuple(int(part.strip()) for part in raw.split(",") if part.strip())
    if not values:
        raise ValueError("expected at least one integer")
    return values


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-values", type=str, default="40,80,120")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seeds", type=str, default="100,101,102")
    parser.add_argument("--k-max", type=int, default=5)
    parser.add_argument("--min-interval-size", type=int, default=8)
    parser.add_argument("--max-sampled-intervals", type=int, default=64)
    parser.add_argument(
        "--skip-workflow-benchmarks",
        action="store_true",
        help="disable optional end-to-end workflow timing",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    config = BenchmarkConfig(
        n_values=_parse_int_csv(args.n_values),
        repeats=args.repeats,
        seeds=_parse_int_csv(args.seeds),
        k_max=args.k_max,
        min_interval_size=args.min_interval_size,
        max_sampled_intervals=args.max_sampled_intervals,
        include_workflow_benchmarks=not args.skip_workflow_benchmarks,
    )
    report = run_benchmark_suite(config)
    print(format_report(report))


if __name__ == "__main__":
    main()
