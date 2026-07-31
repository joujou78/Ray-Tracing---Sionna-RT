# 1802 MHz Calibration 4 — Full Results & Interpretation
**Date:** 2026-07-31  
**Branch:** claude/cool-cori-rrWbY

---

## 1. Calibration Setup

| Parameter | Value |
|-----------|-------|
| Frequency | 1802.5 MHz (λ = 16.7 cm) |
| Scene | Nottingham Ofcom 2018 |
| Trees | 15,486 LiDAR crown-detected |
| MAX_DEPTH | 8 |
| CELL 8e samples | 100M |
| CELL CAL samples | 10M per eval |
| σ floor | itu_brick ≥ 0.030, itu_concrete ≥ 0.030 |
| σ ceiling | itu_brick ≤ 0.20, itu_concrete ≤ 0.20 ← NEW |
| DISABLE_VEG_DISCS | True |
| Weissberger | Active (ITU-R P.833-9, STRtree building exclusion) |

---

## 2. CELL 8e Full Evaluation Results (100M samples)

| Range | N | ON incoh R² | ON incoh Bias | ON incoh RMSE | ON coh R² | ON coh Bias | ON coh RMSE |
|-------|---|-------------|---------------|---------------|-----------|-------------|-------------|
| 0–300m | 198 | −0.728 | +1.8 dB | 5.4 dB | −1.659 | −4.3 dB | 6.7 dB |
| 0–500m | 385 | 0.270 | +1.8 dB | 8.3 dB | **0.345** | −4.3 dB | 7.8 dB |
| 0–750m | 537 | 0.336 | +2.3 dB | 9.4 dB | **0.430** | −3.4 dB | 8.7 dB |
| 0–900m | 635 | 0.346 | +1.3 dB | 9.5 dB | **0.394** | −3.6 dB | 9.1 dB |
| 0–1000m | 701 | 0.414 | +0.3 dB | 9.8 dB | **0.429** | −4.4 dB | 9.7 dB |
| 0–1250m | 767 | **0.519** | −0.6 dB | 10.5 dB | 0.512 | −5.3 dB | 10.6 dB |
| 0–1500m | 808 | **0.527** | −1.4 dB | 11.2 dB | 0.516 | −6.0 dB | 11.3 dB |
| 0–1750m | 857 | **0.496** | −2.4 dB | 11.9 dB | 0.470 | −6.8 dB | 12.2 dB |
| 0–2000m | 984 | **0.510** | −2.2 dB | 11.8 dB | 0.488 | −5.9 dB | 12.0 dB |
| 0–2250m | 1109 | **0.507** | −0.8 dB | 12.5 dB | 0.484 | −4.0 dB | 12.8 dB |
| 0–2500m | 1177 | **0.541** | −0.8 dB | 12.7 dB | 0.506 | −3.6 dB | 13.2 dB |

*Note: 0–2750m, 0–3000m, 0–3500m, 0–4000m all return identical results to 0–2500m — no additional receivers beyond 2500m in this dataset.*

---

## 3. Full Calibration History Comparison

| Range | Old cal (486 trees) | Cal 2 (no floor) | Cal 3 (floor only) | **Cal 4 (floor+ceiling)** | Best overall |
|-------|--------------------|--------------------|---------------------|---------------------------|--------------|
| 0–500m | 0.465 ON coh | ~0.320 ON coh | 0.320 ON coh | **0.345** ON coh | Old cal |
| 0–750m | **0.515** ON coh | 0.404 ON coh | 0.388 ON coh | 0.430 ON coh | Old cal |
| 0–1000m | 0.476 ON coh | ~0.440 | 0.427 ON incoh | **0.429** ON coh | Old cal |
| 0–1250m | 0.508 ON coh | 0.517 ON coh | 0.530 ON incoh | 0.519 ON incoh | Cal 3 |
| 0–1500m | 0.469 ON coh | 0.523 ON coh | **0.533** ON incoh | 0.527 ON incoh | Cal 3 |
| 0–2000m | 0.456 ON best | ~0.499 | **0.516** ON incoh | 0.510 ON incoh | Cal 3 |
| 0–2500m | — | — | **0.561** ON incoh | 0.541 ON incoh | Cal 3 |

---

## 4. Interpretation

### 4.1 σ Upper Bound Effect
The concrete σ ceiling at 0.20 S/m prevented Powell from finding the unphysical σ=3.94 minimum found in Cal 3.

**Result at 0–750m:**
- Cal 3 (no ceiling): ON coh R²=0.388, bias=−3.9 dB
- Cal 4 (ceiling=0.20): ON coh R²=0.430, bias=−3.4 dB
- Improvement: +0.042 R², −0.5 dB bias ✓

**Result at 0–1000m:** ON coh and ON incoh now nearly equal (0.429 vs 0.414) — materials are more physically balanced.

### 4.2 Method dominance
- **0–1000m: ON coh is best** (bias corrected by calibration, coherent interference captured)
- **1000m+: ON incoh takes over** (diffuse scatter paths dominate, incoherent sum captures spatial average)
- This is consistent with 1802 MHz physics: shorter wavelength means coherent paths decorrelate faster with distance

### 4.3 Remaining gap at 0–750m
Cal 4 ON coh R²=0.430 vs old cal 0.515 — gap of 0.085 remains. Two possible causes:
1. **Scene geometry**: old cal used 486 trees (simpler scene), fewer scattering paths — coherent LOS/specular paths dominated and matched well
2. **Calibration still not fully converged**: Powell with 11 params and physical bounds may need more iterations or a global search method

### 4.4 Long-range comparison vs Cal 3
Cal 3 slightly outperforms Cal 4 at long range (0.561 vs 0.541 at 0–2500m). The extreme concrete σ=3.94 in Cal 3 was unphysical but accidentally created very strong reflections that helped at long range where diffuse scatter dominates. Physical bounds produce more correct but slightly lower long-range R².

### 4.5 Scattering ON vs OFF
At 0–2500m: ON incoh R²=0.541 vs OFF incoh R²=0.193 — scattering accounts for 0.348 R². Critical mechanism.

---

## 5. Progressive Improvement Summary

| Cal | Key change | 0–750m best R² | 0–1500m best R² | 0–2500m best R² |
|-----|-----------|----------------|-----------------|-----------------|
| Old (486 trees) | Baseline | 0.515 ON coh | 0.469 ON coh | — |
| Cal 1 (15k trees, bad metal_barrier) | 15,486 trees | 0.317 | — | — |
| Cal 2 (clean, no bounds) | Metal_barrier fixed | 0.404 ON coh | 0.523 ON coh | 0.351 |
| Cal 3 (σ floor) | Lower bound only | 0.388 ON coh | **0.533** ON incoh | **0.561** ON incoh |
| **Cal 4 (σ floor+ceiling)** | Both bounds | **0.430** ON coh | 0.527 ON incoh | 0.541 ON incoh |

---

## 6. Next Options

### Option A — Differential Evolution (global search)
Replace Powell with `scipy.optimize.differential_evolution` (CAL-DE cell).
- Escapes local minima Powell cannot
- 3–5× more evals (~24h) but finds global minimum
- Expected: 0–750m R² push toward 0.47–0.50

### Option B — OS MasterMap building footprints
Sub-metre building accuracy vs OSM's 2–5m error.
At λ=16.7cm, footprint errors directly affect coherent path phase → biggest geometry lever remaining.

### Option C — Accept current and publish
Cal 4 at 0–750m R²=0.430 and 0–1500m R²=0.527 is a strong result.
Thesis-worthy: significant improvement over old cal at long range, consistent physics, well-understood limitations.
