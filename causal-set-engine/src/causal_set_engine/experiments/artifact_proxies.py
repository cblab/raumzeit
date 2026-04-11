"""Compatibility shim for moved artifact proxy diagnostics."""

from causal_set_engine.diagnostics.artifact_proxies import (
    ArtifactProxyValues,
    age_layering_stratification_proxy,
    birth_order_dominance_proxy,
    compute_artifact_proxies,
)

__all__ = [
    "ArtifactProxyValues",
    "birth_order_dominance_proxy",
    "age_layering_stratification_proxy",
    "compute_artifact_proxies",
]
