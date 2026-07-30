# 1802 MHz Calibration 3 — Full Results & Interpretation
**Date:** 2026-07-30  
**Branch:** claude/cool-cori-rrWbY

---

## 1. Calibration Setup

| Parameter | Value |
|-----------|-------|
| Frequency | 1802.5 MHz (λ = 16.7 cm) |
| Scene | Nottingham Ofcom 2018 |
| Trees | 15,486 LiDAR crown-detected (vs 486 OSM in old cal) |
| MAX_DEPTH | 8 |
| CELL 8e samples | 100M |
| CELL CAL samples | 10M per eval |
| CAL evals | 129 (381 min) |
| CAL RMSE final | 11.60 dB |
| Scalar offset | −6.768 dB |
| σ floor | itu_brick ≥ 0.030, itu_concrete ≥ 0.030 |
| σ ceiling | None (bug — caused Powell to find concrete σ = 3.94) |
| DISABLE_VEG_DISCS | True |
| Weissberger | Active (ITU-R P.833-9, STRtree building exclusion) |

---

## 2. Calibrated Material Parameters

| Material | εr | σ (S/m) | S | Notes |
|---|---|---|---|---|
| itu_brick | 4.62 | 0.0682 | 0.250 | Physically reasonable — σ floor worked ✓ |
| itu_concrete | 6.52 | **3.9386** | 0.300 | Unphysical — 75× ITU default, wall loss 401 dB |
| itu_wet_ground | 32.74 | 0.0217 | 0.300 | |
| itu_very_dry_ground | 3.59 | 0.0010 | 0.300 | |
| water_rt | 61.74 | 0.0297 | 0.050 | |
| itu_glass | 6.27 | 0.0087 | 0.080 | Fixed |
| itu_metal | 1.00 | 10,000,000 | 0.050 | Fixed |
| concrete_barrier | 5.31 | 0.0525 | 0.300 | Fixed |
| metal_barrier | 1.00 | 10,000,000 | 0.050 | Fixed |
| canopy_itu_vegetation | 1.50 | 0.0027 | 0.400 | Fixed |
| trunk_itu_wood | 1.99 | 0.0088 | 0.150 | Fixed |
| itu_ceiling_board | 1.00 | 0.0000 | 0.050 | Fixed |

---

## 3. CELL 8e Full Evaluation Results (100M samples)

### All ranges — ON scattering

| Range | N | ON incoh R² | ON incoh Bias | ON incoh RMSE | ON coh R² | ON coh Bias | ON coh RMSE |
|-------|---|-------------|---------------|---------------|-----------|-------------|-------------|
| 0–100m | 17 | −1.958 | −10.7 dB | 11.8 dB | −5.468 | −16.6 dB | 17.5 dB |
| 0–200m | 125 | −1.575 | +0.3 dB | 5.3 dB | −4.497 | −6.2 dB | 7.8 dB |
| 0–300m | 198 | −0.697 | +1.7 dB | 5.4 dB | −1.923 | −5.0 dB | 7.0 dB |
| 0–500m | 385 | 0.288 | +1.7 dB | 8.2 dB | 0.320 | −4.6 dB | 8.0 dB |
| 0–750m | 537 | 0.350 | +2.3 dB | 9.3 dB | 0.388 | −3.9 dB | 9.0 dB |
| 0–900m | 635 | 0.358 | +1.3 dB | 9.4 dB | 0.365 | −4.2 dB | 9.3 dB |
| 0–1000m | 701 | **0.427** | +0.4 dB | 9.7 dB | 0.391 | −4.9 dB | 10.0 dB |
| 0–1250m | 767 | **0.530** | −0.6 dB | 10.4 dB | 0.479 | −5.9 dB | 11.0 dB |
| 0–1500m | 808 | **0.533** | −1.4 dB | 11.1 dB | 0.489 | −6.5 dB | 11.6 dB |
| 0–1750m | 857 | **0.503** | −2.4 dB | 11.8 dB | 0.447 | −7.3 dB | 12.4 dB |
| 0–2000m | 984 | **0.516** | −2.2 dB | 11.7 dB | 0.474 | −6.3 dB | 12.2 dB |
| 0–2250m | 1108 | **0.528** | −0.8 dB | 12.2 dB | 0.489 | −4.4 dB | 12.7 dB |

### Scattering OFF comparison at key ranges

| Range | OFF incoh R² | OFF coh R² | ON vs OFF gain (incoh) |
|-------|-------------|-----------|------------------------|
| 0–750m | 0.291 | 0.072 | +0.059 |
| 0–1250m | 0.419 | 0.333 | +0.111 |
| 0–1500m | 0.434 | 0.375 | +0.099 |
| 0–2000m | 0.255 | 0.198 | +0.261 |
| 0–2250m | 0.220 | 0.170 | +0.308 |

---

## 4. Comparison vs All Previous Calibrations

| Range | Old cal (486 trees) | Cal 2 (no floor) | **Cal 3 (σ floor)** | Best overall |
|-------|--------------------|--------------------|---------------------|--------------|
| 0–500m | 0.465 ON coh | ~0.320 ON coh | 0.320 ON coh | Old cal |
| 0–750m | **0.515** ON coh | 0.404 ON coh | 0.388 ON coh | Old cal |
| 0–1000m | 0.476 ON coh | ~0.440 ON coh | 0.427 ON incoh | Old cal |
| 0–1250m | 0.508 ON coh | 0.517 ON coh | **0.530** ON incoh | **Cal 3** |
| 0–1500m | 0.469 ON coh | 0.523 ON coh | **0.533** ON incoh | **Cal 3** |
| 0–2000m | 0.456 ON best | ~0.499 ON coh | **0.516** ON incoh | **Cal 3** |
| 0–2250m | — | — | **0.528** ON incoh | **Cal 3** |

---

## 5. Interpretation

### 5.1 What worked
- **LiDAR trees (15,486) improve long-range accuracy significantly.** At 0–1250m, R² improved from 0.508 (old, 486 trees) to 0.530 (+0.022). At 0–1500m, 0.469 → 0.533 (+0.064). At 0–2000m, 0.456 → 0.516 (+0.060). Trees add scatter budget that fills in diffracted/attenuated paths at longer ranges.
- **ON scattering consistently dominates OFF** — scattering is essential at 1802 MHz. At 0–2000m, ON incoh R²=0.516 vs OFF incoh 0.255 — scattering adds 0.26 R².
- **ON incoh is the best method from 1000m+.** At shorter wavelengths (1802 MHz) and longer ranges, diffuse scatter paths accumulate and incoherent combining captures them better.
- **σ floor for brick works correctly.** Brick σ = 0.068 S/m (vs ITU default 0.048) — above floor, physically realistic, buildings reflect correctly.

### 5.2 What failed
- **Concrete σ = 3.94 S/m is physically unrealistic.** Real concrete conductivity: 0.015–0.15 S/m. Powell found a bad local minimum at the unphysical high end (75× ITU default) because no upper bound was set.
- **Concrete wall loss = 401 dB** — buildings behave as perfect reflectors/barriers. This creates very strong coherent paths (−4 to −7 dB coherent bias across all ranges) and kills ON coh R² at 0–750m.
- **No σ upper bound was a design gap.** The σ floor fix (lower bound) was correct but incomplete — both lower AND upper bounds are needed to constrain Powell to the physical parameter space.

### 5.3 Method crossover
- **0–900m: ON coh slightly better than ON incoh** (0.388 vs 0.350 at 0–750m) despite the −4 dB bias. Short-range coherent interference pattern is still partially captured.
- **1000m+: ON incoh dominates** — bias from over-reflecting concrete (-5 to -7 dB) hurts coherent combining more at longer ranges where more bounces accumulate the error.

### 5.4 Scattering ON vs OFF
- Scattering gain grows with range: +0.06 at 0–750m, +0.11 at 0–1250m, +0.26 at 0–2000m.
- At long range, diffuse scatter is the primary mechanism reaching receivers — direct and specular paths are fully blocked by buildings and terrain.

---

## 6. Next Step — Calibration 4

**One code change in CELL CAL:**

Add `_SIG_MAX_PER_MAT` immediately after `_SIG_MIN_PER_MAT`:
```python
_SIG_MAX_PER_MAT = {
    'itu_brick':    0.20,   # max 4× ITU default
    'itu_concrete': 0.20,   # max 4× ITU default
}
```

Update upper bound line:
```python
np.log(min(_SIG_MAX_PER_MAT.get(_mn, _SIG_MAX), _p['sig0']*100))
```

**Then:** `USE_CALIBRATED_FILES = False` → CELL CAL → CELL 4A → CELL 8e

**Target for Cal 4:**
- 0–750m ON coh R² ≥ 0.47 (recover from 0.388, approach old cal 0.515)
- 0–1250m R² ≥ 0.52 (maintain Cal 3 record)
- 0–1500m R² ≥ 0.52 (maintain Cal 3 record)
- Coherent bias returns to ~0 dB (concrete σ back to 0.05–0.15 S/m)

If Cal 4 achieves 0–750m ≥ 0.47 AND 0–1250m ≥ 0.52 simultaneously, it will be the **best full-range result across all calibrations and scene configurations.**
