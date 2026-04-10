#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np

from src.config import load_config
from src.io_utils import load_json


def _as_valid_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(out):
        return None
    return out


def _model_names_from_reference_batch(path: Path) -> list[str]:
    batch = load_config(path)
    model_names: list[str] = []
    for cfg_path in batch.get("model_configs", []):
        cfg = load_config(Path(cfg_path))
        model_names.append(str(cfg.get("name", Path(cfg_path).stem)))
    return model_names


def _run_files(model_name: str) -> list[Path]:
    return sorted((Path("results/raw") / model_name).glob("seed_*.json"))


def _collect_history_k1(run_payload: dict) -> tuple[list[int], list[float]]:
    history = run_payload.get("history", [])
    if not isinstance(history, list):
        return [], []

    steps: list[int] = []
    values: list[float] = []
    for point in history:
        if not isinstance(point, dict):
            continue
        k1 = _as_valid_float(point.get("k1"))
        if k1 is None:
            continue
        steps.append(int(point.get("step", 0)))
        values.append(k1)
    return steps, values


def _collect_k2_series(run_payload: dict, field: str) -> tuple[list[int], list[float]]:
    obs = run_payload.get("observables_k2_global", [])
    if not isinstance(obs, list):
        return [], []

    steps: list[int] = []
    values: list[float] = []
    for row in obs:
        if not isinstance(row, dict):
            continue
        val = _as_valid_float(row.get(field))
        if val is None:
            continue
        steps.append(int(row.get("step", 0)))
        values.append(val)
    return steps, values


def _collect_k7_anchor_mean_series(run_payload: dict, field: str) -> tuple[list[int], list[float]]:
    obs = run_payload.get("observables_k7", [])
    if not isinstance(obs, list):
        return [], []

    per_step: dict[int, list[float]] = {}
    for row in obs:
        if not isinstance(row, dict):
            continue
        val = _as_valid_float(row.get(field))
        if val is None:
            continue
        step = int(row.get("step", 0))
        per_step.setdefault(step, []).append(val)

    if not per_step:
        return [], []

    steps = sorted(per_step.keys())
    means = [float(np.mean(np.array(per_step[s], dtype=np.float64))) for s in steps]
    return steps, means


def _plot_comparison(model_to_series: dict[str, list[tuple[list[int], list[float]]]], *, title: str, ylabel: str, out_name: str) -> bool:
    usable = {
        model: [(s, v) for s, v in series if s and v]
        for model, series in model_to_series.items()
    }
    usable = {k: v for k, v in usable.items() if v}
    if not usable:
        print(f"[skip] {out_name}: no usable series found.")
        return False

    plt.figure(figsize=(9, 5.5))

    for model, series in usable.items():
        min_len = min(len(v) for _, v in series)
        if min_len == 0:
            continue

        x = np.array(series[0][0][:min_len], dtype=np.int32)
        y = np.array([vals[:min_len] for _, vals in series], dtype=np.float64)

        for steps, vals in series:
            plt.plot(steps[:min_len], vals[:min_len], alpha=0.15, linewidth=0.8)

        plt.plot(x, np.mean(y, axis=0), linewidth=2.2, label=f"{model} mean")

    plt.title(title)
    plt.xlabel("Step")
    plt.ylabel(ylabel)
    plt.legend(loc="best", fontsize=8)
    plt.tight_layout()

    out_path = Path("figures") / out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=170)
    plt.close()
    print(f"[saved] {out_path.as_posix()}")
    return True


def main() -> None:
    reference_models = _model_names_from_reference_batch(Path("configs/paper_batch_ref.yaml"))
    if not reference_models:
        raise RuntimeError("No models found in configs/paper_batch_ref.yaml")

    k1_series: dict[str, list[tuple[list[int], list[float]]]] = {m: [] for m in reference_models}
    k2_ds_series: dict[str, list[tuple[list[int], list[float]]]] = {m: [] for m in reference_models}
    k2_dv_series: dict[str, list[tuple[list[int], list[float]]]] = {m: [] for m in reference_models}
    k7_ds_series: dict[str, list[tuple[list[int], list[float]]]] = {m: [] for m in reference_models}
    k7_iso_series: dict[str, list[tuple[list[int], list[float]]]] = {m: [] for m in reference_models}
    k7_gfc_series: dict[str, list[tuple[list[int], list[float]]]] = {m: [] for m in reference_models}

    for model in reference_models:
        files = _run_files(model)
        if not files:
            print(f"[warn] No runs found for model '{model}' under results/raw/{model}")
            continue

        for rf in files:
            payload = load_json(rf)
            steps, vals = _collect_history_k1(payload)
            if vals:
                k1_series[model].append((steps, vals))

            ds_steps, ds_vals = _collect_k2_series(payload, "spectral_dimension_ds")
            if ds_vals:
                k2_ds_series[model].append((ds_steps, ds_vals))

            dv_steps, dv_vals = _collect_k2_series(payload, "volume_growth_dimension_dv")
            if dv_vals:
                k2_dv_series[model].append((dv_steps, dv_vals))

            k7ds_steps, k7ds_vals = _collect_k7_anchor_mean_series(payload, "ds_global")
            if k7ds_vals:
                k7_ds_series[model].append((k7ds_steps, k7ds_vals))

            k7iso_steps, k7iso_vals = _collect_k7_anchor_mean_series(payload, "iso_defect")
            if k7iso_vals:
                k7_iso_series[model].append((k7iso_steps, k7iso_vals))

            k7gfc_steps, k7gfc_vals = _collect_k7_anchor_mean_series(payload, "g_fc")
            if k7gfc_vals:
                k7_gfc_series[model].append((k7gfc_steps, k7gfc_vals))

    _plot_comparison(
        k1_series,
        title="Canonical reference comparison: K1 trajectories",
        ylabel="K1",
        out_name="reference_k1_trajectory.png",
    )
    _plot_comparison(
        k2_ds_series,
        title="Canonical reference comparison: K2 spectral dimension (ds)",
        ylabel="K2 ds",
        out_name="reference_k2_ds_comparison.png",
    )
    _plot_comparison(
        k2_dv_series,
        title="Canonical reference comparison: K2 volume-growth dimension (dv)",
        ylabel="K2 dv",
        out_name="reference_k2_dv_comparison.png",
    )
    _plot_comparison(
        k7_ds_series,
        title="Canonical reference comparison: K7 ds_global",
        ylabel="K7 ds_global",
        out_name="reference_k7_ds_global_comparison.png",
    )
    _plot_comparison(
        k7_iso_series,
        title="Canonical reference comparison: K7 iso_defect",
        ylabel="K7 iso_defect",
        out_name="reference_k7_iso_defect_comparison.png",
    )
    _plot_comparison(
        k7_gfc_series,
        title="Canonical reference comparison: K7 g_fc",
        ylabel="K7 g_fc",
        out_name="reference_k7_g_fc_comparison.png",
    )


if __name__ == "__main__":
    main()
