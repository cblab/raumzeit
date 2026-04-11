"""Run a minimal phase-1 calibration demo."""

from __future__ import annotations

import argparse
import json

from causal_set_engine.diagnostics.basic import (
    longest_chain_length,
    num_comparable_pairs,
    num_elements,
    relation_density,
)
from causal_set_engine.generators.minkowski_2d import generate_minkowski_2d


def main() -> None:
    """Generate a 2D Minkowski causal set and print summary diagnostics."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=50, help="number of sprinkled events")
    parser.add_argument("--seed", type=int, default=7, help="random seed")
    args = parser.parse_args()

    cset, events = generate_minkowski_2d(n=args.n, seed=args.seed)

    summary = {
        "n_events": len(events),
        "num_elements": num_elements(cset),
        "num_comparable_pairs": num_comparable_pairs(cset),
        "relation_density": relation_density(cset),
        "longest_chain_length": longest_chain_length(cset),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
