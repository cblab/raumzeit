#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import load_config
from src.io_utils import save_json
from src.runners import run_single



def main() -> None:
    parser = argparse.ArgumentParser(description="Run a single emergent-geometry simulation.")
    parser.add_argument("--config", required=True, help="Path to model config YAML")
    parser.add_argument("--seed", type=int, default=None, help="Optional seed override")
    parser.add_argument("--output", default=None, help="Optional path for full JSON output")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.seed is not None:
        config["seed"] = int(args.seed)

    result = run_single(config)

    if args.output:
        save_json(args.output, result)
        print(f"Saved result to {Path(args.output).as_posix()}")
        return

    final = result.get("final", {})
    summary = {
        "seed": int(result.get("config", {}).get("seed", -1)),
        "steps": int(result.get("config", {}).get("steps", 0)),
        "final_k1": float(final.get("k1", 0.0)),
        "final_num_nodes": int(final.get("num_nodes", 0)),
        "final_active_edges": int(final.get("active_edges", 0)),
    }
    print(summary)


if __name__ == "__main__":
    main()
