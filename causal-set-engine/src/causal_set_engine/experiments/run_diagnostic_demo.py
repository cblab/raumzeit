"""Run a minimal diagnostic demo."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from causal_set_engine.config.loaders import load_diagnostic_demo_config
from causal_set_engine.diagnostics.basic import (
    estimate_dimension_chain_height,
    longest_chain_length,
    num_comparable_pairs,
    num_elements,
    relation_density,
    sampled_interval_statistics,
)
from causal_set_engine.generators.minkowski_2d import generate_minkowski_2d
from causal_set_engine.observables.cst import estimate_myrheim_meyer_dimension


def main(argv: Sequence[str] | None = None) -> None:
    """Generate a 2D Minkowski causal set and print summary diagnostics."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="optional path to JSON/TOML/YAML config file (CLI flags override file values)",
    )
    parser.add_argument("--n", type=int, default=50, help="number of sprinkled events")
    parser.add_argument("--seed", type=int, default=7, help="random seed")
    parser.add_argument(
        "--interval-samples",
        type=int,
        default=30,
        help="number of related pairs sampled for interval statistics",
    )
    args = parser.parse_args(argv)
    raw_cli_args = list(argv) if argv is not None else sys.argv[1:]
    config = load_diagnostic_demo_config(args, raw_cli_args)

    cset, events = generate_minkowski_2d(n=config.n, seed=config.seed)

    summary = {
        "n_events": len(events),
        "num_elements": num_elements(cset),
        "num_comparable_pairs": num_comparable_pairs(cset),
        "relation_density": relation_density(cset),
        "longest_chain_length": longest_chain_length(cset),
        "estimated_dimension_chain_height": estimate_dimension_chain_height(cset),
        "estimated_dimension_myrheim_meyer": estimate_myrheim_meyer_dimension(cset),
        "interval_statistics": sampled_interval_statistics(
            cset, pairs=config.interval_samples, seed=config.seed
        ),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
