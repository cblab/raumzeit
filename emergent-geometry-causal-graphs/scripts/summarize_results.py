#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from src.io_utils import load_json, save_json


def _safe_mean(vals: list[float]) -> float | None:
    if not vals:
        return None
    return float(np.mean(np.array(vals, dtype=np.float64)))


def main() -> None:
    raw_dir = Path("results/raw")
    by_model: dict[str, list[dict]] = defaultdict(list)
    files_found = 0
    files_loaded = 0
    files_skipped = 0
    models_summarized = 0

    model_files: dict[str, list[Path]] = defaultdict(list)
    for raw_file in sorted(raw_dir.glob("*/*.json")):
        files_found += 1
        model = raw_file.parent.name
        model_files[model].append(raw_file)

        if raw_file.suffix.lower() != ".json":
            files_skipped += 1
            print(f"[warn] Skipping non-JSON file: {raw_file.as_posix()}")
            continue

        file_size = raw_file.stat().st_size
        if file_size == 0:
            files_skipped += 1
            print(f"[warn] Skipping empty file: {raw_file.as_posix()}")
            continue

        try:
            payload = load_json(raw_file)
        except (ValueError, json.JSONDecodeError, OSError) as exc:
            files_skipped += 1
            print(f"[warn] Skipping unreadable JSON: {raw_file.as_posix()} ({exc})")
            continue

        if not isinstance(payload, dict):
            files_skipped += 1
            print(f"[warn] Skipping JSON with unexpected root type: {raw_file.as_posix()}")
            continue

        by_model[model].append(payload)
        files_loaded += 1

    out_dir = Path("results/summary")
    out_dir.mkdir(parents=True, exist_ok=True)

    for model, model_raw_files in model_files.items():
        runs = by_model.get(model, [])
        if not runs:
            print(
                f"[warn] Model '{model}' has no valid runs "
                f"({len(model_raw_files)} file(s) found). Skipping summary generation."
            )
            continue

        finals = [r.get("final", {}) for r in runs]
        k1_vals = np.array([float(f.get("k1", 0.0)) for f in finals], dtype=np.float64)
        num_nodes_vals = np.array([float(f.get("num_nodes", 0.0)) for f in finals], dtype=np.float64)
        active_edges_vals = np.array([float(f.get("active_edges", 0.0)) for f in finals], dtype=np.float64)

        k2_final_ds: list[float] = []
        k2_final_dv: list[float] = []
        k2_run_count = 0

        for run in runs:
            obs = run.get("observables_k2_global", [])
            if not isinstance(obs, list) or not obs:
                continue

            last = obs[-1]
            if not isinstance(last, dict):
                continue

            k2_run_count += 1
            ds = last.get("spectral_dimension_ds")
            dv = last.get("volume_growth_dimension_dv")

            if ds is not None:
                k2_final_ds.append(float(ds))
            if dv is not None:
                k2_final_dv.append(float(dv))

        summary = {
            "model": model,
            "run_count": int(len(runs)),
            "mean_final_k1": float(np.mean(k1_vals)) if k1_vals.size else 0.0,
            "std_final_k1": float(np.std(k1_vals)) if k1_vals.size else 0.0,
            "mean_final_num_nodes": float(np.mean(num_nodes_vals)) if num_nodes_vals.size else 0.0,
            "mean_final_active_edges": float(np.mean(active_edges_vals)) if active_edges_vals.size else 0.0,
            "k2_run_count": int(k2_run_count),
            "k2_missing_run_count": int(len(runs) - k2_run_count),
            "mean_final_k2_ds": _safe_mean(k2_final_ds),
            "mean_final_k2_dv": _safe_mean(k2_final_dv),
        }

        out_path = out_dir / f"{model}_summary.json"
        save_json(out_path, summary)
        print(f"[summary] {out_path.as_posix()}")
        models_summarized += 1

    print(
        "[done] "
        f"files_found={files_found}, "
        f"files_loaded={files_loaded}, "
        f"files_skipped={files_skipped}, "
        f"models_summarized={models_summarized}"
    )


if __name__ == "__main__":
    main()
