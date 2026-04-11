# causal-set-engine (post-Stage-5 architecture, with Stage-6 typed config)

This package now has a clear **engine vs research-study** boundary:

- the **engine** provides reusable, dynamics-family-agnostic primitives,
- the **experiments** package contains phase-specific reference studies built on those primitives.

The current codebase reflects completed refactor stages 1–6; stage 7 is this documentation hardening pass.

## Architecture map

```text
src/causal_set_engine/
  core/           # CausalSet structure and invariants
  generators/     # Concrete causal-set constructors (Minkowski, nulls, minimal growth)
  diagnostics/    # Generic diagnostics + artifact proxies
  evaluation/     # Metric rows, batch sampling, and scoring/comparison math
  policies/       # Explicit decision policies (phase-2 gate)
  experiments/    # Reference studies / orchestration entrypoints
  config/         # Typed run config dataclasses + lightweight loaders
```

## Research vs engine boundary

| Layer | Classification | Role | Notes |
|---|---|---|---|
| `core` | Engine | `CausalSet` representation, transitive closure/reduction helpers, invariants. | No phase-specific logic. |
| `generators` | Engine | Minkowski sprinklings, null baselines, and constrained primitive growth generators. | Produces `CausalSet`; does not score itself. |
| `diagnostics` | Engine | Structural diagnostics and artifact proxies. | Reused by multiple studies. |
| `evaluation` | Engine | Metric extraction (`run_once`), seed/size sweeps, comparative scoring math. | Former stage-1/2 consolidation target. |
| `policies` | Engine | Threshold-driven gate policy (`phase2_gate`). | Explicit, deterministic, audit-friendly. |
| `experiments` | Research/reference | Study assembly, CLI reporting, phase-specific interpretation. | Reference studies built on engine APIs. |
| `config` | Engine | Typed dataclasses and simple config-file mapping for run setup. | Added in Stage 6. |

## Current scope and non-goals

Current scope remains conservative:

- calibration and controlled comparisons for Minkowski vs nulls,
- narrow, explicit primitive-growth probes under phase-2 gates,
- no scientific-claim expansion and no broad API redesign.

Non-goals for this cycle:

- adding new dynamics families,
- adding heavy framework/dependency layers,
- starting a new architecture audit before the post-Stage-7 snapshot.

## Setup and testing

From `causal-set-engine/`:

```bash
python -m pip install -e .
pytest -q
```

## CLI usage (unchanged defaults; optional `--config`)

All existing flags continue to work as before. Entry points now also accept optional `--config` (JSON/TOML/YAML) where provided values are used unless overridden by explicit CLI flags.

### Phase-1 demo

```bash
causal-set-demo --n 50 --seed 7 --interval-samples 30
causal-set-demo --config configs/phase1_demo.yaml
```

### Phase-1.75 batch calibration + ranking

```bash
causal-set-batch --dimension 3 --n-values 60,80,100 --runs 8 --seed-start 100 --null-p 0.2 --null-edge-density 0.2 --interval-samples 50
```

### Phase-2a probe

```bash
causal-set-phase2a-probe --n-values 60,80 --runs 8 --seed-start 100 --growth-link-probability 0.2
```

### Phase-2c controlled age-bias scan

```bash
causal-set-phase2c-scan --n-values 60,80 --runs 8 --seed-start 100 --link-density-grid 0.16,0.22,0.28 --bias-strength-grid 0.0,0.5,1.0
```

## Policy and interpretation notes

- `policies/phase2_gate.py` defines fixed phase-2 GO/NO-GO thresholds.
- Phase modules in `experiments/` are **reference studies**, not generic engine APIs.
- Outputs remain calibration evidence for configured batches, not proofs of physical dynamics.
