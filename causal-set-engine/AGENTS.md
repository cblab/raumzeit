# Agent Instructions for `causal-set-engine`

## Scope policy

This package is limited to **phase-1 calibration architecture**.

## Hard constraints

- Keep phase 1 narrow and testable.
- Do **not** add custom growth dynamics until phase-1 calibration is validated.
- Any new functionality must include or update automated tests.
- Prefer small, explicit, pure-Python implementations.
- Avoid adding external dependencies unless clearly justified.
