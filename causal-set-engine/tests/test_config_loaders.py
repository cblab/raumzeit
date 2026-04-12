"""Tests for typed config schemas/loaders."""

from __future__ import annotations

import argparse

from causal_set_engine.config.loaders import (
    load_artifact_aware_scan_config,
    load_batch_calibration_config,
    load_growth_family_probe_config,
    load_interval_evaluation_config,
    load_myrheim_meyer_evaluation_config,
    load_midpoint_evaluation_config,
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


def test_myrheim_meyer_loader_parses_dimensions_and_sizes() -> None:
    args = argparse.Namespace(
        config=None,
        dimensions="2,3,4",
        n_values="40,80",
        runs=7,
        seed_start=100,
        interval_samples=12,
        null_p=0.2,
        null_edge_density=0.22,
    )

    loaded = load_myrheim_meyer_evaluation_config(args, [])
    assert loaded.dimensions == (2, 3, 4)
    assert loaded.n_values == (40, 80)
    assert loaded.runs == 7


def test_interval_loader_parses_dimensions_sizes_and_kmax() -> None:
    args = argparse.Namespace(
        config=None,
        dimensions="2,4",
        n_values="30,50",
        runs=3,
        seed_start=20,
        null_p=0.25,
        null_edge_density=0.3,
        k_max=7,
    )

    loaded = load_interval_evaluation_config(args, [])
    assert loaded.dimensions == (2, 4)
    assert loaded.n_values == (30, 50)
    assert loaded.k_max == 7


def test_midpoint_loader_parses_sampling_controls() -> None:
    args = argparse.Namespace(
        config=None,
        dimensions="2,3,4",
        n_values="40,80",
        runs=5,
        seed_start=10,
        null_p=0.15,
        null_edge_density=0.18,
        min_interval_size=7,
        max_sampled_intervals=32,
        interval_seed_offset=2000,
    )

    loaded = load_midpoint_evaluation_config(args, [])
    assert loaded.dimensions == (2, 3, 4)
    assert loaded.n_values == (40, 80)
    assert loaded.min_interval_size == 7
    assert loaded.max_sampled_intervals == 32
    assert loaded.interval_seed_offset == 2000
