# Local Causal Edge Dynamics Fail to Stabilize Robust Macroscopic Geometry: A Canonical 3-Model Falsification Study

## Abstract
We test a narrow hypothesis: whether a specific class of local, causal, edge-based update rules on growing directed graphs can stabilize robust macroscopic geometry. The contribution is not a claim of emergent spacetime. The contribution is a maintained modular engine, a canonical three-model ablation (`baseline_ref`, `v8a_fast`, `v9a_fast`), a reproducible diagnostics stack (K1, K2, K4, K5, K7), and a disciplined negative result.

Geometry is measured rather than assumed. The workflow is fixed to config → batch → raw outputs → summary tables → figures → commit hash. In the current repository state, available canonical summaries provide direct quantitative support for `baseline_ref`/`baseline` and `v8a_fast` on final K1, active-edge count, and final node count, while the designated `reference_table.json`/`.csv` artifacts and canonical `v9a_fast` summary outputs are not present. Accordingly, the negative conclusion is bounded: the available evidence shows no robust macroscopic isotropic stabilization, and `v8a_fast` shifts local structural statistics without establishing a new asymptotic geometry class. `v9a_fast` remains part of canonical scope, but in this checkout its evaluation is evidence-limited rather than numerically resolved.

## 1. Introduction
This paper asks one focused question: **can this specific local causal mechanism class stabilize robust macroscopic geometry, as measured from graph dynamics alone?**

The study is falsification-driven. We do not assume an ambient manifold, target metric, or pre-imposed geometric law. We evaluate whether geometry-like behavior appears and remains stable under growth. If it does not, we report the boundary of the mechanism rather than reinterpret failure as success.

Accordingly, geometry is operationalized through diagnostics: diffusion scaling, volume growth scaling, concentration/efficiency/path structure, shell/front organization, and fixed-anchor isotropy and transport splits. These observables are designed to discriminate local structural improvements from true macroscopic geometric stabilization.

## 2. Canonical scope and implementation status
The maintained operational truth is the modular engine in:

- `emergent-geometry-causal-graphs/src/`
- canonical configs in `emergent-geometry-causal-graphs/configs/`
- canonical scripts in `emergent-geometry-causal-graphs/scripts/`

The **canonical scientific scope** of this manuscript is exactly:

- `baseline_ref` (`configs/baseline_ref.yaml`)
- `v8a_fast` (`configs/v8a_fast.yaml`)
- `v9a_fast` (`configs/v9a_fast.yaml`)

Canonical batch definition:

- `configs/paper_batch_ref.yaml`

Archival monolith status:

- `archive/reference-monolith/` is provenance only and not operational truth.

Historical variants (e.g., V7/V7.1) are non-canonical and are not part of the main proof path.

## 3. Model
### 3.1 Growth process
At step $t$, the system is a growing directed weighted graph $G_t=(V_t,E_t)$ with binary node states $s_j\in\{0,1\}$. A new node is added each step (until `max_nodes`), chooses parents from existing nodes, and receives initial incoming edges.

### 3.2 Parent selection
For candidate parent $i$, the base score is

$$
S_i^{\mathrm{base}}=\exp\big(\alpha L_i + \beta C_i + \gamma N_i\big),
$$

with local density score

$$
L_i = \frac{1}{1+\lvert k_i^{\text{out}}-\rho^*(|V_t|-1)\rvert},
$$

and novelty

$$
N_i = \frac{1}{1+k_i^{\text{out}}}.
$$

Parents are selected sequentially with genealogical repulsion using ancestry-signature Jaccard overlap

$$
J(i,\ell)=\frac{|A(i)\cap A(\ell)|}{|A(i)\cup A(\ell)|},
$$

and effective score

$$
S_i = S_i^{\mathrm{base}}\prod_{\ell\in P} \max(\varepsilon_r, 1-\lambda_r J(i,\ell)).
$$

### 3.3 State relaxation
Node states relax from weighted incoming influence:

$$
\bar s_j = \frac{\sum_{(i\to j)\in E_t^{\mathrm{act}}} w_{ij}s_i}{\sum_{(i\to j)\in E_t^{\mathrm{act}}} w_{ij}},\qquad
s_j=\mathbf 1[\bar s_j\ge 1/2].
$$

### 3.4 Baseline edge-update skeleton
For active edge $e=(i\to j)$, the update can be written as

$$
\begin{aligned}
w_e(t+1)=w_e(t)
&+\Delta_e^{\mathrm{coh}}
+\Delta_e^{\mathrm{cross}}
-\nu R_e
-\Gamma_e^{\mathrm{inh}}
-\Gamma_e^{\mathrm{crowd}}
-\Gamma_e^{\mathrm{load}}
-\Gamma_e^{\mathrm{plast}}\\
&-\Gamma_e^{\mathrm{center}}
-\Gamma_e^{\mathrm{excess}}
-\mu\big(w_e-w_0\big),
\end{aligned}
$$

with deactivation when

$$
w_e(t+1) < w_{\min}^{\mathrm{eff}}(j).
$$

The effective pruning threshold is density- and calibration-aware:

$$
w_{\min}^{\mathrm{eff}}(j)
= w_{\min}\big(1+\lambda_p\,p_j\big)\times\big(1+\alpha_{\mathrm{lift}}\,\max(0,\bar w-(w_{\star}+\epsilon_w))\big),
$$

where $p_j=\max(0,(k_j^{\mathrm{in}}-k_{\mathrm{target}})/k_{\mathrm{target}})$ and the second factor is active only when weight calibration is enabled.

### 3.5 Variant-specific terms

- **`baseline_ref`**: disables ball-integrity contrast, weight calibration, and V9 coherence terms.
- **`v8a_fast`**: enables local ball-integrity contrast and weight calibration.
- **`v9a_fast`**: inherits `v8a_fast` and additionally enables mesoscale ball-coherence.

For `v8a_fast`, the additional local ball-integrity term is

$$
\Delta_e^{\mathrm{ball}} = \min\left(c_{\mathrm{ball}},\max\left(-c_{\mathrm{ball}},\alpha_{\mathrm{ball}}\left[\omega_{\triangle}T_{ij}+\omega_{2h}H_{ij}+\omega_{\deg}D_j+\omega_{\mathrm{sh}}S_{ij}\right]\right)\right).
$$

where $T_{ij}$ is triangle support, $H_{ij}$ is two-hop coverage gain, $D_j$ is degree support, and $S_{ij}$ is shared-neighbor overlap.

Weight calibration in `v8a_fast` contributes centering and excess penalties:

$$
\Gamma_e^{\mathrm{center}} \propto \max(0,\bar w - w_{\star})\max(0,w_e - w_{\star}),\qquad
\Gamma_e^{\mathrm{excess}} \propto \max(0,w_e - (w_{\star} + \epsilon_w)).
$$

For `v9a_fast`, mesoscale ball coherence adds

$$
\Delta_e^{\mathrm{v9}} = \min\left(c_{\mathrm{v9}},\max\left(-c_{\mathrm{v9}},\alpha_{\mathrm{v9}}\left[\omega_{r2}N_{r2}+\omega_{r3}N_{r3}+\omega_{\mathrm{sec}}B_{\mathrm{sec}}-\omega_{\mathrm{red}}R_{\mathrm{inner}}+\omega_{\mathrm{front}}F_{\mathrm{thin}}N_{r3}\right]\right)\right).
$$

This term combines novelty at radius 2 and 3, sector balancing, inner redundancy suppression, and thin-front support.

## 4. Diagnostics framework
We use K1, K2, K4, K5, and K7.

- **K1 (structural stabilization):** active-edge count, degree moments, weight statistics, normalized degree entropy.
- **K2 (global diffusion/volume):** return probabilities $P(\tau)$, spectral dimension estimate, volume-growth dimension estimate on sampled BFS shadow regions.
- **K4 (concentration/efficiency/path):** incoming Herfindahl concentration, cluster dominance, sampled global efficiency, sampled path length.
- **K5 (shell/front morphology):** shell entropy, front thickness, peak shell index.
- **K7 (fixed-anchor diagnostics family):** repeated measurements around fixed seeds to separate true temporal drift from region-resampling effects.

### 4.1 K2 definitions
Spectral scaling uses return probabilities across walk horizons:

$$
P(\tau)\sim \tau^{-d_s/2}.
$$

Volume-growth scaling uses BFS-ball growth:

$$
V(r)\sim r^{d_v}.
$$

### 4.2 K7 isotropy concept and naming clarification
K7 includes anchor-local isotropy defect, diffusion splits (core/mid/front), and causal-front proxies. Isotropy defect is estimated from branch-imbalance statistics around sampled centers (coefficient-of-variation style radial imbalance).

**Naming clarification:** K7 is a diagnostics family label. It is not “Version 7.” Historical `v7`/`v71` model names are separate and non-canonical for this manuscript.

## 5. Experimental design and reproducibility
This paper is bound to the modular reproducibility chain:

1. **Config layer:** `baseline_ref`, `v8a_fast`, `v9a_fast` YAMLs.
2. **Batch layer:** `configs/paper_batch_ref.yaml` over fixed seeds.
3. **Raw outputs:** `results/raw/{model}/seed_{seed}.json`.
4. **Summary tables:** `results/summary/reference_table.json` and `.csv`.
5. **Figures:** `scripts/make_reference_figures.py`.
6. **Provenance:** record `git rev-parse HEAD` with results.

Reproducibility procedure is documented in `REPRODUCIBILITY.md`.

## 6. Results
This section stays within the canonical three-model ablation (`baseline_ref`, `v8a_fast`, `v9a_fast`) and is restricted to evidence that is present in this checkout.

### 6.1 `baseline_ref`: reference regime from available summaries
The available summary artifact for the baseline mechanism is `results/summary/baseline_summary.json` (model label `baseline`). Across 6 runs, final K1 is $0.1027\pm0.0218$ (mean±std), with $120.17$ active edges and $39.33$ nodes at the final recorded step. This establishes the reference regime as a sparse adaptive graph with moderate seed variability rather than collapse or explosive densification.

Global diffusion/volume estimates can be extracted from the last K2-global record in available baseline raw runs (`results/raw/baseline/seed_*.json`): $d_s\approx1.99\pm0.26$ and $d_v\approx1.31\pm0.19$ (6/6 runs finite). These values indicate nontrivial diffusion geometry, but by themselves do not establish robust isotropic macroscopic closure; notably, no canonical aggregated K7 isotropy table is available in this checkout.

### 6.2 `v8a_fast`: what changes relative to baseline, and what does not
For `v8a_fast`, the available summary (`results/summary/v8a_fast_summary.json`) reports final K1 $0.1013\pm0.0174$, active edges $105.0$, and nodes $35.2$ over 5 runs. Relative to baseline summary values, the dominant shift is structural sparsification (fewer active edges and fewer retained nodes), while mean K1 remains close.

The last-step K2-global values from available `v8a_fast` raw runs give $d_s\approx1.92\pm0.11$ and $d_v\approx1.18\pm0.14$ (5/5 runs finite), again in a similar diffusion-geometric band to baseline. Taken conservatively, the available evidence supports a local/structural retuning (including reduced variance in K1 and lower final size) rather than a clear asymptotic geometry-class transition.

### 6.3 `v9a_fast`: canonical in scope, unresolved in this checkout
`v9a_fast` remains part of canonical scope by config and batch definition (`configs/v9a_fast.yaml`, `configs/paper_batch_ref.yaml`). However, this checkout does not contain `results/summary/reference_table.json`, `results/summary/reference_table.csv`, a `v9a_fast` summary JSON, `results/raw/v9a_fast/` runs, or canonical comparison figures for the three-model reference set.

Therefore, no quantitative incremental claim over `v8a_fast` is made here. The correct status is evidence-limited: the additional mesoscale-coherence mechanism is specified, but its canonical outcome is not resolved by the currently available artifacts.

### 6.4 Evidence policy in the present repository state
The designated canonical tables are `results/summary/reference_table.json` and `.csv`, but they are absent in this checkout. Reported numbers in this section are therefore taken only from available per-model summaries and raw final/last-step diagnostics. Missing canonical aggregates (especially K7 and full three-model reference tables) are treated as unresolved, not inferred.

## 7. Interpretation
The evidence supports a narrow negative conclusion: this local causal edge-dynamics line can self-organize transport and ball-like local structure but does not robustly stabilize macroscopic isotropic geometry.

A useful description is an **anisotropic diffusion-geometric patch medium**: the system forms persistent, structured, locally coherent transport patches without converging to a globally robust isotropic geometric phase.

## 8. Limitations
- The mechanism class is heuristic and local by construction.
- Simulations are finite in size, horizon, and seed count.
- Canonical scope is intentionally narrow (three models only).
- This is not a universal no-go theorem for emergence of geometry.
- Diagnostics are strong operational proxies, not metaphysical proof.

## 9. Related work
**Causal-set and discrete-causality programs.** Causal-set research studies whether spacetime structure can be recovered from fundamentally discrete causal order, with continuum behavior emerging only in suitable limits (Surya, 2019). This paper overlaps at the level of causal/discrete motivation and the use of graph-like relational data. It differs in objective and claim strength: we do not test a full quantum-gravity reconstruction program, and we do not infer continuum recovery. We test a narrower algorithmic question about one local edge-update lineage in a growing directed graph engine.

**Dynamical graph models of emergent locality.** Quantum Graphity and related dynamical-graph approaches ask when locality and geometry-like phases can emerge from graph dynamics (Konopka, Markopoulou, and Severini, 2008). Our setup is closest to this tradition because locality must be induced by endogenous graph evolution rather than imposed geometry. The key difference is evidential posture: instead of proposing a new positive phase claim, we run a canonical three-model ablation and report a bounded negative result when robust macroscopic isotropic stabilization is not observed.

**Higher-order and simplicial network geometry.** Network Geometry with Flavor and subsequent network-geometry work construct higher-order combinatorial structures (simplicial complexes and related growth rules) to study emergent geometric organization and complexity (Bianconi and Rahmede, 2016; Mulder and Bianconi, 2018). Our models are edge-centric and pairwise, so these papers are better viewed as adjacent alternatives than direct baselines. This comparison clarifies scope: our negative finding concerns a local edge-based mechanism class and does not rule out higher-order generative mechanisms.

**Discrete graph-geometric diagnostics and curvature.** Discrete curvature literature develops operational geometric probes on networks, including comparative studies of curvature discretizations and convergence links between Ollivier curvature on random geometric graphs and manifold Ricci curvature (Samal et al., 2018; van der Hoorn et al., 2023). We align with this diagnostics-first philosophy: geometry is measured via operational statistics rather than assumed. However, our diagnostics stack (K1/K2/K4/K5/K7) is used to falsify stability claims for a specific mechanism lineage, not to assert a universal geometric no-go theorem. Accordingly, this manuscript does **not** refute graph-based or pregeometric emergence programs in general; it provides a reproducible falsification result for one narrower local causal edge-dynamics lineage under the canonical three-model protocol.

## 10. Conclusion
Within the canonical modular engine and canonical three-model scope (`baseline_ref`, `v8a_fast`, `v9a_fast`), the currently available repository evidence is sufficient to reject robust macroscopic isotropic stabilization for the baseline→`v8a_fast` slice, but insufficient to numerically resolve the `v9a_fast` increment in this checkout.

What is supported is reproducible local structural organization and transport retuning in available runs; what is not yet supported here is a complete canonical three-model quantitative closure. Future progress likely requires stronger nonlocal consistency constraints, higher-order relational structure, and a completed canonical evidence bundle (`reference_table.*`, `v9a_fast` raw/summary, and three-model comparison figures).

## 11. Reproducibility note
Authoritative execution path:

```bash
python scripts/run_batch.py --config configs/paper_batch_ref.yaml
python scripts/summarize_results.py
python scripts/make_reference_figures.py
git rev-parse HEAD
```

Use the resulting raw outputs, canonical reference tables, figures, and commit hash as the manuscript provenance bundle.
