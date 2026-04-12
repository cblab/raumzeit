"""Simple loaders for typed experiment configuration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from causal_set_engine.config.schema import (
    ArtifactAwareScanConfig,
    BatchCalibrationConfig,
    DiagnosticDemoConfig,
    GrowthFamilyProbeConfig,
    IntervalEvaluationConfig,
    LayerProfileEvaluationConfig,
    MyrheimMeyerEvaluationConfig,
    MidpointEvaluationConfig,
    parse_csv_floats,
    parse_csv_ints,
)


def _load_serialized_mapping(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".json":
        return json.loads(source.read_text())
    if suffix == ".toml":
        try:
            import tomllib
        except ModuleNotFoundError as exc:  # pragma: no cover - Python <3.11 fallback path
            raise RuntimeError(
                "TOML config requires Python 3.11+ (tomllib) or use JSON/YAML config files."
            ) from exc
        return tomllib.loads(source.read_text())
    if suffix in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "YAML config requires PyYAML (`pip install pyyaml`) or use JSON/TOML config files."
            ) from exc
        loaded = yaml.safe_load(source.read_text())
        if not isinstance(loaded, dict):
            raise ValueError("config file must contain a mapping/object at top level")
        return loaded
    raise ValueError("unsupported config file; use .json, .toml, .yaml, or .yml")


def _provided_long_flags(argv: list[str]) -> set[str]:
    provided: set[str] = set()
    for token in argv:
        if not token.startswith("--"):
            continue
        key = token.split("=", 1)[0][2:].replace("-", "_")
        if key:
            provided.add(key)
    return provided


def _merged_values(args: argparse.Namespace, argv: list[str]) -> dict[str, Any]:
    values = vars(args).copy()
    config_path = values.get("config")
    if not config_path:
        return values

    loaded = _load_serialized_mapping(config_path)
    provided = _provided_long_flags(argv)

    for key, value in loaded.items():
        if key not in values or key in provided:
            continue
        values[key] = value
    return values


def load_diagnostic_demo_config(args: argparse.Namespace, argv: list[str]) -> DiagnosticDemoConfig:
    values = _merged_values(args, argv)
    return DiagnosticDemoConfig(
        n=int(values["n"]),
        seed=int(values["seed"]),
        interval_samples=int(values["interval_samples"]),
    )


def load_batch_calibration_config(args: argparse.Namespace, argv: list[str]) -> BatchCalibrationConfig:
    values = _merged_values(args, argv)
    n_values_text = values.get("n_values")
    if isinstance(n_values_text, list):
        n_values_text = ",".join(str(item) for item in n_values_text)
    return BatchCalibrationConfig(
        dimension=int(values["dimension"]),
        n=int(values["n"]),
        n_values_text=str(n_values_text) if n_values_text is not None else None,
        runs=int(values["runs"]),
        seed_start=int(values["seed_start"]),
        null_p=float(values["null_p"]),
        null_edge_density=float(values["null_edge_density"]),
        interval_samples=int(values["interval_samples"]),
    )


def load_growth_family_probe_config(
    args: argparse.Namespace,
    argv: list[str],
) -> GrowthFamilyProbeConfig:
    values = _merged_values(args, argv)
    n_values_input = values["n_values"]
    n_values = (
        parse_csv_ints(n_values_input)
        if isinstance(n_values_input, str)
        else tuple(int(value) for value in n_values_input)
    )
    return GrowthFamilyProbeConfig(
        n_values=n_values,
        runs=int(values["runs"]),
        seed_start=int(values["seed_start"]),
        interval_samples=int(values["interval_samples"]),
        null_p=float(values["null_p"]),
        null_edge_density=float(values["null_edge_density"]),
        growth_link_probability=float(values["growth_link_probability"]),
        sparse_base_link_probability=float(values["sparse_base_link_probability"]),
        age_bias_mode=str(values["age_bias_mode"]),
        lookback_window=int(values["lookback_window"]),
        dynamics_family=str(values["dynamics_family"]),
    )


def load_artifact_aware_scan_config(
    args: argparse.Namespace,
    argv: list[str],
) -> ArtifactAwareScanConfig:
    values = _merged_values(args, argv)

    n_values_input = values["n_values"]
    n_values = (
        parse_csv_ints(n_values_input)
        if isinstance(n_values_input, str)
        else tuple(int(value) for value in n_values_input)
    )

    link_density_input = values["link_density_grid"]
    link_density_grid = (
        parse_csv_floats(link_density_input)
        if isinstance(link_density_input, str)
        else tuple(float(value) for value in link_density_input)
    )

    bias_strength_input = values["bias_strength_grid"]
    bias_strength_grid = (
        parse_csv_floats(bias_strength_input)
        if isinstance(bias_strength_input, str)
        else tuple(float(value) for value in bias_strength_input)
    )

    return ArtifactAwareScanConfig(
        n_values=n_values,
        runs=int(values["runs"]),
        seed_start=int(values["seed_start"]),
        interval_samples=int(values["interval_samples"]),
        null_p=float(values["null_p"]),
        null_edge_density=float(values["null_edge_density"]),
        link_density_grid=link_density_grid,
        bias_strength_grid=bias_strength_grid,
        age_bias_mode=str(values["age_bias_mode"]),
    )


def load_myrheim_meyer_evaluation_config(
    args: argparse.Namespace,
    argv: list[str],
) -> MyrheimMeyerEvaluationConfig:
    values = _merged_values(args, argv)

    dimensions_input = values["dimensions"]
    dimensions = (
        parse_csv_ints(dimensions_input)
        if isinstance(dimensions_input, str)
        else tuple(int(value) for value in dimensions_input)
    )
    if any(dimension not in {2, 3, 4} for dimension in dimensions):
        raise ValueError("dimensions must be chosen from {2, 3, 4}")

    n_values_input = values["n_values"]
    n_values = (
        parse_csv_ints(n_values_input)
        if isinstance(n_values_input, str)
        else tuple(int(value) for value in n_values_input)
    )

    return MyrheimMeyerEvaluationConfig(
        dimensions=dimensions,
        n_values=n_values,
        runs=int(values["runs"]),
        seed_start=int(values["seed_start"]),
        interval_samples=int(values["interval_samples"]),
        null_p=float(values["null_p"]),
        null_edge_density=float(values["null_edge_density"]),
    )


def load_interval_evaluation_config(
    args: argparse.Namespace,
    argv: list[str],
) -> IntervalEvaluationConfig:
    values = _merged_values(args, argv)

    dimensions_input = values["dimensions"]
    dimensions = (
        parse_csv_ints(dimensions_input)
        if isinstance(dimensions_input, str)
        else tuple(int(value) for value in dimensions_input)
    )
    if any(dimension not in {2, 3, 4} for dimension in dimensions):
        raise ValueError("dimensions must be chosen from {2, 3, 4}")

    n_values_input = values["n_values"]
    n_values = (
        parse_csv_ints(n_values_input)
        if isinstance(n_values_input, str)
        else tuple(int(value) for value in n_values_input)
    )

    return IntervalEvaluationConfig(
        dimensions=dimensions,
        n_values=n_values,
        runs=int(values["runs"]),
        seed_start=int(values["seed_start"]),
        null_p=float(values["null_p"]),
        null_edge_density=float(values["null_edge_density"]),
        k_max=int(values["k_max"]),
    )


def load_midpoint_evaluation_config(
    args: argparse.Namespace,
    argv: list[str],
) -> MidpointEvaluationConfig:
    values = _merged_values(args, argv)

    dimensions_input = values["dimensions"]
    dimensions = (
        parse_csv_ints(dimensions_input)
        if isinstance(dimensions_input, str)
        else tuple(int(value) for value in dimensions_input)
    )
    if any(dimension not in {2, 3, 4} for dimension in dimensions):
        raise ValueError("dimensions must be chosen from {2, 3, 4}")

    n_values_input = values["n_values"]
    n_values = (
        parse_csv_ints(n_values_input)
        if isinstance(n_values_input, str)
        else tuple(int(value) for value in n_values_input)
    )

    return MidpointEvaluationConfig(
        dimensions=dimensions,
        n_values=n_values,
        runs=int(values["runs"]),
        seed_start=int(values["seed_start"]),
        null_p=float(values["null_p"]),
        null_edge_density=float(values["null_edge_density"]),
        min_interval_size=int(values["min_interval_size"]),
        max_sampled_intervals=int(values["max_sampled_intervals"]),
        interval_seed_offset=int(values["interval_seed_offset"]),
    )


def load_layer_profile_evaluation_config(
    args: argparse.Namespace,
    argv: list[str],
) -> LayerProfileEvaluationConfig:
    values = _merged_values(args, argv)

    dimensions_input = values["dimensions"]
    dimensions = (
        parse_csv_ints(dimensions_input)
        if isinstance(dimensions_input, str)
        else tuple(int(value) for value in dimensions_input)
    )
    if any(dimension not in {2, 3, 4} for dimension in dimensions):
        raise ValueError("dimensions must be chosen from {2, 3, 4}")

    n_values_input = values["n_values"]
    n_values = (
        parse_csv_ints(n_values_input)
        if isinstance(n_values_input, str)
        else tuple(int(value) for value in n_values_input)
    )

    return LayerProfileEvaluationConfig(
        dimensions=dimensions,
        n_values=n_values,
        runs=int(values["runs"]),
        seed_start=int(values["seed_start"]),
        null_p=float(values["null_p"]),
        null_edge_density=float(values["null_edge_density"]),
        min_interval_size=int(values["min_interval_size"]),
        max_sampled_intervals=int(values["max_sampled_intervals"]),
        interval_seed_offset=int(values["interval_seed_offset"]),
    )
