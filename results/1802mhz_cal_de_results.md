# 1802 MHz CAL-DE Results (Differential Evolution Calibration)

**Date:** 2026-07-31
**Calibration:** Differential Evolution (scipy.optimize.differential_evolution)
**Scene:** 15,486 LiDAR trees, full scene
**Settings:** CAL_DE_SAMPLES=2M, CAL_MAX_DIST_KM=1.5, CAL_MIN_DIST_KM=0.15
**Evaluation:** 100M samples, MAX_DEPTH=8

---

## CAL-DE Runtime

| Metric | Value |
|--------|-------|
| Duration | 329.8 min (5.5 hours) |
| Evaluations | 1260 |
| Converged | Yes |
| Best RMSE (calibration) | 11.609 dB |
| Scalar offset | -5.110 dB |

---

## Calibrated Materials

| Material | εᵣ | σ (S/m) | S | Notes |
|----------|-----|---------|---|-------|
| water_rt | 76.746 | 0.00118 | 0.152 | |
| itu_concrete | 5.377 | 0.04391 | **0.668** | very high S — diffuse scattering |
| itu_brick | 5.555 | 0.18829 | 0.473 | σ near upper bound (0.20) |
| itu_very_dry_ground | 2.909 | 0.00532 | 0.086 | |
| itu_wet_ground | 30.047 | 0.25743 | 0.177 | |

Key characteristic: `itu_concrete S=0.668` — DE found strong diffuse scattering compensates for constrained σ.

---

## CELL 8e Evaluation Results (100M samples, ON incoh)

| Range | N | Bias (dB) | RMSE (dB) | R² | vs Cal 3 | vs Old cal |
|-------|---|-----------|-----------|----|----------|------------|
| 0-100m | 17 | -12.4 | 13.3 | -2.771 | structural | structural |
| 0-200m | 125 | -1.3 | 5.5 | -1.725 | — | — |
| 0-300m | 198 | 0.0 | 5.1 | -0.539 | — | — |
| 0-500m | 385 | +1.0 | 7.8 | 0.348 | ~same | worse |
| 0-750m | 537 | +1.7 | 8.5 | 0.453 | better | worse |
| 0-900m | 635 | +0.7 | 9.0 | 0.409 | — | — |
| 0-1000m | 701 | -0.4 | 9.5 | 0.453 | better | worse |
| 0-1250m | 767 | -1.4 | 10.2 | **0.546** | **NEW RECORD** | better |
| 0-1500m | 808 | -2.2 | 11.0 | **0.542** | **NEW RECORD** | better |
| 0-1750m | 857 | -3.2 | 11.7 | 0.506 | worse | — |
| 0-2000m | 985 | -2.6 | 12.0 | 0.493 | worse | — |
| 0-2250m | 1107 | -1.1 | 12.5 | 0.505 | — | — |
| 0-2500m | 1175 | -0.8 | 12.7 | 0.545 | worse | — |

---

## Full Calibration History Comparison (ON incoh R²)

| Range | Old cal (486 trees) | Cal 3 (σ floor) | Cal 4 (σ bounds) | CAL-DE | **Best** |
|-------|---------------------|-----------------|------------------|--------|---------|
| 0-500m | 0.465 (coh) | ~0.35 | ~0.38 | 0.348 | Old cal |
| 0-750m | **0.515** (coh) | 0.388 | 0.430 | 0.453 | Old cal |
| 0-1000m | 0.476 (coh) | 0.430 | 0.452 | 0.453 | Old cal |
| 0-1250m | 0.508 (coh) | 0.530 | ~0.530 | **0.546** | CAL-DE |
| 0-1500m | 0.469 | 0.533 | ~0.533 | **0.542** | CAL-DE |
| 0-1750m | — | ~0.525 | — | 0.506 | Cal 3 |
| 0-2000m | — | **0.516** | — | 0.493 | Cal 3 |
| 0-2250m | — | — | — | 0.505 | — |
| 0-2500m | — | **0.561** | — | 0.545 | Cal 3 |

---

## Interpretation

### What DE found
- Physical σ bounds respected (concrete 0.044, brick 0.188 — both within [0.030, 0.20])
- Compensated with very high concrete S=0.668 (diffuse scattering)
- Diffuse energy distribution: pushes signal broadly → helps medium range (0-1500m)
- Same calibration RMSE as Powell (~11.6 dB) but different parameter space

### Range-dependent behaviour
- **Short range (0-750m):** Diffuse concrete scatters energy away from specular paths → slightly worse than old cal
- **Medium range (0-1250m to 0-1500m):** Broad energy distribution helps → NEW RECORDS
- **1750m-2000m dip:** Scalar -5.11 dB slightly over-corrects at this range (bias: -3.2 dB)
- **2250m-2500m recovery:** R² recovers to 0.545 — second-best long-range result ever

### Why CAL-DE didn't beat Cal 3 at 0-2500m
- `CAL_MAX_DIST_KM=1.5` — receivers beyond 1.5km were not included in calibration
- DE optimised for 0-1.5km window; generalisation to 2-2.5km is imperfect
- Cal 3 happened to generalise better to long range despite different parameter values

### Near-range failure (0-300m)
- Bias = -12.4 dB at 0-100m (simulation underpredicts)
- Structural issue: mast-shadow LOS receivers — not a calibration problem
- Same in all calibrations

---

## Records Set by CAL-DE

| Range | R² | Previous best |
|-------|-----|--------------|
| **0-1250m** | **0.546** | Cal 3: 0.530 |
| **0-1500m** | **0.542** | Cal 3: 0.533 |

---

## Recommendation for Next Steps

### Option A — Recalibrate with CAL_MAX_DIST_KM=2.0 (Powell)
- Include 985 receivers (vs 808 at 1.5km)
- Forces optimizer to balance short and long range
- Expected: R²=0.50+ at all ranges, possible new records at 0-2000m+
- Runtime: ~2-3 hours (Powell faster than DE)

### Option B — Accept split results for thesis
- CAL-DE: best for 0-1250m (0.546) and 0-1500m (0.542) analysis
- Cal 3: best for 0-2500m (0.561) overall coverage
- No additional compute required

### Option C — CAL-DE with CAL_MAX_DIST_KM=2.5
- Full long-range coverage in calibration
- ~6 hours runtime
- Highest chance of a single calibration that dominates all ranges
