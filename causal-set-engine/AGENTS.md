# Agent Instructions for `causal-set-engine`

## Scope policy

Treat this package as a function-centric engine with explicit engine/research boundaries.

- Treat `core`, `generators`, `diagnostics`, `evaluation`, `policies`, and `config` as reusable engine layers.
- Treat `experiments` as reference-study orchestration on top of engine APIs.
- Use canonical function-centric names in docs and user-facing text (diagnostic demo, batch calibration, growth family probe, artifact-aware scan, policy gate).

## Hard constraints

- Preserve behavior unless the task explicitly asks for behavior changes.
- Preserve existing canonical CLI contracts and defaults; additive flags are preferred over breaking changes.
- Do **not** add new dynamics families unless explicitly requested.
- Do **not** expand scientific scope or claims during architecture/refactor tasks.
- Keep implementations explicit, testable, and lightweight (plain Python + dataclasses/functions).
- Any new functionality must include or update automated tests.

## Current priorities

1. Keep engine modules function-centric and reusable.
2. Keep research interpretation inside `experiments/` and docs.
3. Continue reducing cross-layer coupling.
4. Maintain auditability: deterministic defaults, explicit thresholds, transparent metric math.
5. Keep architecture docs aligned with the current codebase and boundaries.
