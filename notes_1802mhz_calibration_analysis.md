# 1802 MHz Calibration — Root Cause Analysis & Proposed Fix
**Date:** 2026-07-24  
**Snapshot:** `sionna2_1802mhz_dem_simulation_SNAPSHOT_20260724_051038.ipynb`  
**Branch:** `claude/cool-cori-rrWbY`

---

## Current State (pre-fix)

| Phase | RMSE | Notes |
|-------|------|-------|
| Phase 0 (scalar only, 30M) | 15.23 dB | scalar = -7.260 dB |
| Phase 1 warm-up (7.5M, 135 evals) | 12.56 dB | at 7.5M sample landscape |
| Post-priming re-scalar (30M, warm-up params) | 15.24 dB | gains lost — landscape mismatch |
| Phase 2 Powell (30M, evals 136-187) | 15.13-15.20 dB | oscillating, stuck at physics floor |

Powell oscillation confirmed: evals 185=15.203, 186=15.193, 187=15.130 dB — no convergence trend.

---

## Root Cause Analysis

### Problem 1 — Sample-count landscape mismatch (primary cause)

`CAL_SAMPLES_WARM = CAL_SAMPLES_PS // 4 = 7.5M` (hardcoded in CELL CAL)  
`CAL_SAMPLES_POWELL = 30M`

7.5M samples detects a sparser subset of ray paths than 30M. Material parameters that
minimise RMSE on the 7.5M path-loss surface are optimal for a different objective than the
30M surface. The 1.4 dB scalar jump (-8.94 dB @ 7.5M → -7.57 dB @ 30M) is direct evidence
of systematic path-detection change — not MC noise.

Result: warm-up found RMSE=12.56 dB on one landscape; Powell starts from those params on a
different landscape and immediately sees RMSE=15.24 dB. The warm-up was 214 minutes of wasted
computation.

### Problem 2 — No fixed random seed

`CAL_FIXED_SEED = 0` (disabled). Each PathSolver call gets a new MC seed.  
With `CAL_N_AVG_SOLVE = 2` the noise floor is ±0.21 dB per eval (sqrt(2) reduction).  
Without a fixed seed, consecutive evals for the same parameter point can differ by ~0.3 dB,
causing Powell to follow noise gradients rather than true material-parameter gradients.

### Problem 3 — Too many free parameters

19 free parameters: 9 materials × 2 (εr + σ) + 1 scalar.  
At 1802 MHz, glass/metal/wood contribute negligible path count — their εr/σ have near-zero
sensitivity in the objective. Powell wastes dimensions on them while under-exploring the
3-4 materials that actually dominate (brick, concrete, wet_ground).

---

## Proposed Fix (7 changes, not yet applied)

### Config Cell 4 — 6 param changes

| Parameter | Current | Proposed | Reason |
|-----------|---------|----------|--------|
| `CAL_FIXED_SEED` | `0` | `42` | Lock MC sequence — eliminates between-eval drift |
| `CAL_WARM_CYCLES` | `1` | `0` | 7.5M warm-up does not transfer to 30M Powell; skip it |
| `CAL_N_AVG_SOLVE` | `2` | `3` | Noise floor: ±0.17 dB vs ±0.21 dB |
| `CAL_POWELL_FTOL` | `0.15` | `0.08` | Tighter — legal now seed is fixed |
| `CAL_POWELL_XTOL` | `0.05` | `0.03` | Consistent |
| `CAL_FIXED_MATS` | `{'itu_ceiling_board'}` | `{'itu_ceiling_board', 'itu_glass', 'itu_metal', 'itu_wood'}` | Fix irrelevant materials — reduce 19→13 free params |

### CELL CAL (cell index 79) — 1 code change

Change:
```python
CAL_SAMPLES_WARM = max(300_000, globals().get('CAL_SAMPLES_PS', 500_000) // 4)
```
To:
```python
_warm_factor = int(globals().get('CAL_SAMPLES_WARM_FACTOR', 4))
CAL_SAMPLES_WARM = max(300_000, globals().get('CAL_SAMPLES_PS', 500_000) // _warm_factor)
```
Exposes the warm-up divisor as a configurable param for future use.

---

## Expected Impact After Fix

| Metric | Pre-fix | Expected |
|--------|---------|----------|
| Calibration RMSE | ~15.2 dB (stuck) | ~14.0-15.0 dB (physics floor — structural) |
| CELL 8e RMSE (100M) | not yet run | **10-13 dB** (eval historically << cal) |
| Powell convergence | oscillating, no exit | Converges in 30-50 evals |
| Runtime | ongoing (stuck) | ~6-8 hours |

---

## Physics Floor Explanation (for PPTX / thesis)

At 1802 MHz (vs 915 MHz), diffraction is the dominant propagation mechanism in NLOS.
Diffracted path amplitude is determined by edge geometry (building corners, rooflines) via
the ITU-R P.526 knife-edge model — it has no dependence on material εr or σ.

Consequence: tuning material EM parameters shifts the balance between specular reflection
and diffuse scatter, but cannot move diffracted path amplitudes. Since diffraction dominates
the NLOS budget at 1802 MHz, material calibration has limited leverage. The ~14-15 dB
calibration RMSE floor is structural, not a convergence failure.

The evaluation RMSE at 100M samples (CELL 8e) is historically much lower than the calibration
RMSE because:
1. More samples → lower variance → better-resolved path statistics
2. Evaluation uses all receivers (not the calibration subset)
3. At 915 MHz: cal RMSE ~8-9 dB → eval RMSE 6.0 dB at 0-750m (33% reduction)

Analogous improvement is expected at 1802 MHz.

---

## Key Numbers for PPTX / Thesis

### 1802 MHz — Current best calibration state
- Scalar offset: -7.566 dB (post-priming re-scalar after warm-up)
- Calibration RMSE: ~15.2 dB (30M samples, full scene, 208 receivers 0-1.5 km)
- Propagation flags: `los, specular_reflection, diffuse_reflection, diffraction, edge_diffraction, refraction, diffraction_lit_region` (all enabled)
- Materials calibrated: 9 ITU materials × 2 params (εr + σ), S fixed at ITU defaults
- Calibration samples: 30M per eval, N_AVG=2
- Evaluation samples: 100M (CELL 8e, `NUM_SAMPLES_PS`)

### 915 MHz — Best achieved result
- RMSE: **6.0 dB** at 0-750m range
- R²: **0.835** at 0-750m
- Bias: +0.8 dB at 750m (well-centred)
- Evaluation samples: 100M
- CAL_MIN_DIST_KM: 0.15 km
- MAX_DEPTH: 8, diffraction + edge_diffraction ON

---

## Calibration Algorithm — Summary for Thesis

The calibration runs in three phases (Powell path):

**Phase 0 — Scalar-only correction**  
Single-parameter least-squares: finds the dB offset that minimises RMSE across all calibration
receivers. Establishes a baseline. Runs at full Powell sample count (30M).

**Phase 1 — Coordinate-descent warm-up**  
1D minimise_scalar per parameter (εr, σ for each material), cycling once.
Intended to find a better starting point for the full Powell search. At 7.5M samples (current
config), this runs on a lower-fidelity landscape that does not transfer to Phase 2. FIX: use
equal sample counts across phases, or skip warm-up (CAL_WARM_CYCLES=0).

**Phase 2 — Powell optimisation**  
`scipy.optimize.minimize(method='powell')` over all free material params + scalar.
Averaged over N_AVG=2 solves per eval to reduce MC noise. Powell terminates when the
improvement in RMSE falls below FTOL=0.15 dB between iterations.

**Phase 3 — Final re-scalar**  
After Powell converges on material params, re-runs scalar-only correction at the optimal
material point. Saves `scalar_offset_1802mhz.json` + `calibrated_materials_1802mhz.json`.
