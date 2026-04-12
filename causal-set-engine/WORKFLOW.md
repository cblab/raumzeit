# causal-set-engine Researcher Workflow (Practical Guide)

This guide is a **do-this-next** workflow for new users.

It is intentionally operational:
- exact commands,
- what outputs to inspect,
- warning signs,
- when to continue vs stop and debug.

---

## 0) Before you start (one-time setup)

From the `causal-set-engine/` directory:

```bash
python -m pip install -e .
```

Quick sanity check:

```bash
causal-set --help
```

If that prints the subcommands, your canonical researcher CLI is ready.

If `causal-set` is not found, use module fallback:

```bash
python -m causal_set_engine.cli --help
```

If that works, run all commands below as:

```bash
python -m causal_set_engine.cli <subcommand> ...
```

---

## 1) Quick start (first meaningful run)

Run the diagnostic demo first:

```bash
causal-set run --n 50 --seed 7 --interval-samples 30
```

What success looks like:
- JSON output appears (not a traceback).
- It includes keys like:
  - `num_elements`
  - `num_comparable_pairs`
  - `relation_density`
  - `longest_chain_length`
  - `estimated_dimension_chain_height`
  - `estimated_dimension_myrheim_meyer`
  - `interval_statistics`

Good enough to continue:
- command completes,
- output is structured JSON,
- values are finite numbers.

Stop and debug now if:
- command crashes,
- output is empty,
- `interval_statistics` looks missing or malformed.

---

## 2) Canonical researcher workflow (recommended order)

Use this order:

1. `causal-set run`
2. `causal-set calibrate`
3. `causal-set evaluate-myrheim`
4. `causal-set evaluate-intervals`
5. `causal-set evaluate-midpoint`
6. `causal-set evaluate-layers`

Why this order:
- You first verify that the engine runs.
- Then calibrate reference vs null behavior at small scale.
- Then validate core observables one by one before using richer structure metrics.

---

## 3) Worked example (Minkowski reference vs null baselines)

This example is small enough for beginners but still meaningful.

### Step 1 — Smoke test the engine

```bash
causal-set run --n 60 --seed 11 --interval-samples 30
```

Inspect:
- JSON is valid.
- `estimated_dimension_myrheim_meyer` is present.
- `interval_statistics` exists.

Continue if:
- no crash,
- no obviously broken fields.

Stop if:
- missing fields or NaNs.

---

### Step 2 — Calibrate against null models

```bash
causal-set calibrate \
  --dimension 3 \
  --n-values 40,60,80 \
  --runs 6 \
  --seed-start 100 \
  --null-p 0.2 \
  --null-edge-density 0.2 \
  --interval-samples 40
```

Inspect:
- `model ...` table for `minkowski3d`, `random-poset`, `fixed-edge-poset`.
- `conservative discriminator ranking` section.
- `combined manifold-likeness score` section.

Promising behavior:
- Minkowski rows are consistently distinct from both null rows across multiple `N`.
- ranking has non-trivial usefulness scores (not all near zero).
- combined worst-case effect is not collapsing to ~0.

Warning signs:
- very large overlap across models for most metrics,
- unstable signs across `N`,
- combined score does not improve worst-case separation.

Do not proceed yet if:
- model separation is weak/noisy across all tested `N`.

What to do if weak:
- increase `--runs` (e.g., 6 -> 10),
- increase `--n-values` upward (e.g., add `100`),
- keep seeds deterministic (`--seed-start`) for reproducibility.

---

### Step 3 — Validate Myrheim-Meyer behavior

```bash
causal-set evaluate-myrheim \
  --dimensions 2,3,4 \
  --n-values 40,80 \
  --runs 6 \
  --seed-start 100 \
  --null-p 0.2 \
  --null-edge-density 0.2
```

Inspect:
- `per-dimension summaries` table,
- `myrheim-meyer N-trend by dimension`,
- `separation vs null models`,
- `compact conclusions` lines (monotone count, conservative min effect).

Promising behavior:
- some monotone ordering signal across dimensions,
- conservative min |effect| vs nulls is clearly non-zero,
- noise is not dominating every cell.

Warning signs:
- monotone count near zero,
- effect sizes near zero across most rows,
- stdev so large that means are not informative.

Do not proceed yet if:
- Myrheim-Meyer does not show reliable separation at all.

What to do:
- increase `--runs`,
- test slightly larger `N` values,
- re-check calibration assumptions before interpreting deeper observables.

---

### Step 4 — Check global interval statistics

```bash
causal-set evaluate-intervals \
  --dimensions 2,3,4 \
  --n-values 40,80 \
  --runs 6 \
  --seed-start 100 \
  --k-max 5 \
  --null-p 0.2 \
  --null-edge-density 0.2
```

Inspect:
- `interval abundance summary by model`,
- `link-focused view (N0 intervals where k=0)`.

Promising behavior:
- interval densities differ between Minkowski references and nulls in a repeatable way,
- link-focused summaries are not identical across all models.

Warning signs:
- nearly identical density summaries across all models,
- strong run-to-run instability (large sd vs mean).

Do not proceed yet if:
- interval summaries are too unstable to distinguish anything.

What to do:
- increase `--runs`,
- increase `N`,
- keep `k-max` modest first (e.g., 4–6) to avoid over-reading sparse high-k bins.

---

### Step 5 — Check midpoint scaling sensor

```bash
causal-set evaluate-midpoint \
  --dimensions 2,3,4 \
  --n-values 40,80 \
  --runs 6 \
  --seed-start 100 \
  --min-interval-size 8 \
  --max-sampled-intervals 48 \
  --null-p 0.2 \
  --null-edge-density 0.2
```

Inspect:
- `per-model summaries` columns:
  - `midpoint_d(mean±sd)`
  - `sampled/qualifying(mean)`
  - `under_sampled`
- `separation vs null models` (midpoint vs myrheim vs chain).
- compact conclusions for conservative min effects.

Promising behavior:
- midpoint-based separation is comparable to other sensors,
- under-sampled count is low,
- sampled/qualifying is reasonable for requested sample budget.

Warning signs:
- many under-sampled runs,
- midpoint effect sizes collapse while others remain strong,
- high noise with tiny qualifying intervals.

Do not proceed yet if:
- under-sampling is widespread.

What to do:
- lower `--min-interval-size` slightly (if too strict),
- or increase `N`,
- or reduce requested max samples to realistic levels for available qualifying intervals.

---

### Step 6 — Check interval layer profiles

```bash
causal-set evaluate-layers \
  --dimensions 2,3,4 \
  --n-values 40,80 \
  --runs 6 \
  --seed-start 100 \
  --min-interval-size 8 \
  --max-sampled-intervals 48 \
  --null-p 0.2 \
  --null-edge-density 0.2
```

Inspect:
- `per-model summaries` columns for:
  - `occ_layers(mean±sd)`
  - `boundary_frac(mean±sd)`
  - `peak_idx(mean±sd)`
  - `sampled/qualifying` and `under`
- `separation vs null models` (layer metrics plus midpoint/myrheim).
- compact conclusions comparing conservative min effects.

Promising behavior:
- at least some layer-profile metrics show robust separation vs nulls,
- conclusions are consistent with midpoint/myrheim, not contradictory noise.

Warning signs:
- layer metrics are all weak while under-sampling is high,
- apparent effects rely on one metric only and vanish in others.

Do not proceed yet if:
- layer metrics are unstable and unsupported by other sensors.

What to do:
- improve sampling quality (runs, N, interval constraints),
- then rerun from midpoint and layers together.

---

## 4) What to inspect after each step (fast checklist)

- `run`:
  - matters: valid JSON and core fields.
  - stable: finite metrics, no missing keys.
  - warning: malformed output / crashes.

- `calibrate`:
  - matters: model table, ranking, combined score.
  - stable: repeatable Minkowski-vs-null differences across N.
  - warning: overlap everywhere, mixed signs, near-zero worst-case effect.

- `evaluate-myrheim`:
  - matters: monotone ordering count, null separation effects, stdev.
  - stable: non-zero conservative separation + manageable variance.
  - warning: near-zero effects or extreme noise.

- `evaluate-intervals`:
  - matters: k-bin counts/densities and link-focused `k=0` behavior.
  - stable: consistent model differences across N.
  - warning: identical distributions or very noisy bins.

- `evaluate-midpoint`:
  - matters: midpoint effect sizes + under-sampling columns.
  - stable: low under-sampling, reasonable separation.
  - warning: many under-sampled runs, collapsed midpoint signal.

- `evaluate-layers`:
  - matters: occupied layers, boundary fraction, peak index, under-sampling.
  - stable: multi-metric support, not single-metric luck.
  - warning: weak/contradictory layer behavior with high noise.

---

## 5) Troubleshooting and decision guidance

If results are too noisy:
- increase `--runs` first,
- then increase `N`.

If interval workflows are under-sampled:
- reduce `--min-interval-size` slightly,
- reduce `--max-sampled-intervals` to realistic values,
- or move to larger `N`.

If reference/null separation is weak:
- do **not** over-interpret.
- rerun with stronger sampling (more runs, larger N) before claiming anything.

If one sensor disagrees with all others:
- treat that sensor as unstable for this regime,
- debug data quality and sampling before moving on.

When to go back and debug instead of proceeding:
- repeated crashes or malformed outputs,
- persistent under-sampling in midpoint/layer workflows,
- near-zero separation across all reference-vs-null comparisons.

---

## 6) Research discipline (non-negotiable rules)

1. **Do not trust a single metric alone.**
2. **Always compare against null baselines.**
3. **Do not make theory claims from one workflow output.**
4. **Validate sensors (stability + separation) before using them to judge dynamics.**
5. **Keep runs reproducible** (record seeds, parameters, and CLI command lines).

---

## 7) Main workflow in one numbered checklist

1. Run `causal-set run` to verify the engine and output format.
2. Run `causal-set calibrate` to establish baseline reference-vs-null separation.
3. Run `causal-set evaluate-myrheim` to validate global dimensional signal.
4. Run `causal-set evaluate-intervals` to check global interval structure.
5. Run `causal-set evaluate-midpoint` and verify under-sampling is controlled.
6. Run `causal-set evaluate-layers` and look for multi-metric support.
7. If any step fails stability/separation checks, pause and debug before continuing.

---

## 8) Most important “do not do this” warnings

- Do **not** publish conclusions from one command or one metric.
- Do **not** ignore null baselines.
- Do **not** proceed when under-sampling warnings are common.
- Do **not** treat noisy, overlapping outputs as evidence of strong structure.
- Do **not** change many parameters at once when debugging (change one knob, rerun, compare).
