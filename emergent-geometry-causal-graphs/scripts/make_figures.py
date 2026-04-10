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


def _plot_baseline_k1(histories: list[tuple[list[int], list[float], str]]) -> None:
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


def _plot_k2_series(step_series: list[list[int]], value_series: list[list[float]], ylabel: str, out_name: str) -> None:
    min_len = min(len(v) for v in value_series)
    if min_len == 0:
        return

    x = np.array(step_series[0][:min_len], dtype=np.int32)
    y = np.array([vals[:min_len] for vals in value_series], dtype=np.float64)

    plt.figure(figsize=(8, 5))
    for steps, vals in zip(step_series, value_series, strict=False):
        plt.plot(steps[:min_len], vals[:min_len], alpha=0.3, linewidth=1.0)

    plt.plot(x, np.mean(y, axis=0), color="black", linewidth=2.0, label="mean")
    plt.xlabel("Step")
    plt.ylabel(ylabel)
    plt.title(f"Baseline {ylabel} trajectories")
    plt.legend(loc="best", fontsize=8)
    plt.tight_layout()

    out_path = Path("figures") / out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=160)
    plt.close()
    print(f"Saved {out_path.as_posix()}")


def _aggregate_k7_per_step(obs: list[dict], field: str) -> tuple[list[int], list[float]]:
    per_step: dict[int, list[float]] = {}
    for row in obs:
        if not isinstance(row, dict):
            continue
        val = row.get(field)
        if val is None:
            continue
        step = int(row.get("step", 0))
        per_step.setdefault(step, []).append(float(val))

    if not per_step:
        return [], []

    steps = sorted(per_step.keys())
    values = [float(np.mean(np.array(per_step[s], dtype=np.float64))) for s in steps]
    return steps, values


def _plot_k7_series(step_series: list[list[int]], value_series: list[list[float]], ylabel: str, out_name: str) -> None:
    min_len = min(len(v) for v in value_series)
    if min_len == 0:
        return

    x = np.array(step_series[0][:min_len], dtype=np.int32)
    y = np.array([vals[:min_len] for vals in value_series], dtype=np.float64)

    plt.figure(figsize=(8, 5))
    for steps, vals in zip(step_series, value_series, strict=False):
        plt.plot(steps[:min_len], vals[:min_len], alpha=0.2, linewidth=1.0, color="tab:blue")

    plt.plot(x, np.mean(y, axis=0), color="black", linewidth=2.0, label="mean across seeds")
    plt.xlabel("Step")
    plt.ylabel(ylabel)
    plt.title(f"Baseline {ylabel} (K7 fixed anchors)")
    plt.legend(loc="best", fontsize=8)
    plt.tight_layout()

    out_path = Path("figures") / out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=160)
    plt.close()
    print(f"Saved {out_path.as_posix()}")


def main() -> None:
    baseline_runs = sorted(Path("results/raw/baseline").glob("seed_*.json"))
    if not baseline_runs:
        raise FileNotFoundError("No baseline runs found under results/raw/baseline")

    histories: list[tuple[list[int], list[float], str]] = []
    k2_steps_ds: list[list[int]] = []
    k2_vals_ds: list[list[float]] = []
    k2_steps_dv: list[list[int]] = []
    k2_vals_dv: list[list[float]] = []
    k7_steps_ds: list[list[int]] = []
    k7_vals_ds: list[list[float]] = []
    k7_steps_iso: list[list[int]] = []
    k7_vals_iso: list[list[float]] = []

    for run_file in baseline_runs:
        payload = load_json(run_file)

        history = payload.get("history", [])
        steps = [int(point.get("step", 0)) for point in history]
        k1 = [float(point.get("k1", 0.0)) for point in history]
        histories.append((steps, k1, run_file.stem))

        k2_obs = payload.get("observables_k2_global", [])
        if isinstance(k2_obs, list) and k2_obs:
            ds_points = [point for point in k2_obs if point.get("spectral_dimension_ds") is not None]
            dv_points = [point for point in k2_obs if point.get("volume_growth_dimension_dv") is not None]

            if ds_points:
                k2_steps_ds.append([int(point.get("step", 0)) for point in ds_points])
                k2_vals_ds.append([float(point.get("spectral_dimension_ds", 0.0)) for point in ds_points])

            if dv_points:
                k2_steps_dv.append([int(point.get("step", 0)) for point in dv_points])
                k2_vals_dv.append([float(point.get("volume_growth_dimension_dv", 0.0)) for point in dv_points])

        k7_obs = payload.get("observables_k7", [])
        if isinstance(k7_obs, list) and k7_obs:
            ds_steps, ds_vals = _aggregate_k7_per_step(k7_obs, field="ds_global")
            if ds_steps:
                k7_steps_ds.append(ds_steps)
                k7_vals_ds.append(ds_vals)

            iso_steps, iso_vals = _aggregate_k7_per_step(k7_obs, field="iso_defect")
            if iso_steps:
                k7_steps_iso.append(iso_steps)
                k7_vals_iso.append(iso_vals)

    _plot_baseline_k1(histories)

    if k2_vals_ds:
        _plot_k2_series(k2_steps_ds, k2_vals_ds, "K2 spectral dimension ds", "fig2_baseline_k2_ds.png")

    if k2_vals_dv:
        _plot_k2_series(k2_steps_dv, k2_vals_dv, "K2 volume-growth dimension dv", "fig3_baseline_k2_dv.png")

    if k7_vals_ds:
        _plot_k7_series(k7_steps_ds, k7_vals_ds, "K7 anchor-local ds_global", "fig3_baseline_k7.png")

    if k7_vals_iso:
        _plot_k7_series(k7_steps_iso, k7_vals_iso, "K7 anchor-local iso_defect", "fig3b_baseline_k7_iso.png")


if __name__ == "__main__":
    main()
