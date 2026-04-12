"""Tests for canonical root CLI dispatch."""

from __future__ import annotations

import runpy
import sys

import pytest

from causal_set_engine import cli


def test_root_cli_dispatches_run(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_main(argv: list[str] | None = None) -> None:
        captured["argv"] = argv

    monkeypatch.setattr("causal_set_engine.experiments.run_diagnostic_demo.main", fake_main)
    cli.main(["run", "--n", "77"])

    assert captured["argv"] == ["--n", "77"]


def test_root_cli_dispatches_calibrate(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_main(argv: list[str] | None = None) -> None:
        captured["argv"] = argv

    monkeypatch.setattr("causal_set_engine.experiments.run_batch_calibration.main", fake_main)
    cli.main(["calibrate", "--runs", "9"])

    assert captured["argv"] == ["--runs", "9"]


def test_root_cli_dispatches_evaluate_growth(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_main(argv: list[str] | None = None) -> None:
        captured["argv"] = argv

    monkeypatch.setattr("causal_set_engine.experiments.run_growth_family_probe.main", fake_main)
    cli.main(["evaluate-growth", "--dynamics-family", "all"])

    assert captured["argv"] == ["--dynamics-family", "all"]


def test_root_cli_dispatches_scan_artifacts(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_main(argv: list[str] | None = None) -> None:
        captured["argv"] = argv

    monkeypatch.setattr("causal_set_engine.experiments.run_artifact_aware_scan.main", fake_main)
    cli.main(["scan-artifacts", "--runs", "6"])

    assert captured["argv"] == ["--runs", "6"]


def test_root_cli_dispatches_evaluate_myrheim(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_main(argv: list[str] | None = None) -> None:
        captured["argv"] = argv

    monkeypatch.setattr(
        "causal_set_engine.experiments.run_myrheim_meyer_evaluation.main",
        fake_main,
    )
    cli.main(["evaluate-myrheim", "--runs", "5"])

    assert captured["argv"] == ["--runs", "5"]



def test_root_cli_dispatches_evaluate_intervals(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_main(argv: list[str] | None = None) -> None:
        captured["argv"] = argv

    monkeypatch.setattr(
        "causal_set_engine.experiments.run_interval_evaluation.main",
        fake_main,
    )
    cli.main(["evaluate-intervals", "--runs", "5"])

    assert captured["argv"] == ["--runs", "5"]


def test_root_cli_dispatches_evaluate_midpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_main(argv: list[str] | None = None) -> None:
        captured["argv"] = argv

    monkeypatch.setattr(
        "causal_set_engine.experiments.run_midpoint_evaluation.main",
        fake_main,
    )
    cli.main(["evaluate-midpoint", "--runs", "5"])

    assert captured["argv"] == ["--runs", "5"]



def test_root_cli_dispatches_evaluate_layers(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_main(argv: list[str] | None = None) -> None:
        captured["argv"] = argv

    monkeypatch.setattr(
        "causal_set_engine.experiments.run_layer_evaluation.main",
        fake_main,
    )
    cli.main(["evaluate-layers", "--runs", "5"])

    assert captured["argv"] == ["--runs", "5"]

def test_root_cli_requires_subcommand() -> None:
    with pytest.raises(SystemExit):
        cli.main([])


def test_python_m_causal_set_engine_cli_invokes_main(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_main(argv: list[str] | None = None) -> None:
        captured["argv"] = argv

    monkeypatch.setattr("causal_set_engine.experiments.run_diagnostic_demo.main", fake_main)
    monkeypatch.setattr("sys.argv", ["causal_set_engine.cli", "run", "--n", "77"])
    sys.modules.pop("causal_set_engine.cli", None)
    runpy.run_module("causal_set_engine.cli", run_name="__main__")

    assert captured["argv"] == ["--n", "77"]


def test_python_m_causal_set_engine_invokes_cli_main(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_main(argv: list[str] | None = None) -> None:
        captured["argv"] = argv

    monkeypatch.setattr("causal_set_engine.experiments.run_diagnostic_demo.main", fake_main)
    monkeypatch.setattr("sys.argv", ["causal_set_engine", "run", "--n", "88"])
    runpy.run_module("causal_set_engine", run_name="__main__")

    assert captured["argv"] == ["--n", "88"]
