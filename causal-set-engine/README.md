# causal-set-engine

`causal-set-engine` provides a compact, function-centric causal-set calibration engine with a clear boundary between reusable engine layers and study orchestration.

## Current architecture

```text
src/causal_set_engine/
  core/           # causal-set structure and invariants
  generators/     # Minkowski, null, and growth-family constructors
  diagnostics/    # reusable diagnostics and artifact proxy computations
  observables/    # CST-specific research observables layered above diagnostics
  evaluation/     # metrics, sampling helpers, and scoring math
  policies/       # explicit GO/NO-GO decision policy
  experiments/    # study orchestration built on engine APIs
  config/         # typed run configs and config-file loaders
```

## Canonical researcher CLI

The canonical researcher-facing interface is a single root command with workflow subcommands:

```bash
causal-set run --n 50 --seed 7 --interval-samples 30
causal-set run --config configs/diagnostic_demo.yaml

causal-set calibrate --dimension 3 --n-values 60,80,100 --runs 8 --seed-start 100 --null-p 0.2 --null-edge-density 0.2 --interval-samples 50

causal-set evaluate-growth --n-values 60,80 --runs 8 --seed-start 100 --growth-link-probability 0.2

causal-set scan-artifacts --n-values 60,80 --runs 8 --seed-start 100 --link-density-grid 0.16,0.22,0.28 --bias-strength-grid 0.0,0.5,1.0
```

This is the preferred interface for researchers on Linux, macOS, and Windows.

### Cross-platform module fallbacks

If the console script is not available in your shell, use Python module invocation:

```bash
python -m causal_set_engine.cli run --n 50 --seed 7
python -m causal_set_engine.cli calibrate --n-values 60,80 --runs 8
python -m causal_set_engine.cli evaluate-growth --n-values 60,80 --runs 8
python -m causal_set_engine.cli scan-artifacts --n-values 60,80 --runs 8
```

An additional package-level fallback is also supported:

```bash
python -m causal_set_engine run --n 50 --seed 7
```

Legacy separate workflow modules remain available internally for compatibility, but the canonical researcher workflow is `causal-set <subcommand> ...`.

## Functional boundaries

- Engine modules (`core`, `generators`, `diagnostics`, `evaluation`, `policies`, `config`) are reusable and function-centric.
- CST-standard observables live in `observables/cst/` so theory-specific estimators stay distinct from generic engine diagnostics.
- `experiments` modules assemble concrete study flows, invoke policy decisions, and return auditable result structures.
- Policy thresholds are explicit in `policies/policy_gate.py`; scoring and metric math are centralized in `evaluation/`.

## Myrheim-Meyer dimension estimator

`causal_set_engine.observables.cst.myrheim_meyer` adds a transparent Myrheim-Meyer dimension estimator based on ordering fraction:

- ordering fraction: `r = R / (N (N-1))`, where `R` is the number of ordered comparable pairs `x ≺ y`,
- continuum model used for inversion:
  `C(d) = Gamma(d + 1) * Gamma(d / 2) / (4 * Gamma(3 d / 2))`,
- estimator: deterministic bisection solve of `C(d) = r` on a fixed bracket.

This differs from `diagnostics.basic.estimate_dimension_chain_height`, which is a coarse chain-growth scaling proxy (`log N / log L`) used for lightweight calibration. Myrheim-Meyer is a CST-standard observable tied directly to pair-ordering statistics, but still remains a finite-size/region-sensitive estimator.

### Limitations

- The estimator is calibrated to Alexandrov-interval-style Minkowski sprinklings; non-interval regions can shift recovered dimensions.
- Small `N` can produce high variance.
- Returned values are clipped to the configured bracket when ordering fractions fall outside model range.
