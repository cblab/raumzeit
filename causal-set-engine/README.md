# causal-set-engine (Phase 1 → 1.75)

This folder contains a **minimal Python package scaffold** for phase-1 calibration and phase-1.5 robustness testing of causal set tooling.

## Phase-1.75 goal

Keep the architecture conservative, testable, and dynamics-free while improving calibration robustness for:

- 2D, 3D, and 4D Minkowski sprinklings (all with explicit bounded regions and c=1),
- multiple null baselines,
- seed and size sweeps via batch experiments,
- compact, auditable diagnostics summaries.

## Hard non-goals (still explicit)

Phase 1.75 intentionally does **not** include:

- custom causal-set growth dynamics,
- curvature/gravity layers,
- speculative theory claims,
- heavy plotting stacks,
- performance-oriented rewrites.

## Local development workflow

From `causal-set-engine/`:

```bash
python -m pip install -e .
```

## Run tests

```bash
pytest -q
```

## Run demos

Single-run phase-1 demo (2D Minkowski):

```bash
causal-set-demo --n 50 --seed 7 --interval-samples 30
# equivalent:
python -m causal_set_engine.experiments.run_phase1_demo --n 50 --seed 7 --interval-samples 30
python -m causal_set_engine --n 50 --seed 7 --interval-samples 30
```

Batch phase-1.75 robustness comparison (including size sweep and conservative ranking):

```bash
causal-set-batch --dimension 3 --n-values 60,80,100 --runs 8 --seed-start 100 --null-p 0.2 --null-edge-density 0.2 --interval-samples 50
# equivalent:
python -m causal_set_engine.experiments.run_phase1_batch --dimension 4 --n 100 --runs 12 --seed-start 300 --null-p 0.2 --null-edge-density 0.25 --interval-samples 60
```

## Null models used in phase-1.5

1. `random-poset` (forward Bernoulli DAG)
   - Preserves: element count, acyclicity (by index ordering), expected edge density.
   - Destroys: Lorentzian lightcone structure, manifold-like interval geometry.

2. `fixed-edge-poset` (forward DAG with exact sampled edge count)
   - Preserves: element count, acyclicity, exact direct-edge count.
   - Destroys: Lorentzian lightcone structure, manifold-like interval geometry, coordinate interpretation.

## Diagnostics and explicit limitations

- `estimate_dimension_chain_height`
  - Useful as a coarse discriminator only.
  - Limitation: depends strongly on finite-size effects and longest-chain noise; not a precision dimension estimator.

- `longest_chain_length`
  - Useful for rough growth-scaling differences.
  - Limitation: can overlap across models for small `N` or poorly chosen null density.

- `sampled_interval_statistics`
  - Useful for comparing interval-size distributions compactly.
  - Limitation: sample-count dependent; different pair-sampling choices can change conclusions.

Phase-1.75 adds explicit conservative decision metrics (effect size, overlap proxy, sign consistency, size-trend consistency) plus a transparent linear combined score.

All phase-1.75 outputs remain empirical for the chosen batch settings and fixed heuristics; they are calibration evidence, not proofs of manifold-likeness.
