"""Compatibility checks for relocated modules and renamed entrypoints."""

from causal_set_engine.config.loaders import (
    load_artifact_aware_scan_config,
    load_phase2c_scan_config,
)
from causal_set_engine.diagnostics.artifact_proxies import compute_artifact_proxies as compute_new
from causal_set_engine.evaluation.scoring import build_combined_score as build_new
from causal_set_engine.experiments.artifact_aware_scan import (
    evaluate_age_biased_scan as evaluate_scan_new,
)
from causal_set_engine.experiments.artifact_proxies import compute_artifact_proxies as compute_old
from causal_set_engine.experiments.decision_metrics import build_combined_score as build_old
from causal_set_engine.experiments.phase2c_scan import (
    evaluate_age_biased_phase2c_scan as evaluate_scan_old,
)
from causal_set_engine.policies.phase2_gate import evaluate_phase2_gate as evaluate_gate_old
from causal_set_engine.policies.policy_gate import evaluate_phase2_gate as evaluate_gate_new


def test_decision_metrics_shim_reexports_scoring_symbol() -> None:
    assert build_old is build_new


def test_artifact_proxies_shim_reexports_diagnostics_symbol() -> None:
    assert compute_old is compute_new


def test_phase2c_scan_module_shim_reexports_artifact_aware_scan() -> None:
    assert evaluate_scan_old is evaluate_scan_new


def test_policy_gate_module_shim_reexports_policy_gate() -> None:
    assert evaluate_gate_old is evaluate_gate_new


def test_legacy_loader_alias_points_to_canonical_loader() -> None:
    assert load_phase2c_scan_config is load_artifact_aware_scan_config
