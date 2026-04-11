"""Compatibility checks for relocated stage-2/stage-3 modules."""

from causal_set_engine.diagnostics.artifact_proxies import compute_artifact_proxies as compute_new
from causal_set_engine.evaluation.scoring import build_combined_score as build_new
from causal_set_engine.experiments.artifact_proxies import compute_artifact_proxies as compute_old
from causal_set_engine.experiments.decision_metrics import build_combined_score as build_old


def test_decision_metrics_shim_reexports_scoring_symbol() -> None:
    assert build_old is build_new


def test_artifact_proxies_shim_reexports_diagnostics_symbol() -> None:
    assert compute_old is compute_new
