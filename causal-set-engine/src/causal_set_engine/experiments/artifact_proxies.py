"""Explicit artifact proxy utilities for primitive growth diagnostics.

These proxies are intentionally heuristic and transparent.

- Birth-order dominance proxy:
  Pearson correlation between olderness and out-degree.
  olderness(i) = 1 - i/(N-1), out_degree(i) = number of direct future links from i.
  proxy = max(0, corr(olderness, out_degree)).
  Values near 1 indicate stronger dominance of early-born elements in generating links.

- Age-layering proxy:
  Birth indices are binned into 4 equal-width layers. We count direct-edge frequencies
  across layer pairs (source_layer, target_layer) and compute normalized entropy.
  proxy = 1 - H/H_max, where H is Shannon entropy over layer-pair frequencies.
  Values near 1 indicate stronger stratification into a narrow set of age-layer channels.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from causal_set_engine.core.causal_set import CausalSet


@dataclass(frozen=True)
class ArtifactProxyValues:
    birth_order_dominance: float
    age_layering_stratification: float


def _pearson_correlation(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x <= 0.0 or var_y <= 0.0:
        return 0.0
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    return cov / math.sqrt(var_x * var_y)


def birth_order_dominance_proxy(cset: CausalSet) -> float:
    """Estimate whether early births dominate link production.

    Formula:
    - olderness(i) = 1 - i/(N-1)
    - out_degree(i) = |direct_future(i)|
    - raw = corr(olderness, out_degree)
    - proxy = clamp(max(0, raw), 0, 1)
    """

    elements = sorted(cset.elements)
    n = len(elements)
    if n < 2:
        return 0.0

    max_idx = float(max(elements)) if max(elements) > 0 else 1.0
    direct = cset.direct_relations
    olderness = [1.0 - (float(i) / max_idx) for i in elements]
    out_degree = [float(len(direct.get(i, set()))) for i in elements]

    raw = _pearson_correlation(olderness, out_degree)
    return min(1.0, max(0.0, raw))


def age_layering_stratification_proxy(cset: CausalSet, layer_count: int = 4) -> float:
    """Estimate age-layer stratification from direct-edge layer channels.

    Formula:
    1. layer(i) = floor(i * layer_count / N) clipped to [0, layer_count-1]
    2. Count direct edges by (layer(source), layer(target)).
    3. Let p_k be normalized counts over non-empty channels.
    4. H = -sum_k p_k log(p_k), H_max = log(K), K=number of active channels.
    5. proxy = 1 - H/H_max (or 1 when K<=1).
    """

    if layer_count < 2:
        raise ValueError("layer_count must be >= 2")

    elements = sorted(cset.elements)
    n = len(elements)
    if n < 2:
        return 0.0

    def _layer(idx: int) -> int:
        raw = int((idx * layer_count) / n)
        return min(layer_count - 1, max(0, raw))

    counts: dict[tuple[int, int], int] = {}
    for src, futures in cset.direct_relations.items():
        src_layer = _layer(src)
        for dst in futures:
            key = (src_layer, _layer(dst))
            counts[key] = counts.get(key, 0) + 1

    total = sum(counts.values())
    if total <= 0:
        return 0.0

    probs = [count / total for count in counts.values()]
    if len(probs) <= 1:
        return 1.0

    entropy = -sum(p * math.log(p) for p in probs if p > 0.0)
    max_entropy = math.log(len(probs))
    if max_entropy <= 0.0:
        return 1.0
    return min(1.0, max(0.0, 1.0 - (entropy / max_entropy)))


def compute_artifact_proxies(cset: CausalSet) -> ArtifactProxyValues:
    return ArtifactProxyValues(
        birth_order_dominance=birth_order_dominance_proxy(cset),
        age_layering_stratification=age_layering_stratification_proxy(cset),
    )
