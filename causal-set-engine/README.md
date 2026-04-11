# causal-set-engine (post-Stage-7 architecture)

This package maintains a clear **engine vs research-study** boundary:

- the **engine** provides reusable, dynamics-family-agnostic primitives,
- the **experiments** package contains reference-study orchestration built on those primitives.

## Architecture map

```text
src/causal_set_engine/
  core/           # CausalSet structure and invariants
  generators/     # Concrete causal-set constructors (Minkowski, nulls, minimal growth)
  diagnostics/    # Generic diagnostics + artifact proxies
  evaluation/     # Metric rows, batch sampling, and scoring/comparison math
  policies/       # Explicit policy gate logic
  experiments/    # Reference studies / orchestration entrypoints
  config/         # Typed run config dataclasses + lightweight loaders
```

## CLI usage (canonical names)

```bash
causal-set-diagnostic-demo --n 50 --seed 7 --interval-samples 30
causal-set-diagnostic-demo --config configs/diagnostic_demo.yaml

causal-set-batch-calibration --dimension 3 --n-values 60,80,100 --runs 8 --seed-start 100 --null-p 0.2 --null-edge-density 0.2 --interval-samples 50

causal-set-growth-family-probe --n-values 60,80 --runs 8 --seed-start 100 --growth-link-probability 0.2

causal-set-artifact-aware-scan --n-values 60,80 --runs 8 --seed-start 100 --link-density-grid 0.16,0.22,0.28 --bias-strength-grid 0.0,0.5,1.0
```

## Legacy compatibility names

Legacy phase-centric paths still work and are now compatibility aliases:

- CLI aliases: `causal-set-demo`, `causal-set-batch`, `causal-set-phase2a-probe`, `causal-set-phase2c-scan`
- Module aliases:
  - `experiments.phase2a_probe` -> `experiments.growth_family_probe`
  - `experiments.phase2c_scan` -> `experiments.artifact_aware_scan`
  - `policies.phase2_gate` -> `policies.policy_gate`
- Config filename alias: `configs/phase1_demo.yaml` -> `configs/diagnostic_demo.yaml`

## Policy and interpretation notes

- `policies/policy_gate.py` defines fixed GO/NO-GO thresholds.
- Experiment modules in `experiments/` are **reference studies**, not generic engine APIs.
- Outputs remain calibration evidence for configured batches, not proofs of physical dynamics.
