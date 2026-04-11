"""Tests for typed config schemas/loaders introduced in stage 6."""

from __future__ import annotations

import argparse

from causal_set_engine.config.loaders import (
    load_batch_calibration_config,
    load_growth_family_probe_config,
    load_artifact_aware_scan_config,
)


def test_growth_family_probe_loader_maps_csv_to_typed_tuple() -> None:
    args = argparse.Namespace(
        config=None,
        n_values="60,80",
        runs=8,
        seed_start=100,
        interval_samples=50,
        null_p=0.2,
        null_edge_density=0.2,
        growth_link_probability=0.2,
        sparse_base_link_probability=0.25,
        age_bias_mode="older",
        lookback_window=8,
        dynamics_family="all",
    )

    config = load_growth_family_probe_config(args, [])

    assert config.n_values == (60, 80)
    assert config.dynamics_family == "all"


def test_batch_calibration_loader_config_file_applies_when_flag_not_provided(tmp_path) -> None:
    config_file = tmp_path / "batch_config.json"
    config_file.write_text('{"dimension": 4, "n": 110, "runs": 12, "n_values": "90,110"}')

    args = argparse.Namespace(
        config=str(config_file),
        dimension=2,
        n=80,
        n_values=None,
        runs=8,
        seed_start=100,
        null_p=0.2,
        null_edge_density=0.2,
        interval_samples=50,
    )

    loaded = load_batch_calibration_config(args, ["--config", str(config_file)])

    assert loaded.dimension == 4
    assert loaded.n == 110
    assert loaded.runs == 12
    assert loaded.n_values_text == "90,110"


def test_artifact_aware_scan_loader_cli_values_override_config_file(tmp_path) -> None:
    config_file = tmp_path / "scan_config.json"
    config_file.write_text('{"runs": 99, "link_density_grid": [0.5], "age_bias_mode": "newer"}')

    args = argparse.Namespace(
        config=str(config_file),
        n_values="60,80",
        runs=8,
        seed_start=100,
        interval_samples=50,
        null_p=0.2,
        null_edge_density=0.2,
        link_density_grid="0.16,0.22,0.28",
        bias_strength_grid="0.0,0.5,1.0",
        age_bias_mode="older",
    )

    loaded = load_artifact_aware_scan_config(
        args,
        ["--config", str(config_file), "--runs", "8", "--age-bias-mode", "older"],
    )

    assert loaded.runs == 8
    assert loaded.age_bias_mode == "older"
    assert loaded.link_density_grid == (0.5,)
