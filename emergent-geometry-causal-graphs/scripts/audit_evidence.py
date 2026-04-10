#!/usr/bin/env python3
"""Audit canonical evidence completeness for the 3-model manuscript scope."""

from __future__ import annotations

import json
import math
from pathlib import Path

CANONICAL_MODELS = ["baseline_ref", "v8a_fast", "v9a_fast"]
EXPECTED_FIGURES = [
    "reference_k1_trajectory.png",
    "reference_k2_ds_comparison.png",
    "reference_k2_dv_comparison.png",
    "reference_k7_ds_global_comparison.png",
    "reference_k7_iso_defect_comparison.png",
    "reference_k7_g_fc_comparison.png",
]


def _is_finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def _metric_present_in_raw(raw_files: list[Path], metric: str) -> bool:
    for raw_file in raw_files:
        payload = json.loads(raw_file.read_text())
        if metric == "k1":
            history = payload.get("history", [])
            if isinstance(history, list) and any(
                isinstance(point, dict) and _is_finite_number(point.get("k1"))
                for point in history
            ):
                return True
        elif metric == "k2":
            k2_obs = payload.get("observables_k2_global", [])
            if isinstance(k2_obs, list) and any(
                isinstance(obs, dict)
                and (
                    _is_finite_number(obs.get("spectral_dimension_ds"))
                    or _is_finite_number(obs.get("volume_growth_dimension_dv"))
                )
                for obs in k2_obs
            ):
                return True
        elif metric == "k7":
            k7_obs = payload.get("observables_k7", [])
            if isinstance(k7_obs, list) and any(
                isinstance(obs, dict)
                and any(
                    _is_finite_number(obs.get(key))
                    for key in ("ds_global", "iso_defect", "g_fc")
                )
                for obs in k7_obs
            ):
                return True
        elif metric == "k4":
            k4_obs = payload.get("observables_k4_global", [])
            if isinstance(k4_obs, list) and any(
                isinstance(obs, dict)
                and any(_is_finite_number(value) for value in obs.values())
                for obs in k4_obs
            ):
                return True
        elif metric == "k5":
            k5_obs = payload.get("observables_k5_global", [])
            if isinstance(k5_obs, list) and any(
                isinstance(obs, dict)
                and any(_is_finite_number(value) for value in obs.values())
                for obs in k5_obs
            ):
                return True
    return False


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    results_root = repo_root / "results"
    figures_root = repo_root / "figures"

    models_out: dict[str, dict[str, object]] = {}
    for model in CANONICAL_MODELS:
        raw_files = sorted((results_root / "raw" / model).glob("seed_*.json"))
        summary_path = results_root / "summary" / f"{model}_summary.json"
        summary_present = summary_path.exists() and bool(json.loads(summary_path.read_text()))

        k1_present = _metric_present_in_raw(raw_files, "k1")
        k2_present = _metric_present_in_raw(raw_files, "k2")
        k7_present = _metric_present_in_raw(raw_files, "k7")
        k4_present = _metric_present_in_raw(raw_files, "k4")
        k5_present = _metric_present_in_raw(raw_files, "k5")

        figures_present = [
            name for name in EXPECTED_FIGURES if (figures_root / name).exists()
        ]

        evidence_status = "missing"
        if raw_files or summary_present:
            evidence_status = "partial"
        if raw_files and summary_present and k1_present and k2_present and k7_present:
            evidence_status = "complete"

        models_out[model] = {
            "raw_runs_present": "yes" if raw_files else "no",
            "summary_present": "yes" if summary_present else "no",
            "k1_present": "yes" if k1_present else "no",
            "k2_present": "yes" if k2_present else "no",
            "k7_present": "yes" if k7_present else "no",
            "k4_present": "yes" if k4_present else "no",
            "k5_present": "yes" if k5_present else "no",
            "figures_present": figures_present,
            "evidence_status": evidence_status,
        }

    reference_table_present = (
        (results_root / "summary" / "reference_table.json").exists()
        and (results_root / "summary" / "reference_table.csv").exists()
    )
    reference_figures_present = all(
        (figures_root / name).exists() for name in EXPECTED_FIGURES
    )

    recommended_manuscript_status = "results-blocked"
    if any(model["evidence_status"] != "missing" for model in models_out.values()):
        recommended_manuscript_status = "results-partial"
    if (
        all(model["evidence_status"] == "complete" for model in models_out.values())
        and reference_table_present
        and reference_figures_present
    ):
        recommended_manuscript_status = "results-ready"

    audit_payload = {
        "canonical_scope": CANONICAL_MODELS,
        "models": models_out,
        "repo": {
            "canonical_scope": CANONICAL_MODELS,
            "reference_table_present": "yes" if reference_table_present else "no",
            "reference_figures_present": "yes" if reference_figures_present else "no",
            "recommended_manuscript_status": recommended_manuscript_status,
        },
    }

    out_path = results_root / "summary" / "evidence_audit.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(audit_payload, indent=2) + "\n")
    print(out_path)


if __name__ == "__main__":
    main()
