"""Canonical researcher-facing CLI for causal-set-engine workflows."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from causal_set_engine.experiments import (
    run_artifact_aware_scan,
    run_batch_calibration,
    run_diagnostic_demo,
    run_growth_family_probe,
    run_myrheim_meyer_evaluation,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the root parser with researcher-facing workflow subcommands."""
    parser = argparse.ArgumentParser(
        prog="causal-set",
        description="Canonical researcher workflow CLI for causal-set-engine.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("run", help="run the diagnostic demo workflow")
    subparsers.add_parser("calibrate", help="run the batch calibration workflow")
    subparsers.add_parser(
        "evaluate-growth",
        help="run policy-gated growth family evaluation workflow",
    )
    subparsers.add_parser(
        "scan-artifacts",
        help="run artifact-aware growth scan workflow",
    )
    subparsers.add_parser(
        "evaluate-myrheim",
        help="run focused Myrheim-Meyer evaluation workflow",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Dispatch to canonical workflow entrypoints."""
    parser = build_parser()
    args, remaining = parser.parse_known_args(argv)

    if args.command == "run":
        run_diagnostic_demo.main(remaining)
        return
    if args.command == "calibrate":
        run_batch_calibration.main(remaining)
        return
    if args.command == "evaluate-growth":
        run_growth_family_probe.main(remaining)
        return
    if args.command == "scan-artifacts":
        run_artifact_aware_scan.main(remaining)
        return
    if args.command == "evaluate-myrheim":
        run_myrheim_meyer_evaluation.main(remaining)
        return

    parser.error(f"unknown command: {args.command}")


if __name__ == "__main__":
    main()
