# Agent Instructions for `causal-set-engine`

## Scope policy

This package is in a **post-Stage-7 refactor state** with explicit engine/research boundaries and function-centric naming.

- Treat `core`, `generators`, `diagnostics`, `evaluation`, `policies`, and `config` as reusable engine layers.
- Treat `experiments` as reference-study orchestration on top of engine APIs.
- Prefer canonical function-centric names in docs and user-facing text (diagnostic demo, batch calibration, growth family probe, artifact-aware scan, policy gate).
- Keep legacy phase-centric module/CLI names only as compatibility aliases.

## Hard constraints

- Preserve behavior unless the task explicitly asks for behavior changes.
- Preserve existing CLI contracts and defaults; additive flags are preferred over breaking changes.
- Do **not** add new dynamics families unless explicitly requested.
- Do **not** expand scientific scope or claims during architecture/refactor tasks.
- Keep implementations explicit, testable, and lightweight (plain Python + dataclasses/functions).
- Any new functionality must include or update automated tests.

## Current priorities

1. Keep engine modules phase-agnostic and reusable.
2. Keep research interpretation inside `experiments/` and docs.
3. Continue reducing cross-layer coupling.
4. Maintain auditability: deterministic defaults, explicit thresholds, transparent metric math.
5. Keep refactor-plan docs accurate until the next fresh architecture audit is run.
