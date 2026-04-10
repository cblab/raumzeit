# emergent-geometry-causal-graphs

A compact research scaffold for stochastic graph growth experiments with per-step structural diagnostics.

The current simulation slice is now runnable end-to-end:
- single-run execution from YAML config,
- deterministic batch execution over model configs and seeds,
- raw JSON result capture,
- summary statistics aggregation,
- baseline K1 figure generation,
- optional K2 global observables (sampled-region spectral/volume-growth diagnostics),
- optional K7 fixed-anchor diagnostics for separating sampling heterogeneity from genuine temporal drift.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run a single simulation

```bash
python scripts/run_single.py --config configs/baseline.yaml
```

Save full JSON output:

```bash
python scripts/run_single.py \
  --config configs/baseline.yaml \
  --seed 123 \
  --output results/raw/baseline/seed_123.json
```

## Enable K2 global diagnostics

K2 is sampled from a BFS-defined shadow region and written under
`observables_k2_global` in each raw run payload.

Set these fields in the corresponding model YAML under `configs/`, for example `configs/baseline.yaml`:

```yaml
k2_global_every: 10
k2_region_size: 256
k2_taus: [1, 2, 4, 8, 16]
k2_walkers: 256
```

- `k2_global_every <= 0` disables K2 collection.
- Measurements are appended at step `0` and every `k2_global_every` steps thereafter.


## Enable K7 fixed-anchor diagnostics

K7 keeps anchor seeds fixed across time and measures local geometry in seed-centered
BFS regions, helping separate sampling heterogeneity from genuine temporal drift.
Records are stored under `observables_k7` in each raw run payload.

Set these fields in the corresponding model YAML under `configs/`, for example `configs/baseline.yaml`:

```yaml
k7_every: 20
fine_start: 80
fine_end: 140
fine_every: 5
num_anchors: 6
anchor_region_size: 128
anchor_min_region: 24
k6_taus: [1, 2, 4, 8, 16]
k6_walkers: 256
k6_min_start_nodes: 2
k6_core_frac: 0.25
k6_mid_frac: 0.50
k6_front_frac: 0.25
```

- `k7_every <= 0` disables K7 collection.
- K7 anchors are initialized once after graph initialization and reused for all steps.
- Measurements run on the standard cadence (`k7_every`) with optional finer cadence in
  `[fine_start, fine_end]` using `fine_every`.

## Run a paper-style batch

```bash
python scripts/run_batch.py --config configs/paper_batch.yaml
```

This runs each listed model config for each listed seed and stores raw outputs at:

- `results/raw/{model_name}/seed_{seed}.json`
- `results/manifests/batch_manifest.json`

## Summarize results

```bash
python scripts/summarize_results.py
```

Summaries are written to:

- `results/summary/{model_name}_summary.json`

Each summary includes:
- mean final K1
- std final K1
- mean final number of nodes
- mean final active edge count
- number of runs
- K2 coverage fields (`k2_run_count`, `k2_missing_run_count`)
- K2 aggregate fields when available (`mean_final_k2_ds`, `mean_final_k2_dv`)
- K7 aggregate fields when available (`run_count_with_k7`, `mean_last_k7_ds_global`, `mean_last_k7_dv_global`, `mean_last_k7_g_fc`, `mean_num_k7_records`, and optional `mean_last_k7_iso`)

## Make figures

```bash
python scripts/make_figures.py
```

This always creates:

- `figures/fig1_baseline_k1.png`

and creates K2/K7 figures when corresponding observables exist in the raw payloads:

- `figures/fig2_baseline_k2_ds.png`
- `figures/fig3_baseline_k2_dv.png`
- `figures/fig3_baseline_k7.png`
- optionally `figures/fig3b_baseline_k7_iso.png`

based on baseline seeds under `results/raw/baseline/`.

## Config notes

`run_single.py --config configs/baseline.yaml` reads that YAML file directly, and batch execution reads the listed model YAML files from `configs/`.

Model configs are YAML files loaded through `src/config.py`.

A config can inherit from another config using:

```yaml
inherits: baseline.yaml
```

Inheritance is deterministic and deep-merges dictionaries with child values overriding parent values.
