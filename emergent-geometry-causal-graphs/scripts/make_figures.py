#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np

from src.io_utils import load_json



def main() -> None:
    baseline_runs = sorted(Path("results/raw/baseline").glob("seed_*.json"))
    if not baseline_runs:
        raise FileNotFoundError("No baseline runs found under results/raw/baseline")

    histories = []
    for run_file in baseline_runs:
        payload = load_json(run_file)
        history = payload.get("history", [])
        steps = [int(point.get("step", 0)) for point in history]
        k1 = [float(point.get("k1", 0.0)) for point in history]
        histories.append((steps, k1, run_file.stem))

    min_len = min(len(k1) for _, k1, _ in histories)
    step_axis = np.array(histories[0][0][:min_len], dtype=np.int32)
    stacked = np.array([k1[:min_len] for _, k1, _ in histories], dtype=np.float64)
    mean_curve = np.mean(stacked, axis=0)

    plt.figure(figsize=(8, 5))
    for steps, k1, label in histories:
        plt.plot(steps[:min_len], k1[:min_len], alpha=0.3, linewidth=1.0, label=label)

    plt.plot(step_axis, mean_curve, color="black", linewidth=2.0, label="mean")
    plt.xlabel("Step")
    plt.ylabel("K1")
    plt.title("Baseline K1 trajectories")
    plt.legend(loc="best", fontsize=7, ncol=2)
    plt.tight_layout()

    out_path = Path("figures/fig1_baseline_k1.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=160)
    plt.close()

    print(f"Saved {out_path.as_posix()}")


if __name__ == "__main__":
    main()
