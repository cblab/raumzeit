# emergent-geometry-causal-graphs

A compact research scaffold for stochastic graph growth experiments with per-step structural diagnostics.

The current simulation slice is now runnable end-to-end:
- single-run execution from YAML config,
- deterministic batch execution over model configs and seeds,
- raw JSON result capture,
- summary statistics aggregation,
- baseline K1 figure generation,
- optional K2 global observables (sampled-region spectral/volume-growth diagnostics).

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

Set these fields in your config:

```yaml
k2_global_every: 10
k2_region_size: 256
k2_taus: [1, 2, 4, 8, 16]
k2_walkers: 256
```

- `k2_global_every <= 0` disables K2 collection.
- Measurements are appended at step `0` and every `k2_global_every` steps thereafter.

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

## Make figures

```bash
python scripts/make_figures.py
```

This always creates:

- `figures/fig1_baseline_k1.png`

and creates K2 figures when corresponding observables exist in the raw payloads:

- `figures/fig2_baseline_k2_ds.png`
- `figures/fig3_baseline_k2_dv.png`

based on baseline seeds under `results/raw/baseline/`.

## Config notes

Model configs are YAML files loaded through `src/config.py`.

A config can inherit from another config using:

```yaml
inherits: baseline.yaml
```

Inheritance is deterministic and deep-merges dictionaries with child values overriding parent values.
