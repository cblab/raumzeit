#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from src.io_utils import load_json, save_json



def main() -> None:
    by_model: dict[str, list[dict]] = defaultdict(list)

    for raw_file in sorted(Path("results/raw").glob("*/*.json")):
        model = raw_file.parent.name
        payload = load_json(raw_file)
        by_model[model].append(payload)

    out_dir = Path("results/summary")
    out_dir.mkdir(parents=True, exist_ok=True)

    for model, runs in by_model.items():
        finals = [r.get("final", {}) for r in runs]
        k1_vals = np.array([float(f.get("k1", 0.0)) for f in finals], dtype=np.float64)
        num_nodes_vals = np.array([float(f.get("num_nodes", 0.0)) for f in finals], dtype=np.float64)
        active_edges_vals = np.array([float(f.get("active_edges", 0.0)) for f in finals], dtype=np.float64)

        summary = {
            "model": model,
            "n_runs": int(len(runs)),
            "mean_final_k1": float(np.mean(k1_vals)) if k1_vals.size else 0.0,
            "std_final_k1": float(np.std(k1_vals)) if k1_vals.size else 0.0,
            "mean_final_num_nodes": float(np.mean(num_nodes_vals)) if num_nodes_vals.size else 0.0,
            "mean_final_active_edges": float(np.mean(active_edges_vals)) if active_edges_vals.size else 0.0,
        }

        out_path = out_dir / f"{model}_summary.json"
        save_json(out_path, summary)
        print(f"[summary] {out_path.as_posix()}")


if __name__ == "__main__":
    main()
