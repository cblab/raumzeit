# causal-set-engine

`causal-set-engine` provides a compact, function-centric causal-set calibration engine with a clear boundary between reusable engine layers and study orchestration.

## Current architecture

```text
src/causal_set_engine/
  core/           # causal-set structure and invariants
  generators/     # Minkowski, null, and growth-family constructors
  diagnostics/    # reusable diagnostics and artifact proxy computations
  evaluation/     # metrics, sampling helpers, and scoring math
  policies/       # explicit GO/NO-GO decision policy
  experiments/    # study orchestration built on engine APIs
  config/         # typed run configs and config-file loaders
```

## Canonical CLI commands

```bash
causal-set-diagnostic-demo --n 50 --seed 7 --interval-samples 30
causal-set-diagnostic-demo --config configs/diagnostic_demo.yaml

causal-set-batch-calibration --dimension 3 --n-values 60,80,100 --runs 8 --seed-start 100 --null-p 0.2 --null-edge-density 0.2 --interval-samples 50

causal-set-growth-family-probe --n-values 60,80 --runs 8 --seed-start 100 --growth-link-probability 0.2

causal-set-artifact-aware-scan --n-values 60,80 --runs 8 --seed-start 100 --link-density-grid 0.16,0.22,0.28 --bias-strength-grid 0.0,0.5,1.0
```

## Functional boundaries

- Engine modules (`core`, `generators`, `diagnostics`, `evaluation`, `policies`, `config`) are reusable and function-centric.
- `experiments` modules assemble concrete study flows, invoke policy decisions, and return auditable result structures.
- Policy thresholds are explicit in `policies/policy_gate.py`; scoring and metric math are centralized in `evaluation/`.
