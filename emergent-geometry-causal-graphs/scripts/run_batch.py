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
    parser = argparse.ArgumentParser(description="Run a deterministic batch of simulations.")
    parser.add_argument("--config", required=True, help="Path to batch YAML config")
    args = parser.parse_args()

    batch_config = load_config(args.config)
    model_configs = batch_config.get("model_configs", [])
    seeds = [int(s) for s in batch_config.get("seeds", [])]

    manifest = {
        "batch_config": str(Path(args.config)),
        "models": [],
        "runs": [],
    }

    for model_cfg_path in model_configs:
        cfg_path = Path(model_cfg_path)
        model_config = load_config(cfg_path)
        model_name = str(model_config.get("name", cfg_path.stem))
        manifest["models"].append({"name": model_name, "config": str(cfg_path)})

        for seed in seeds:
            run_config = dict(model_config)
            run_config["seed"] = int(seed)
            result = run_single(run_config)

            out_path = Path("results/raw") / model_name / f"seed_{seed}.json"
            save_json(out_path, result)

            manifest["runs"].append(
                {
                    "model": model_name,
                    "seed": int(seed),
                    "output": out_path.as_posix(),
                    "final": result.get("final", {}),
                }
            )

            print(f"[done] model={model_name} seed={seed} -> {out_path.as_posix()}")

    save_json("results/manifests/batch_manifest.json", manifest)
    print("Saved batch manifest to results/manifests/batch_manifest.json")


if __name__ == "__main__":
    main()
