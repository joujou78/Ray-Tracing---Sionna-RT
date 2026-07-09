# Nottingham 915 MHz — RMSE Improvement Roadmap

**Current best:** RMSE=8.27 dB, R²=0.806@750m / 0.758@1km / 0.676@1250m  
**Target:** Beat 8.27 dB RMSE and improve R² at all distances (0–1750m)  
**Scene:** Sionna RT 2.0, full Nottingham scene, MAX_DEPTH=8, ITU-R P.2040-2 materials

---

## Tier 1 — Immediate, High Impact

| # | Improvement | How | Expected Gain |
|---|-------------|-----|---------------|
| 1.1 | **Warm start from calibrated values** | CAL_N_ITER=2 does this automatically — pass 2 starts from pass 1 calibrated materials | -1 to -2 dB |
| 1.2 | **More calibration samples** | `CAL_SAMPLES_PS = 10_000_000` or 50M — reduces stochastic noise in Powell, cleaner gradient signal. 8.27 dB tag noted 50M samples. | -1 to -3 dB |
| 1.3 | **Tighter Powell tolerance** | `CAL_POWELL_XTOL = 0.001` (was 0.01), `CAL_POWELL_MAXITER = 50` (was 30) | -0.5 to -1 dB |

---

## Tier 2 — Scene Improvements

| # | Improvement | How | Expected Gain |
|---|-------------|-----|---------------|
| 2.1 | **Fix 8 near-range mast-shadow receivers** | Accurate TX antenna pattern (directional, not omnidirectional) or correct TX height — these 8 receivers cause R²<0 at 0–300m structural bias | R²@300m fix |
| 2.2 | **Higher terrain resolution** | `TERRAIN_GRID_N = 2000` (was 1000) — finer terrain captures micro-elevation effects at far range where R² drops | R²@1250m+ |
| 2.3 | **OS road polygons** | True road widths from Ordnance Survey instead of OSM estimates | scene fidelity |
| 2.4 | **Building height accuracy** | Cross-check 581 default-height buildings (use alternative LiDAR source or OS data) | near-range |

---

## Tier 3 — Physics Model

| # | Improvement | How | Expected Gain |
|---|-------------|-----|---------------|
| 3.1 | **DirectivePattern scattering** | Sionna RT 2.0 supports directive scattering — more physically accurate for rough surfaces than default Lambertian | NLOS accuracy |
| 3.2 | **Ground reflection (two-ray)** | Two-ray ground reflection model for long-distance paths (>1km) — could fix far-range R² collapse beyond 1250m | R²@1250m+ |
| 3.3 | **Refraction through buildings** | Partial transparency with calibrated er/sigma for glass/wood — helps deep NLOS receivers | NLOS |
| 3.4 | **TX antenna pattern** | Replace omnidirectional with actual antenna radiation pattern from Ofcom dataset if available | near-range |

---

## Tier 4 — Calibration Strategy

| # | Improvement | How | Expected Gain |
|---|-------------|-----|---------------|
| 4.1 | **Differential evolution optimizer** | Replace Powell with `scipy.optimize.differential_evolution` — global optimizer, avoids local minima. Much slower but finds better solutions | global optimum |
| 4.2 | **Extended calibration range** | `CAL_MAX_DIST_KM = 2.0` — include more far-range receivers in calibration to improve R²@1250m+ | far-range R² |
| 4.3 | **Per-distance-band calibration** | Separate material tuning for near (0–500m) / mid (500m–1km) / far (1km+) receiver subsets | distance-dependent |
| 4.4 | **ML/NN augmentation** | Sionna neural calibration (CELL B1 / Sionna 0.18) — NN-augmented path loss correction on top of RT | -1 to -3 dB |

---

## Implementation Order

```
Current run:  CAL_N_ITER=2 + 2M samples (in progress) → baseline
Step 1:       Tier 1.2 — increase CAL_SAMPLES_PS to 10M or 50M, re-run CAL
Step 2:       Tier 1.3 — tighter Powell tolerance, more iterations
Step 3:       Tier 2.1 — investigate 8 near-range mast-shadow receivers
Step 4:       Tier 2.2 — TERRAIN_GRID_N=2000 (requires terrain rebuild)
Step 5:       Tier 3.1 — DirectivePattern scattering in Sionna RT 2.0
Step 6:       Tier 4.1 — Differential evolution for global calibration
```

---

## Known Dead Ends (do not retry)

| Approach | Reason |
|----------|--------|
| Disc PLYs S > 0 | Scatter flood — 700× ON/OFF ratio |
| Disc PLYs S = 0 | Over-blocking +7.7 dB |
| VEG_AUGMENT_TERRAIN | wet_ground S=0.30 → scatter flood |
| MAX_DEPTH > 8 | Extra bounces → spatial noise, R² drops to 0.555 |
| NUM_SAMPLES_PS > 2M (eval) | Calibration-evaluation mismatch |

---

*Deep research findings (Sionna RT docs, academic papers, ITU-R P.833) to be merged here when workflow completes.*
