"""Typed run configuration schemas for experiment entrypoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


def parse_csv_ints(text: str) -> tuple[int, ...]:
    """Parse comma-separated integers into a sorted unique tuple."""
    values = tuple(sorted({int(token.strip()) for token in text.split(",") if token.strip()}))
    if not values:
        raise ValueError("value list cannot be empty")
    return values


def parse_csv_floats(text: str) -> tuple[float, ...]:
    """Parse comma-separated floats preserving order."""
    values = tuple(float(token.strip()) for token in text.split(",") if token.strip())
    if not values:
        raise ValueError("value list cannot be empty")
    return values


@dataclass(frozen=True)
class DiagnosticDemoConfig:
    """Typed config for `run_diagnostic_demo`."""

    n: int = 50
    seed: int = 7
    interval_samples: int = 30


@dataclass(frozen=True)
class BatchSweepConfig:
    """Shared batch sweep settings used across study entrypoints."""

    n_values: tuple[int, ...] = (60, 80)
    runs: int = 8
    seed_start: int = 100
    interval_samples: int = 50
    null_p: float = 0.2
    null_edge_density: float = 0.2


@dataclass(frozen=True)
class BatchCalibrationConfig:
    """Typed config for `run_batch_calibration`."""

    dimension: Literal[2, 3, 4] = 2
    n: int = 80
    n_values_text: str | None = None
    runs: int = 8
    seed_start: int = 100
    null_p: float = 0.2
    null_edge_density: float = 0.2
    interval_samples: int = 50


@dataclass(frozen=True)
class GrowthFamilyProbeConfig:
    """Typed config for `run_growth_family_probe`."""

    n_values: tuple[int, ...] = (60, 80)
    runs: int = 8
    seed_start: int = 100
    interval_samples: int = 50
    null_p: float = 0.2
    null_edge_density: float = 0.2
    growth_link_probability: float = 0.2
    sparse_base_link_probability: float = 0.25
    age_bias_mode: Literal["older", "newer"] = "older"
    lookback_window: int = 8
    dynamics_family: str = "bernoulli-forward"


@dataclass(frozen=True)
class ArtifactAwareScanConfig:
    """Typed config for `run_artifact_aware_scan`."""

    n_values: tuple[int, ...] = (60, 80)
    runs: int = 8
    seed_start: int = 100
    interval_samples: int = 50
    null_p: float = 0.2
    null_edge_density: float = 0.2
    link_density_grid: tuple[float, ...] = (0.16, 0.22, 0.28)
    bias_strength_grid: tuple[float, ...] = (0.0, 0.5, 1.0)
    age_bias_mode: Literal["older", "newer"] = "older"

