# Sionna RT — Nottingham 915 MHz Scene: Session Reference

## Project Overview
Ray tracing simulation of the Ofcom 2018 Nottingham 915 MHz dataset using Sionna 2.0.
- Scene builder: `sionna019_scene_builder.ipynb`
- Simulation: `sionna2_915mhz_dem_simulation.ipynb`
- CRS: **EPSG:27700 (British National Grid)**, always_xy=True — never UTM
- Scene directory: `~/sionna_rt/nottingham_ofcom2018_915mhz_dem/scene_v4_full/`
- Working branch: `claude/cool-cori-rrWbY`

---

## 1802 MHz Results (old 486-tree cal applied to 15,486-tree scene — pre-recalibration baseline)

Best method: **ON coh** at short-medium range (0-1250m); **ON incoh** competitive at 1500m+

| Range | N | Method | Bias (dB) | RMSE (dB) | R² |
|-------|---|--------|-----------|-----------|-----|
| 0-500m | 385 | ON coh | -2.0 | 7.1 | **0.465** |
| 0-750m | 537 | ON coh | -1.1 | 8.0 | **0.515** |
| 0-1000m | 701 | ON coh | -2.7 | 9.3 | **0.476** |
| 0-1250m | 767 | ON coh | -4.1 | 10.6 | **0.508** |
| 0-1500m | 808 | ON coh | -5.1 | 11.8 | **0.469** |
| 0-2000m | 985 | ON best | -0.4 | 12.4 | **0.456** |
| 0-2500m | 1177 | ON coh | -3.7 | 13.9 | **0.452** |

Notes:
- ON incoh has +3-4 dB positive bias at 0-750m — calibration was for 486-tree scene, now 15,486 trees changes scatter budget
- ON coh consistently better than incoh at 1802 MHz (shorter wavelength → stronger coherent interference)
- Crossover at ~1750m: incoh and coh converge, incoh slightly better beyond
- Weissberger already applied in CELL 8e (always on regardless of CAL_APPLY_WEISSBERGER flag)

## 1802 MHz Results — 15,486-tree scene (FINAL)

**Settings:** CAL_FIX_SCATTER=False / DISABLE_VEG_DISCS=True / CAL_FIXED_SEED=42 / CAL_MAX_DIST_KM=1.5 / CAL_MIN_DIST_KM=0.15 / 100M eval samples

**Best method: ON incoh** (ON coh collapsed — 15,486 trees destroy coherent phase)

| Range | N | Method | Bias (dB) | RMSE (dB) | R² |
|-------|---|--------|-----------|-----------|-----|
| 0-1000m | 701 | ON incoh | -1.4 | 9.6 | **0.442** |
| 0-1000m | 701 | ON coh | -6.6 | 11.6 | 0.187 |
| 0-1250m | 767 | ON incoh | -2.4 | 10.6 | **0.509** |
| 0-1250m | 767 | ON coh | -8.2 | 13.4 | 0.220 |

Full 0-1500m summary (ON incoh — best method):

| Range | N | Bias (dB) | RMSE (dB) | R² |
|-------|---|-----------|-----------|-----|
| 0-1000m | 701 | -1.4 | 9.6 | **0.442** |
| 0-1250m | 767 | -2.4 | 10.6 | **0.509** |
| 0-1500m | 808 | -3.3 | 11.6 | **0.488** |

Trend: R² peaks at 0-1250m; negative bias grows then stabilises (-1.4 → -2.4 → -3.3 → -4.4 → -4.0 dB); R² recovers slightly at 2000m (0.448 vs 0.428 at 1750m) — 1750-2000m band well-predicted.

| Range | N | Bias (dB) | RMSE (dB) | R² |
|-------|---|-----------|-----------|-----|
| 0-1000m | 701 | -1.4 | 9.6 | **0.442** |
| 0-1250m | 767 | -2.4 | 10.6 | **0.509** |
| 0-1500m | 808 | -3.3 | 11.6 | 0.488 |
| 0-1750m | 857 | -4.4 | 12.6 | 0.428 |
| 0-2000m | 985 | -4.0 | 12.5 | 0.448 |

Full 0-1000m breakdown (N=701, avg ON rays=32313, OFF rays=140):

| Method | Bias (dB) | RMSE (dB) | STD (dB) | R² |
|--------|-----------|-----------|----------|-----|
| ON incoh | -1.4 | 9.6 | 9.5 | **0.442** |
| OFF incoh | -1.3 | 9.9 | 9.8 | 0.407 |
| ON coh | -6.6 | 11.6 | 9.5 | 0.187 |
| OFF coh | +0.7 | 10.5 | 10.5 | 0.327 |
| ON best | -0.5 | 9.7 | 9.6 | 0.433 |
| OFF best | -0.5 | 9.8 | 9.8 | 0.417 |

Full 0-1500m breakdown (N=808, avg ON rays=29070, OFF rays=129):

| Method | Bias (dB) | RMSE (dB) | STD (dB) | R² |
|--------|-----------|-----------|----------|-----|
| ON incoh | -3.3 | 11.6 | 11.1 | **0.488** |
| OFF incoh | -3.0 | 12.0 | 11.6 | 0.453 |
| ON coh | -9.1 | 14.4 | 11.2 | 0.212 |
| OFF coh | -1.1 | 12.6 | 12.6 | 0.396 |
| ON best | -2.2 | 11.6 | 11.4 | 0.490 |
| OFF best | -2.0 | 11.8 | 11.7 | 0.468 |

Full 0-1250m breakdown (N=767, avg ON rays=30209, OFF rays=133):

| Method | Bias (dB) | RMSE (dB) | STD (dB) | R² |
|--------|-----------|-----------|----------|-----|
| ON incoh | -2.4 | 10.6 | 10.4 | **0.509** |
| OFF incoh | -2.1 | 11.1 | 10.8 | 0.470 |
| ON coh | -8.2 | 13.4 | 10.6 | 0.220 |
| OFF coh | -0.2 | 11.7 | 11.7 | 0.407 |
| ON best | -1.3 | 10.7 | 10.7 | 0.500 |
| OFF best | -1.2 | 11.0 | 10.9 | 0.475 |

**Key findings:**
- ON coh collapsed (R²=0.187 at 0-1000m) — 15,486 trees generate massive destructive interference at 1802 MHz (16.7cm wavelength)
- ON incoh is the best method for 1802 MHz with 15,486-tree scene
- R²=0.442 at 0-1000m, 0.509 at 0-1250m — matches old 486-tree ON coh baseline (~0.476/0.508)
- Small negative bias (-1.4 to -2.4 dB) — slight over-prediction at both ranges
- avg_rays ON=32313 vs OFF=140 — scattering active and providing the dominant propagation mechanism
- **These results accepted as final — no further recalibration planned for 1802 MHz**

**Comparison vs old 486-tree baseline:**
| Range | Old (ON coh) | New (ON incoh) | Delta |
|-------|-------------|----------------|-------|
| 0-1000m | 0.476 | 0.442 | -0.034 |
| 0-1250m | 0.508 | 0.509 | +0.001 |

Result: same R² as old 486-tree baseline — R²~0.44-0.51 accepted as the physics floor for 1802 MHz Nottingham with 15,486-tree scene.

## 1802 MHz Calibration History

| Run | Settings | Cal RMSE | Eval R² (0-1000m) | Best method |
|-----|----------|----------|-------------------|-------------|
| Run 1 (486-tree scene) | S locked, 7 params | ~8 dB | 0.476 | ON coh |
| Run 2 (15,486-tree) — **FINAL** | S unlocked, N_AVG=1 | ~13.5-14.5 dB | **0.442** | ON incoh |

## 1802 MHz Pending Tests

| Priority | Test | How | Expected |
|----------|------|-----|----------|
| 1 | LiDAR crown detection tuning | Adjust LIDAR_TREE_MIN_DIST_M / MIN_H_M | density vs false-positive tradeoff |
| 2 | Separate LOS/NLOS scalar in CELL 8e | Medium complexity | -1 to -2 dB RMSE (NYURay approach) |

## Key Findings So Far (1802 MHz)

| Finding | Detail |
|---------|--------|
| ON incoh best for 15,486-tree scene | ON coh collapsed (R²=0.187) — tree coherent interference destroys phase at 1802 MHz |
| Physics floor confirmed: R²~0.44-0.51 | Both runs converge here; matches literature R²~0.5 ceiling for pure geometry+material cal |
| Crossover at ~1750m | incoh becomes competitive beyond this range (old 486-tree finding, still valid) |
| LiDAR trees: 486 → 15,486 | nDSM peak detection, 5m min spacing, 3-30m height filter, building exclusion |
| DISABLE_VEG_DISCS=True | Disc veg (itu_ceiling_board) transparent; 3D canopy (canopy_itu_vegetation) active |
| Weissberger always on in CELL 8e | CAL_APPLY_WEISSBERGER flag only affects CELL CAL, not CELL 8e |
| Phase 3 bug fixed | Comparison was inverted — now correctly keeps Phase 3 if RMSE improves |
| Convergence plot fixed | _mat_names truncated to _ph_arr.shape[1]//3 to avoid IndexError |
| Physics floor confirmed by literature | Dense urban outdoor 1.8 GHz: R²~0.5 ceiling for pure geometry+material cal (arXiv:2507.19653) |
| CAL_SKIP_PROBE must stay True | Warm prior S=0.35 biases sensitivity probe low — probe blocks Powell unless skipped |
| CAL_FIXED_SEED=42 required | Without it: ±4 dB systematic drift between evals, Powell cannot find gradient |
| _SIG_MAX_PER_MAT applied | brick/concrete σ ≤ 0.20 — uncapped Cal-3 produced σ=3.94 (unphysical) |

---

## Scar Hill 915 MHz Status (sionna2_915mhz_dem_simulation_scarhill.ipynb)

**Scene built 2026-08-08 — CELL CAL completed (10.71 dB, iteration 1). CELL 8e run at 10M samples.**

### Results (SRTM 30m terrain, 10M eval samples, ON incoh best method)

| Range | N | Bias (dB) | RMSE (dB) | R² | Notes |
|-------|---|-----------|-----------|-----|-------|
| 0-500m | 75 | +0.7 | 12.0 | -3.43 | near-field scatter noise |
| 0-1000m | 140 | +4.7 | 12.4 | -0.11 | over-prediction mid-range |
| **0-1250m** | **179** | **+0.9** | **15.1** | **+0.083** | **best — bias-centred** |
| 0-1500m | 202 | +2.5 | 15.8 | -0.10 | |
| 0-3000m | 375 | -1.9 | 16.6 | -0.007 | near-zero bias |
| 0-3500m | 441 | -6.1 | 19.3 | +0.055 | |

**Key findings:**
- R²=0.083 peak (0-1250m) — SRTM 30m physics floor for rural hilltop site
- avg_rays ON=19k-40k vs OFF=55 — scatter dominant (DISABLE_VEG_DISCS=False, S=0.50)
- Calibration centred (+0.9 dB at 0-1250m) — cal correct, R² limited by terrain resolution
- CELL CAL: 10.71 dB (820 evals, single iteration, no auto-retry)
- NUM_SAMPLES_PS=10M matches CAL_SAMPLES_PS=10M — fair eval (100M causes scatter mismatch)
- **Only meaningful improvement: Scottish LiDAR 1m DTM (lidar.scot NJ40/41/50/51)**

### Site parameters (from scarhill915.csv header)
| Parameter | Value |
|-----------|-------|
| Site name | Scar Hill, Aberdeenshire, Scotland |
| TX lat/lon | 57.1887 / -2.8547 |
| BNG grid ref | NJ 483 111 (Lumphanan/Torphins area) |
| Frequency | 915.95 MHz |
| TX AGL | 17 m |
| EIRP | 46.9 dBm (TX_CONDUCTED_DBM=45.6 + 1.3 dBi antenna) |
| RX AGL | 1.5 m |
| Noise floor | -124 dBm |
| Records | 143,541 (max range ~32 km — rural Aberdeenshire) |

### Scene configuration
| Parameter | Value | Notes |
|-----------|-------|-------|
| SCENE_WEST/EAST | -2.9374 / -2.65 | ~15 km wide (expanded to cover all 1200 receivers) |
| SCENE_SOUTH/NORTH | 57.1435 / 57.2339 | ~10 km tall |
| TERRAIN_PAD_M | 3000 | 3 km beyond scene bbox |
| CRS | EPSG:27700 (BNG) | valid for all Great Britain |
| TERRAIN_SOURCE | auto → srtm (30m) | Scotland north of EA LiDAR boundary (55.9°N) |
| NDSM_PROVIDER | auto → opentopo | same reason |
| CAL_MAX_DIST_KM | 1.5 | same as Nottingham 915 — auto-discover finds effective range |
| CAL_MIN_DIST_KM | 0.15 | same near-field exclusion |
| CAL_MIN_VALID_FRAC | 0.65 | same as Nottingham 915 |
| CAL_SAMPLES_PS | 10_000_000 | same as Nottingham 915 |
| NUM_SAMPLES_PS | 10_000_000 | matches CAL_SAMPLES_PS=10M — skip CELL 4A for rural scenes (scatter mismatch at 100M) |
| TX_AGL_SCAN_M | [15, 17, 20, 25, 30] | TX height auto-selection |
| RX_EXTRA_GAIN_DB | 0.0 dB | same as Nottingham 915 (no chain loss applied) |

### Scottish LiDAR (1m — better than SRTM 30m)
Download from **lidar.scot** — 4 OS 10km squares cover full scene + 3km terrain padding:

| Square | Absolute BNG | Contents |
|--------|-------------|---------|
| **NJ40** | E:340-350k, N:800-810k | SW quadrant |
| **NJ41** | E:340-350k, N:810-820k | W of TX |
| **NJ50** | E:350-360k, N:800-810k | S of TX |
| **NJ51** | E:350-360k, N:810-820k | TX area |

Tile names: `NJ4003_1m_DTM.tif` → `NJ5619_1m_DTM.tif` — 272 DTM + 272 DSM = 544 files

After download + merge:
```bash
gdal_merge.py -o ~/sionna_rt/scarhill_ofcom_915mhz_dem/dem.tif NJ4*_1m_DTM.tif NJ5*_1m_DTM.tif
gdal_merge.py -o ~/sionna_rt/scarhill_ofcom_915mhz_dem/lidar_dsm.tif NJ4*_1m_DSM.tif NJ5*_1m_DSM.tif
```
Then set `TERRAIN_SOURCE = 'ea_lidar'` and `NDSM_PROVIDER = 'ea'` in scene builder CELL 0.

### Run sequence (same as London)
```
Scene builder: CELL 0 → CELL 1 → CELL 2 → CELL 2b → CELL 4 → CELL B3
Simulation:    CELL 0 → CELL 1 → TX AGL scan → CELL CAL → CELL 4A → CELL 8e (100M)
```

---

## Nottingham 2695 MHz Status (sionna2_2695mhz_dem_simulation.ipynb)

**Run 2 CELL 8e complete (2026-08-09). Best result: R²=0.574 at 0-1250m (ON incoh) — beats 1802 MHz at same range (R²=0.509).**

### Site parameters (from nottingham2695.csv header)
| Parameter | Value |
|-----------|-------|
| Site name | Nottingham |
| TX lat/lon | 52.9863 / -1.2559 (same mast as 1802 MHz) |
| Frequency | 2695 MHz |
| TX AGL | 17 m |
| TX amplifier power | 49.2 dBm |
| TX cable loss | 2.2 dB |
| TX antenna gain | 2.2 dBi |
| TX EIRP | 56 dBm (TX_CONDUCTED_DBM=53.8 + 2.2 dBi) |
| RX AGL | 1.5 m |
| RX chain (total) | -9.3 dB (antenna -1 + cable -0.3 + splitter -6.3 + BPF -1.7) |
| Noise floor | -120 dBm |
| Records | 261,967 (36,351 within scene bbox; 12,594 within 1.5 km cal range) |

### Scene and simulation configuration
| Parameter | Value | Notes |
|-----------|-------|-------|
| SCENE_BASE_DIR | nottingham_ofcom2018_1802mhz_dem | reuse existing scene — no rebuild |
| BASE_DIR | nottingham_ofcom2018_2695mhz_dem | all outputs go here |
| SCENE_WEST/EAST | -1.294229 / -1.218595 | same as 1802 MHz |
| SCENE_SOUTH/NORTH | 52.963691 / 53.008909 | same as 1802 MHz |
| FREQUENCY_HZ | 2695e6 | 2695 MHz |
| VEG_CONDUCTIVITY | 0.15 S/m | ITU-R P.833 at 2.7 GHz (0.05→0.10→0.15 at 0.9→1.8→2.7 GHz) |
| VEG_RELATIVE_PERMITTIVITY | 17.0 | ITU-R P.833 — portable 0.9-3.6 GHz |
| DISABLE_VEG_DISCS | True | all disc/tree geometry transparent; P.833 post-hoc in CELL 8e |
| CAL_FIX_SCATTER | False | S free (er+sigma+S calibrated jointly) |
| CAL_N_AVG_SOLVE | 1 | fixed seed sufficient |
| CAL_SAMPLES_PS | 30_000_000 | 30M (updated from 10M — reduces MC noise floor ±0.21→±0.12 dB) |
| NUM_SAMPLES_PS | 100_000_000 | 100M eval (optimal per 915 MHz benchmark) |
| CAL_MAX_DIST_KM | 1.0 | calibrate within LOS regime only (Rbp=916m at 2695 MHz — avoids dual-slope sign-flip) |
| CAL_MIN_DIST_KM | 0.15 | near-field exclusion |
| EVAL_MIN_DIST_KM | 0.15 | exclude near-field from CELL 8e stats (R²=-12 at 0-100m drags cumulative bands) |
| CAL_SCALAR_BOUNDS | (-30.0, 20.0) | wider than default (-20,5) — pre-cal bias +8 to +15 dB at 2695 MHz |
| NOISE_FLOOR_DBM | -120.0 | from CSV header |
| Sigma bounds | frequency-derived | _SIG_MIN/MAX_PER_MAT from ITU-R P.2040-2 at 2695 MHz |
| Vegetation formula | ITU-R P.833-10 | _p833_atten_db() preferred at 2-3 GHz (Weissberger under-estimates ~40%) |
| Calibration files | calibrated_materials_2695mhz.json + scalar_offset_2695mhz.json | saved to BASE_DIR |

### 2695 MHz Results (Run 1: CAL_MAX_DIST_KM=1.5, P.833 vegetation, brick P.2040-2 fix)

**Settings:** CAL_SCALAR_BOUNDS=(-30,20) / CAL_FIX_SCATTER=False / CAL_MAX_DIST_KM=1.5 / P.833 vegetation / 100M eval

| Range | N | Method | Bias (dB) | RMSE (dB) | R² | Notes |
|-------|---|--------|-----------|-----------|-----|-------|
| 0-1000m | 256 | ON incoh | -6.5 | 13.9 | **0.246** | LOS regime dominant |
| 0-1250m | 328 | ON incoh | 0.0 | 17.8 | 0.173 | dual-slope sign-flip |

**Key findings:**
- Dual-slope breakpoint at Rbp = 916m (4 × hBS × hUT × f/c = 4×17×1.5×2695e6/3e8)
- 0-1000m bias = -6.5 dB (under-predicts) vs 1000-1250m bias = +23.1 dB (massively over-predicts)
- Calibration averages to 0.0 dB at 0-1250m — masks sign-flip, suppresses R² from 0.246 to 0.173
- 3GPP TR 38.901 UMa NLOS shadow fading floor: σ_SF = 7.82 dB (physics minimum RMSE)
- Bug fixed: Powell scalar bounds were (-20,5) — clipped Phase 0 optimal scalar (+10-12 dB) to +5 dB → fixed to (-30,20)
- Bug fixed: brick sigma used P.2040-1 (2015) freq-dependent formula → fixed to P.2040-2 (2021) flat 0.038 S/m
- Next run: CAL_MAX_DIST_KM=1.0 (below Rbp) to calibrate within single-slope LOS regime

### 2695 MHz Results (Run 2: CAL_MAX_DIST_KM=1.0, CAL_SAMPLES_PS=10M, scalar=-2.305 dB) — CELL 8e in progress

**Settings:** CAL_SCALAR_BOUNDS=(-30,20) / CAL_FIX_SCATTER=False / CAL_MAX_DIST_KM=1.0 / EVAL_MIN_DIST_KM=0.0 / 100M eval / Cal RMSE=14.37 dB

**Best method: ON incoh** — scattering provides 45+ R² points vs OFF incoh at 0-1000m

| Range | N (ON) | Bias (dB) | RMSE (dB) | R² (ON incoh) | R² (OFF incoh) | Notes |
|-------|--------|-----------|-----------|---------------|----------------|-------|
| 0-750m | 198 | +1.5 | 11.8 | 0.321 | 0.251 | |
| 0-900m | 233 | +2.5 | 11.5 | 0.408 | 0.171 | |
| 0-1000m | 256 | +2.7 | 11.1 | 0.515 | 0.063 | within calibrated range |
| **0-1250m** | **324** | **+4.8** | **12.7** | **0.574** | **0.070** | **peak R² — beats 1802 MHz (0.509)** |

Full 0-1000m breakdown (N=256, avg ON rays=17702, OFF rays=80):

| Method | Bias (dB) | RMSE (dB) | R² |
|--------|-----------|-----------|-----|
| ON incoh | +2.7 | 11.1 | **0.515** |
| OFF incoh | +6.1 | 15.5 | 0.063 |
| ON coh | -6.9 | 12.6 | 0.376 |
| OFF coh | +7.3 | 16.5 | -0.065 |
| ON best | +5.5 | 12.9 | 0.351 |

Full 0-1250m breakdown (N=324 ON / 264 OFF, avg ON rays=12398, OFF rays=55):

| Method | Bias (dB) | RMSE (dB) | R² |
|--------|-----------|-----------|-----|
| ON incoh | +4.8 | 12.7 | **0.574** |
| OFF incoh | +6.4 | 15.8 | 0.070 |
| ON coh | -3.7 | 14.6 | 0.436 |
| OFF coh | +7.6 | 16.9 | -0.058 |
| ON best | +7.5 | 14.4 | 0.447 |

**Key findings (Run 2):**
- CAL_MAX_DIST_KM=1.0 (below Rbp=916m) eliminates dual-slope sign-flip — R² jumps from 0.246 (Run 1) to 0.574 at 0-1250m
- Scattering is critical: ON incoh (0.574) vs OFF incoh (0.070) — 50 point gap; model fails without scatter
- 50 receivers in 0-1250m have scatter-only paths (no LOS/specular) — would be coverage holes with scattering OFF
- ON coh competitive (0.436) — unlike 1802 MHz where coherent collapsed; DISABLE_CANOPY=True reduces destructive interference
- Bias grows with range: +2.7 dB at 0-1000m → +4.8 dB at 0-1250m — slight over-prediction in NLOS regime
- RMSE=11.1 dB at 0-1000m — 3.3 dB above physics floor (σ_SF=7.82 dB); mainly MC noise from 10M cal samples
- R² peaks at 0-1250m (0.574) — 1000-1250m band well-predicted despite being beyond calibrated range
- Beats 1802 MHz at 0-1250m: 2695 MHz R²=0.574 vs 1802 MHz R²=0.509

Full distance breakdown (ON incoh — best method):

| Range | N (ON) | Bias (dB) | RMSE (dB) | R² | Notes |
|-------|--------|-----------|-----------|-----|-------|
| 0-500m | 132 | +0.1 | 13.3 | -0.536 | near-field noise (below CAL_MIN_DIST_KM floor) |
| 0-750m | 198 | +1.5 | 11.8 | 0.321 | |
| 0-900m | 233 | +2.5 | 11.5 | 0.408 | |
| 0-1000m | 256 | +2.7 | 11.1 | **0.515** | calibrated range ceiling |
| 0-1250m | 324 | +4.8 | 12.7 | **0.574** | peak R² |
| 0-1500m | 504 | +1.3 | 16.8 | 0.282 | dual-slope NLOS transition — sharp R² drop |
| 0-1750m | 651 | -0.4 | 19.6 | -0.109 | deep NLOS |
| 0-2000m | 975 | +0.3 | 18.2 | -0.293 | bias centred; RMSE recovers slightly |
| 0-2250m | 1110 | +0.6 | 17.2 | -0.280 | |

**Key observations (full range):**
- Hard cliff at 1250m → 1500m (R² 0.574 → 0.282) — dual-slope NLOS transition zone
- Bias stays near zero at all ranges (+0.6 dB at 0-2250m) — scalar calibration effective throughout
- RMSE recovers 1750m+ (19.6 → 18.2 → 17.2 dB) — deep NLOS simpler geometry, fewer reflections
- OFF methods collapse beyond 1250m: OFF incoh R²=-2.929 at 0-2250m (RMSE=32.7 dB)
- Scattering covers 318 additional receivers at 0-2250m (1110 ON vs 792 OFF valid paths)

**Next step: Run 3 (30M samples, EVAL_MIN_DIST_KM=0.15) — already configured**
- CAL_SAMPLES_PS=30M already committed — reduces MC noise floor ±0.21→±0.12 dB
- EVAL_MIN_DIST_KM=0.15 already committed — removes near-field noise from stats
- Expected: cal RMSE ~11-12 dB, eval RMSE ~9-10 dB at 0-1000m, R² > 0.60 at 0-1250m
- After Run 3: implement separate LOS/NLOS scalar in CELL 8e (-1 to -2 dB RMSE)

### Dual-slope breakpoint analysis (ITU-R P.1411)

Rbp = 4 × hBS × hUT × f / c — frequency comparison:

| Frequency | Rbp | LOS regime | NLOS regime |
|-----------|-----|------------|-------------|
| 915 MHz | 311 m | 0-311m | 311m+ |
| 1802 MHz | 613 m | 0-613m | 613m+ |
| **2695 MHz** | **916 m** | **0-916m** | **916m+** |

At 2695 MHz the breakpoint falls WITHIN the 0-1.5km evaluation range — calibrating across it mixes two physics regimes and destroys R².

### Literature fixes applied (committed `fe21b29`)

| Fix | Formula | Impact |
|-----|---------|--------|
| ITU-R P.833-10 vegetation | A = Am × (1 − exp(−d × γ/Am)); Am=25 dB, γ=2.0 dB/m at ~3 GHz | 8.3 dB at 5m depth vs Weissberger 4.0 dB — 40% more attenuation |
| ITU-R P.2040-2 (2021) brick | σ = 0.038 S/m, freq-independent (d=0) | Corrects 47% overcalculation at 2695 MHz vs old P.2040-1 value |
| 3GPP TR 38.901 UMa reference | LOS PL=28.0+22·log10(d3D)+20·log10(fc); NLOS σ_SF=7.82 dB | Sets physics floor expectation in CELL 8e output |
| CAL_SCALAR_BOUNDS=(-30,20) | Wider Powell scalar range | Prevents Phase 0 +10-12 dB optimal scalar from being clipped to +5 dB |

### Pre-run setup (on your machine)
```bash
mkdir -p ~/sionna_rt/nottingham_ofcom2018_2695mhz_dem/results
cp nottingham2695.csv ~/sionna_rt/nottingham_ofcom2018_2695mhz_dem/
```

### Run sequence
```
NO scene builder needed — reuses 1802 MHz scene directly.
Simulation: CELL 1 → TX AGL scan → CELL CAL → CELL 4A → CELL 8e
```

---

## Nottingham 3602 MHz Status (sionna2_3602mhz_dem_simulation.ipynb)

**CELL 8e Run 1 complete (2026-08-12, pre-per-path fix). Run 2 complete (2026-08-13, per-path P.833 + double-correction fix + height filter). Best: R²=0.154 at 0-1000m (ON incoh).**

### CELL 8e Run 2 Results (per-path P.833 + height filter, N_SCALAR_BINS=10, 100M samples)

Best method: **ON incoh** at 0-1000m (R²=0.154, Bias=+1.1 dB) — ON coh slightly better at 0-900m

| Range | N | Method | Bias (dB) | RMSE (dB) | R² | Notes |
|-------|---|--------|-----------|-----------|-----|-------|
| 0-300m | 71 | ON incoh | +18.1 | 19.4 | -8.366 | EVAL_MIN=250m; near-field noise |
| 0-500m | 308 | ON incoh | +5.9 | 15.8 | -1.748 | short-range noise |
| 0-750m | 598 | ON coh | -2.0 | 12.4 | -0.026 | |
| 0-900m | 740 | ON coh | -3.0 | 12.4 | **0.113** | ON coh best at this range |
| **0-1000m** | **863** | **ON incoh** | **+1.1** | **13.0** | **0.154** | **peak R² — best result** |
| 0-1250m | 867 | ON incoh | +1.0 | 13.4 | 0.103 | N saturates — all receivers within 1.25km |

Full 0-1000m breakdown (N=863, avg ON rays=20750):

| Method | Bias (dB) | RMSE (dB) | R² |
|--------|-----------|-----------|-----|
| ON incoh | +1.1 | 13.0 | **0.154** |
| OFF incoh | +3.3 | 15.6 | -0.228 |
| ON coh | -4.7 | 13.5 | 0.093 |
| OFF coh | +5.1 | 16.6 | -0.383 |
| ON best | +3.9 | 14.0 | 0.012 |

**Improvement vs Run 1 (per-receiver only):**
- Run 1: R² < 0 at ALL ranges (best was -0.026 at 0-750m ON coh)
- Run 2: R² = 0.154 at 0-1000m — per-path P.833 + double-correction fix moved R² positive
- Key fix: removing double-counting (per-receiver Weissberger was applied after per-path P.833 but bin scalar was fit without Weissberger → inconsistent pipeline)

### CELL 8e Run 1 Results (pre-per-path fix, for comparison)

| Range | N | Method | Bias (dB) | RMSE (dB) | R² | Notes |
|-------|---|--------|-----------|-----------|-----|-------|
| 0-300m | 71 | ON incoh | +18.1 | 19.4 | -8.366 | near-field over-correction |
| 0-500m | 308 | ON incoh | +5.9 | 15.8 | -1.748 | |
| 0-750m | 598 | ON coh | -2.0 | 12.4 | **-0.026** | best result (barely negative) |

**Bin scalar (5 bins, Run 1):**
| Bin | Correction | Meaning |
|-----|-----------|---------|
| 0.26 km | -4.99 dB | model 5 dB too optimistic |
| 0.48 km | -6.27 dB | |
| 0.70 km | -22.93 dB | model 35 dB too optimistic before scalar — NLOS collapse |
| 0.92 km | -14.69 dB | |

**Root cause — confirmed diagnosis:**
At λ=8.3 cm, tree branch diameter ≈ λ → near-total opacity. DISABLE_CANOPY=True (required to prevent total ray blockage) makes all vegetation transparent. NLOS paths at 700m+ reach the receiver unrealistically through transparent trees → model predicts 35 dB too much signal before scalar. Per-path P.833 (applied to each ray segment) partially recovers this (R² from -0.026 → +0.154). Double-counting fix (Weissberger disabled when PER_PATH_VEG=True) removes inconsistency in correction pipeline.

**Remaining limitations at R²=0.154:**
- DISABLE_CANOPY=True removes physical geometry — rays pass through trees, not around them
- Per-path P.833 uses 2D horizontal intersection; height filter (z > 30m) added but approximate
- N=867 receivers all within 1.25km — limited dataset statistics at 3602 MHz
- 3GPP TR 38.901 UMa NLOS physics floor: σ_SF=6.0 dB → minimum achievable RMSE ~6 dB; current 13.0 dB = 7 dB above floor

**This is a valid thesis finding:**
> At 3602 MHz, purely geometric surface-based RT fails to model vegetation attenuation. The canopy geometry must be disabled to prevent total ray blockage (DISABLE_CANOPY=True), but this removes the dominant loss mechanism in NLOS paths. Per-path P.833 correction (applied per ray segment using paths.vertices) partially recovers accuracy (R² from <0 to 0.154), but cannot fully compensate for the wrong ray geometry. Final RMSE=13.0 dB is 7 dB above the 3GPP shadow fading floor, demonstrating that geometric RT without volumetric vegetation absorption is frequency-limited.

### Calibration History

| Run | Settings | Phase 0 RMSE | Scalar | After-scalar RMSE | Notes |
|-----|----------|-------------|--------|-------------------|-------|
| Run 0 (aborted) | DISABLE_CANOPY=False, 10M | 46 dB | +30 dB | 29.5 dB | canopy cones blocked all rays >400m |
| Run 1 (aborted) | DISABLE_CANOPY=True, 10M | 31.4 dB | +21.2 dB | 23.1 dB | MC noise floor |
| Run 2 (aborted) | DISABLE_CANOPY=True, 30M, bounds=(-30,20) | 47.2 dB | +30.0 dB (CLIPPED) | 31.6 dB | scalar capped |
| Run 3 (aborted) | DISABLE_CANOPY=True, 30M, bounds=(-60,60) | TBD | TBD | TBD | stuck at noise floor |
| **Run 4 — FINAL** | DISABLE_CANOPY=True, 30M, CAL_MAX=1.0, NF filter | +26.33 dB | **+12.097 dB** | **23.39 dB** | checkpoint saved; CELL 8e run |

### How to Simulate Vegetation Absorption (future work)

Sionna RT 2.0 is a **surface-based tracer** — absorption only occurs at surface interactions, not through volumes. Three approaches to model vegetation attenuation at high frequencies:

**Option 1 — Stacked disc layers (feasible in Sionna RT)**
Replace single canopy cone with N horizontal disc layers at different heights within the crown. Each disc has:
- er ≈ 1.05 (near-air, minimal reflection)
- sigma = high (absorption at each surface hit)
- S = 0.3-0.5 (scatter to surrounding directions)
Each ray passes through multiple discs → cumulative attenuation per layer. More layers → better approximation of volumetric absorption. Scene builder change required; 1802 MHz scene builder is FROZEN.

**Option 2 — Complex permittivity slab (equivalent medium)**
Model canopy as a solid slab with effective complex permittivity derived from ITU-R P.833 one-way attenuation:
- ε_eff = ε_r + i·σ/(ω·ε_0), tune σ to give correct two-way path loss through slab at each frequency
- At 3602 MHz: P.833 gives ~9.8 dB/5m → tune sigma to match
- Problem: Sionna RT computes surface interactions only — a thick slab gives one surface hit, same as a thin slab. No volumetric path-integral absorption.
- Only works if multiple thin slabs are stacked (same as Option 1).

**Option 3 — Per-path post-processing (best accuracy, no scene change)**
Instead of applying P.833 to the final per-receiver path loss (current approach), apply it to each individual ray path before incoherent summation:
- For each path, compute which vegetation polygons the path vertices intersect
- Apply ITU-R P.833 attenuation dB to that path's power before summing with others
- This is a CELL 8e change only — no scene rebuild needed
- Requires access to PathSolver vertex/segment data per path

**Option 4 — Hybrid geometric+statistical (NYURay approach)**
Keep RT for building geometry. Apply a statistical vegetation shadowing model per receiver based on link vegetation depth (current CELL 8e approach, but applied during path combination not after).

**Recommended for thesis continuation:** Option 3 (per-path P.833) — feasible in CELL 8e without scene rebuild, physically correct, and directly addresses the 3602 MHz failure mode.

### CELL CAL Configuration (current — FINAL)
| Parameter | Value | Notes |
|-----------|-------|-------|
| SCENE_BASE_DIR | nottingham_ofcom2018_1802mhz_dem | reuse existing scene |
| FREQUENCY_HZ | 3602.5e6 | |
| DISABLE_CANOPY | True | required — cones block all rays >400m at λ=8.3 cm |
| DISABLE_VEG_DISCS | False | disc PLYs active (S=0.10 horizontal scatter) |
| CAL_MAX_DIST_KM | 1.0 | within LOS regime (Rbp=1225m) |
| CAL_SCALAR_BOUNDS | (-60.0, 60.0) | Phase 0 needs +12 dB |
| CAL_NOISE_MARGIN_DB | 10.0 | excludes RX within 10 dB of noise floor |
| CAL_SAMPLES_PS | 30_000_000 | |
| NUM_SAMPLES_PS | 100_000_000 | |
| EVAL_MIN_DIST_KM | 0.25 | |

**CELL CAL running (2026-08-09). First run at 30M samples with DISABLE_CANOPY=True and CAL_SCALAR_BOUNDS=(-60,60).**

### Site parameters (from nottingham3602.csv header)
| Parameter | Value |
|-----------|-------|
| Site name | Nottingham |
| TX lat/lon | 52.9863 / -1.2559 (same mast as 1802/2695 MHz) |
| Frequency | 3602.5 MHz |
| TX AGL | 17 m |
| TX EIRP | 54 dBm (TX_CONDUCTED_DBM=51.2 + 2.8 dBi) |
| RX AGL | 1.5 m |
| RX chain | 0.0 dB applied (no chain loss) |
| Noise floor | -109 dBm |

### Scene and simulation configuration
| Parameter | Value | Notes |
|-----------|-------|-------|
| SCENE_BASE_DIR | nottingham_ofcom2018_1802mhz_dem | reuse existing scene — no rebuild |
| FREQUENCY_HZ | 3602.5e6 | 3602 MHz |
| VEG_CONDUCTIVITY | 0.20 S/m | ITU-R P.833 at 3.6 GHz |
| DISABLE_VEG_DISCS | True | disc PLYs transparent |
| DISABLE_CANOPY | True | 3D canopy+trunk transparent — cones block all rays >400m at λ=8.3 cm |
| CAL_FIX_SCATTER | False | S free |
| CAL_SAMPLES_PS | 30_000_000 | 30M |
| CAL_MAX_DIST_KM | 1.0 | calibrate within LOS regime (Rbp=1225m at 3602 MHz) |
| CAL_MIN_DIST_KM | 0.15 | near-field exclusion |
| EVAL_MIN_DIST_KM | 0.15 | exclude near-field from stats |
| CAL_SCALAR_BOUNDS | (-60.0, 60.0) | Phase 0 finds +30 dB scalar — must cover it |
| NUM_SAMPLES_PS | 100_000_000 | 100M eval |

### 3602 MHz Calibration History

| Run | Settings | Phase 0 RMSE | Scalar | After-scalar RMSE | Notes |
|-----|----------|-------------|--------|-------------------|-------|
| Run 0 (aborted) | DISABLE_CANOPY=False, 10M | 46 dB | +30 dB | 29.5 dB | canopy cones blocked all rays >400m |
| Run 1 (aborted) | DISABLE_CANOPY=True, 10M | 31.4 dB | +21.2 dB | 23.1 dB | MC noise floor — flat at 21.574 dB from eval 2 |
| Run 2 (aborted) | DISABLE_CANOPY=True, 30M, bounds=(-30,20) | 47.2 dB | +30.0 dB (CLIPPED) | 31.6 dB | scalar capped at +20 — Phase 2 fights Phase 0 |
| **Run 3 (running)** | DISABLE_CANOPY=True, 30M, bounds=(-60,60) | TBD | TBD | TBD | correct bounds — Phase 2 free to optimise |

**Key findings so far:**
- DISABLE_CANOPY=True required — active canopy cones at λ=8.3 cm block all rays beyond 400m (RMSE=46 dB, scalar=+30 dB)
- +30 dB scalar is real physics gap — transparent canopy removes scattering; remaining paths are building reflections only
- CAL_SCALAR_BOUNDS=(-30,20) clips the scalar: Run 2 Phase 2 fought to reduce scalar from +30 toward +20, actively worsening cal
- 10M samples insufficient at 3602 MHz — MC noise floor ±0.21 dB prevents Powell finding gradient below 21.574 dB

### 3602 MHz Session Fixes (committed to claude/cool-cori-rrWbY)
| Commit | Fix |
|--------|-----|
| `ed841a6` | DISABLE_CANOPY=True in CELL 1 + conditional transparency in CELL 4A |
| `23075d2` | EVAL_MIN_DIST_KM=0.15 + CAL_SAMPLES_PS=30M |
| `8979235` | CAL_SCALAR_BOUNDS (-30,20) → (-60,60) — stops Phase 2 fighting Phase 0 |

---

## London 915 MHz Status (sionna2_915mhz_dem_simulation_london.ipynb)

**Calibration run as of 2026-08-06 — near termination (FTOL):**

| Phase | RMSE (dB) | Notes |
|-------|-----------|-------|
| TX AGL scan | AGL=45m selected | 92% valid paths (206/223); AGL=25m had only 52% — rejected by coverage filter |
| Phase 0 scalar | 13.547 dB | scalar=+12.253 dB |
| Phase 2 eval 1 (probe) | 10.145 dB | accidental good point from probe |
| Phase 2 evals 2-41 | 10.910-10.941 dB | oscillating — MC noise floor (37 params, 20M samples, ±0.21 dB noise) |
| Expected termination | ~10.9 dB cal RMSE | FTOL natural stop |

**London CELL CAL fixes (all committed):**

| Commit | Fix |
|--------|-----|
| `484ef6c` | TX AGL selection: added coverage filter TX_AGL_MIN_COVERAGE=0.80 — AGL=25m rejected (52% paths) |
| `7d928e7` | Phase 0 stale `_res_sf.fun` NameError |
| `a4ed73f` | Post-priming re-scalar stale `_res_pgs.fun` NameError |
| `011d92b` | Warm-prior `_res_wp.fun` + Phase 3 `_res_sf2.fun` NameErrors |

**London CELL 1 additions:**
```python
TX_AGL_SCAN_M       = [25, 30, 35, 40, 45]
TX_AGL_MIN_COVERAGE = 0.80   # min valid-path fraction for AGL selection
CAL_SCALAR_BOUNDS   = (-60.0, 60.0)
TX_CONDUCTED_DBM    = 49.0
```

**Expected CELL 8e (after London Powell terminates):**
- RMSE: ~7-9 dB at 0-750m (eval at 100M samples much better than cal RMSE)
- R²: ~0.35-0.45 at 0-750m (London has more NLOS + complex urban canyon)
- Eval at 100M samples needed before drawing conclusions

---

## Physics Floor Research — Key Literature Findings (2025)

### Root causes of 14-15 dB uncalibrated floor at 1802 MHz:

| Source | Magnitude | Fixable? |
|--------|-----------|---------|
| Missing dynamic clutter (cars, furniture) | ~4-6 dB | No — not in static scene |
| Uniform material assignment per type | ~6-12 dB | Partially — 5 categories already implemented |
| Antenna pattern uncertainty | ~2-4 dB | Requires measured pattern |

### Literature RMSE benchmarks (urban outdoor):
- **Wireless InSite** indoor: 5.0 dB @ 2.4 GHz, 5.1 dB @ 5 GHz (heavily material-dependent)
- **NYURay** calibrated outdoor: 3.2 dB LOS / 5.8 dB NLOS @ 6.75/16.95 GHz — uses per-building material classification from LiDAR
- **Sionna RT** at 2.8 GHz urban: significant improvement with photogrammetric point clouds + semantic segmentation (ground/buildings/vegetation/fences/cars)
- **R² ceiling**: ~0.5 for pure geometry+material calibration; ~0.7-0.8 requires hybrid RT+neural correction

### NVLabs calibration approaches (diff-rt-calibration repo):
- `ITU_Materials.ipynb` — scalar only (same as our Phase 0)
- `Learned_Materials.ipynb` — gradient descent on raw ε/σ/S (smoother than Powell, ~2-3 dB better)
- `Neural_Materials.ipynb` — NN parametrizes material properties (most expressive)
- `instant-rm/Calibration.ipynb` — Path Replay Backpropagation for city-scale fitting
- **All validated indoors (DICHASUS dataset, Stuttgart, 2.4 GHz) — not urban outdoor**

### Improvement options (post current-cal):

| Option | Expected gain | Complexity | Notes |
|--------|--------------|-----------|-------|
| N_AVG=2 in CELL CAL | -1 to -2 dB cal RMSE | Low — 1 config change | Halves MC noise variance |
| Gradient-based cal (diff-rt) | -2 to -3 dB vs Powell | High — new pipeline | Needs Sionna autograd enabled |
| Separate LOS/NLOS scalar | -1 to -2 dB eval RMSE | Medium — CELL 8e change | NYURay achieves 3.2/5.8 dB this way |
| Per-building material diversity | -1 to -2 dB | Very High — scene rebuild needed | Requires new scene builder (1802 MHz builder is FROZEN) |
| Hybrid RT+NN residual correction | R² 0.7-0.8 achievable | Very High — needs training data | Post-thesis research direction |

### Per-building material diversity — status:
Current scene already has 5 building PLY files (brick/concrete/glass/metal/wood) — one level of diversity. True per-building calibration (each building own material) requires scene builder changes. **1802 MHz scene builder is FROZEN — this cannot be implemented without a new builder.** Not recommended before seeing current cal CELL 8e results.

### Thesis References — Key Citations

#### Dual LOS/NLOS scalar justification
- **3GPP TR 38.901** (v18, 2024) — "Study on channel model for frequencies from 0.5 to 100 GHz." Defines separate LOS/NLOS path loss models, shadow fading σ (UMa NLOS: σ_SF=7.82 dB), and the breakpoint Rbp = 4·hBS·hUT·f/c. The dual-slope structure and LOS/NLOS separation implemented in CELL 8e are a direct application of this model.
- **ITU-R P.1411-12** (2019) — "Propagation data and prediction methods for the planning of short-range outdoor radiocommunication systems and radio local area networks." Defines the dual-slope breakpoint and separate LOS/NLOS exponents used to derive Rbp = 916m (2695 MHz) and 1225m (3602 MHz).
- **NYURay (Ju, Xing, Kanhere, Rappaport — NYU WIRELESS)** — Outdoor ray tracing validation at 6.75/16.95 GHz. Achieves 3.2 dB LOS / 5.8 dB NLOS RMSE using separate per-zone mean corrections and per-building material classification from LiDAR. Search: "NYURay calibrated outdoor" on IEEE Xplore.

#### Physics floor and RT calibration
- **arXiv:2507.19653** — Confirms R²~0.5 ceiling for pure geometry+material calibration in dense urban outdoor at 1.8 GHz. Cited as physics floor justification for 1802 MHz results.
- **NVLabs diff-rt-calibration** (Hoydis et al., NVIDIA) — `Learned_Materials.ipynb`, `Neural_Materials.ipynb`, `instant-rm/Calibration.ipynb`. Gradient-based and neural material calibration for Sionna RT. Validated indoors (DICHASUS dataset, Stuttgart, 2.4 GHz).
- **Wireless InSite** (Remcom) — Indoor RT benchmarks: 5.0 dB @ 2.4 GHz, 5.1 dB @ 5 GHz. Heavily material-dependent.

#### Vegetation attenuation
- **ITU-R P.833-10** (2021) — "Attenuation in vegetation." Formula: A = Am × (1 − exp(−d·γ/Am)); Am=25 dB, γ=2.0 dB/m at ~3 GHz. Used in CELL 8e for 2695/3602 MHz (replaces Weissberger which under-estimates ~40% above 2 GHz).
- **Weissberger (1982)** — Empirical vegetation attenuation model. Used in CELL 8e for 915/1802 MHz. Formula: A = 1.33·f^0.284·d^0.588 (dB) for d > 14m.

#### Material EM properties
- **ITU-R P.2040-2** (2021) — "Effects of building materials and structures on radiowave propagation." Brick σ = 0.038 S/m (frequency-independent). Corrects P.2040-1 (2015) over-calculation at 2695+ MHz.

---

## Current Scene State (snapshot)

### Features enabled
| Feature | PLY | Material |
|---------|-----|----------|
| Terrain | terrain.ply | itu_wet_ground / itu_medium_dry_ground |
| Buildings | bld_itu_brick/concrete/glass/metal/wood.ply | per-material |
| Roads | road_itu_asphalt.ply | itu_asphalt (er=2.56, locked) |
| Water (River Trent) | water_itu_water.ply | itu_water (er=80) |
| OSM/VOM vegetation | veg_itu_vegetation.ply | itu_vegetation (er=17, S=0.5) |
| Individual trees | trees_itu_vegetation.ply | itu_vegetation |
| nDSM extra vegetation | ndms_itu_vegetation_extra.ply | itu_vegetation |
| Bridges (man_made) | bld_itu_concrete_bridges.ply | itu_concrete |
| Highway bridges | infra_itu_concrete_hwy_bridges.ply | itu_concrete |
| Railways | rail_itu_metal.ply | itu_metal |
| Vegetation terrain | terrain_veg.ply | itu_vegetation (er=17, S=0) |

### RT parameters
| Parameter | Value |
|-----------|-------|
| MAX_DEPTH | 8 |
| NUM_SAMPLES_PS | 500,000 |
| diffraction | True |
| edge_diffraction | True |
| CAL_MAX_DIST_KM | 1.5 | auto-discover finds effective range from path coverage |
| VEG_DISC_SPACING_M | 20.0 |
| VEG_MAX_DISCS_PER_POLYGON | 500 |
| VEG_NDMS_EXTRA | True |
| VEG_NDMS_MIN_H_M | 2.0 |
| VEG_NDMS_EXTRA_RES_M | 10.0 |
| TERRAIN_GRID_N | 1000 |

---

## Results Reference

Best method across all runs: **ON incoh** (scattering ON, incoherent sum).

### Step 1 — Buildings + terrain only (depth=8, calibrated)
| Range | N | Bias (dB) | RMSE (dB) | R² |
|-------|---|-----------|-----------|-----|
| 0-300m | 26 | -3.7 | 6.0 | -0.020 |
| 0-500m | 44 | -5.8 | 8.4 | +0.337 |
| 0-750m | 67 | -2.6 | 7.9 | **+0.716** |
| 0-900m | 78 | -0.2 | 9.2 | +0.643 |
| 0-1000m | 87 | +0.9 | 9.3 | **+0.679** |
| 0-1250m | 168 | +6.0 | 12.8 | +0.496 |

### Full scene evolution (ON incoh, 0-750m / 0-1000m / 0-1250m R²)
| Scene | 0-750m | 0-1000m | 0-1250m | Notes |
|-------|--------|---------|---------|-------|
| Buildings only (d=8) | 0.716 | 0.679 | 0.496 | baseline |
| +grid disc veg (d=8) | 0.692 | 0.691 | 0.383 | |
| +roads+water+veg (d=8, all cal) | 0.696 | 0.609 | 0.401 | |
| +bridges+rails uncal (d=8) | 0.555 | 0.530 | 0.487 | before recal |
| Full scene cal d=8, 500k, 1km | 0.680 | 0.639 | 0.167 | scalar=-0.064 dB |
| Full scene cal d=8, 2M, 0.1km floor | 0.625 | 0.738 | 0.673 | 8.32 dB cal |
| Full scene cal d=8, 2M, 0.25km floor | 0.660 | 0.763 | 0.681 | 9.72 dB cal |
| Full scene cal d=8, 2M, 0.15km floor | 0.742 | 0.803 | 0.683 | 9.92 dB cal |
| **Full scene cal d=8, 100M eval, 0.15km floor** | **0.835** | **0.813** | **0.741** | **6.0 dB RMSE — best** |

> Best result: RMSE 6.0 dB @ 0-750m, CAL_MIN_DIST_KM=0.15, d=8, 100M eval samples.
> Full table (ON incoh, 100M samples): 0-300m R²=0.007 | 0-500m R²=0.664 | 0-750m R²=0.835 | 0-900m R²=0.797 | 0-1000m R²=0.813 | 0-1250m R²=0.741
> Bias: +0.8 dB @750m, +1.0 dB @1km — well-centred.
> Near-range (0-300m): R²~0 from 8 LOS mast-shadow receivers — structural, not a calibration issue.
> Key finding: 100M eval samples is optimal — 90M/200M give identical or slightly worse results.

---

## PERMANENT DO-NOT-TOUCH FILES (never edit, never patch, never modify under any circumstance)

- `sionna2_915mhz_dem_simulation.ipynb` — 915 MHz Nottingham simulation, FROZEN
- `sionna019_scene_builder.ipynb` — 915 MHz scene builder, FROZEN
- `sionna019_1802mhz_scene_builder.ipynb` — 1802 MHz scene builder, FROZEN

These files must never be opened for writing by Claude. Any task that would patch "all notebooks" must explicitly exclude these three files.

---

## Critical Rules (never break these)

1. **SCENE_WEST must match exactly** between scene builder and simulation notebook.
   - Current value: `SCENE_WEST = -1.267685` (both notebooks)
   - Mismatch of even 0.025° causes ~855m coordinate offset — buildings in wrong place.

2. **terrain.ply and building PLYs must share the same scene centre.**
   - If SCENE_WEST/EAST/SOUTH/NORTH changes, delete `terrain.ply` AND all `bld_*.ply` and rebuild both.
   - Never keep terrain.ply from a different bbox configuration.

3. **CELL 3 must always run after every kernel restart** — even when terrain.ply already exists.
   - It defines `center_utm`. CELL 4's terrain PLY interpolator needs it to convert BNG coords to scene-local.
   - CELL 3 skips the terrain rebuild (fast, ~2s) but still restores `center_utm`.

4. **Never change config without permission.** No bias tweaks, no hardcoded offsets.
   - All height caps must be None-aware: `_bld_cap = float(X) if X is not None else float('inf')`

5. **No automatic bbox from TX position.** `USE_GPS_CENTRE = False` always.
   - Scene extent must be independent of TX location.

6. **Do not delete calibration files between feature tests.**
   - Delete only when doing a full recalibration (CELL CAL) after scene geometry is stable.
   - Both files must be present together: scalar_offset + calibrated_materials.

---

## Pre-Rebuild Checklist

Before running CELL 3 + CELL 4 + CELL B3:

- [ ] Confirm `SCENE_WEST = -1.267685` in CELL 0 config
- [ ] Confirm `SCENE_WEST = -1.267685` in simulation notebook CELL 1
- [ ] Check `terrain.ply` was built with the **same** SCENE_WEST:
  ```python
  # Quick terrain bbox check (run in scene builder after CELL 0+1):
  import struct, numpy as np
  with open(os.path.join(MESH_DIR, 'terrain.ply'), 'rb') as f:
      n_verts = 0
      while True:
          line = f.readline().decode('ascii','ignore').strip()
          if line.startswith('element vertex'): n_verts = int(line.split()[-1])
          if line == 'end_header': break
      data = np.frombuffer(f.read(n_verts*12), dtype=np.float32).reshape(-1,3)
  expected_half_x = ((SCENE_EAST-SCENE_WEST)*111000*__import__('math').cos(__import__('math').radians((SCENE_NORTH+SCENE_SOUTH)/2)))/2
  actual_half_x = float(data[:,0].max())
  print(f'Expected X half-span: {expected_half_x:.0f} m')
  print(f'Actual   X half-span: {actual_half_x:.0f} m')
  print('OK' if abs(actual_half_x - expected_half_x) < 100 else 'MISMATCH — delete terrain.ply and rebuild CELL 3')
  ```
- [ ] Delete stale PLYs before rebuild:
  ```bash
  # Delete everything except terrain (if terrain bbox is confirmed correct):
  find ~/sionna_rt/nottingham_ofcom2018_915mhz_dem/scene_v4_full/meshes/ \
    -name "*.ply" ! -name "terrain.ply" -delete

  # If terrain bbox is wrong — delete terrain too:
  rm ~/sionna_rt/nottingham_ofcom2018_915mhz_dem/scene_v4_full/meshes/terrain.ply
  ```

---

## Cell Run Order

### Full rebuild from scratch
```
CELL 0 → CELL 1 → CELL 3 → CELL 3b → CELL 4 → CELL B3
```

### After kernel restart (terrain.ply exists)
```
CELL 0 → CELL 1 → CELL 3 (restores local_z, skips rebuild) → CELL 3b → CELL 4 → CELL B3
```

### After changing SCENE_WEST/EAST/SOUTH/NORTH
```
Delete terrain.ply + all bld_*.ply
CELL 0 → CELL 1 → CELL 3 (full rebuild) → CELL 3b → CELL 4 → CELL B3
```

### After calibration (apply + verify)
```
CELL 4A → CELL 8e
```

---

## Step-by-Step Scene Testing

Current config is **Full scene** (all features enabled).

| Step | Features | Status |
|------|----------|--------|
| 1 | Buildings + terrain | done — R²=0.716 @ 0-750m |
| 2 | + Vegetation (OSM + VOM + nDSM extra) | done |
| 3 | + Roads + water + bridges + railways | done |
| 4 | nDSM slab geometry (solid vertical boxes) | implemented |
| 5 | TERRAIN_GRID_N=1000 (finer terrain) | done |
| 6 | Road junction union fix (clean overlaps) | done — road_itu_asphalt.ply rebuilt |
| 7 | OS road polygons (true widths, OS Open Roads) | pending |

---

## Vegetation Architecture

Three complementary sources — together cover all green areas:

| Source | What it captures | Geometry |
|--------|-----------------|----------|
| OSM polygons | Parks, forests, scrub, named green areas | Discs (VEG_DISC_SPACING_M grid) |
| VOM polygons | LiDAR-detected canopy (EA data) | Discs (VEG_DISC_SPACING_M grid) |
| nDSM extra | Road verges, garden trees, motorway belts, M1 corridor | Discs (VEG_NDMS_EXTRA_RES_M grid) |
| Two-material terrain | Vegetation-covered ground (itu_vegetation, S=0) | DTM triangles in vegetation zones |

Key parameters:
- `VEG_DISC_SPACING_M = 20.0` — grid spacing for OSM/VOM discs
- `VEG_MAX_DISCS_PER_POLYGON = 500` — was 10 (caused M1 belt to get only 10 discs for 500m polygon)
- `VEG_NDMS_EXTRA_RES_M = 10.0` — grid spacing for nDSM extra discs
- `VEG_NDMS_MIN_H_M = 2.0` — minimum nDSM height to classify as vegetation

nDSM extra geometry: flat discs at canopy top — same as OSM/VOM approach.
Sionna RT uses surface interactions not volumetric absorption: discs scatter rays that hit them.
Weissberger model handles bulk attenuation (post-processing in CELL 8e).
Solid slabs rejected: Sionna has no path-integral absorption — a box just adds more scattering surfaces.

---

## Known Bugs Fixed

| Commit | File | Bug |
|--------|------|-----|
| `e410b9a` | scene builder CELL B3 | 17 `INCLUDE_` flags had no `_SKIP_PLY` guard — stale PLYs silently entered XML |
| `e410b9a` | scene builder CELL B3 | `surface_*_landuse.ply` has dynamic names — needed suffix-based skip |
| `e410b9a` | scene builder CELL 0 | `INCLUDE_FOOTWAYS`, `INCLUDE_GREENSPACES`, `INCLUDE_LANDUSE` missing from config |
| `2bdcec4` | scene builder CELL 4 | All 5 building height clips hardcoded — replaced with None-aware `_bld_cap` / `_veg_cap` |
| `285eb13` | simulation CELL CAL | Memory leak: PathSolver result not deleted — swap filled at ~680 evals |
| `6e2b4e2` | simulation CELL CAL | DrJIT kernel caching: flat RMSE across all evals — added 3-probe sensitivity check |
| `2bec77c` | scene builder CELL 4 | Buildings below ground: `local_z` unreliable — replaced with terrain PLY RegularGridInterpolator |
| `c1d08d3` | scene builder CELL 4 | VEG_MAX_DISCS_PER_POLYGON=10 capped large polygons (M1 belt) to 10 discs — now 500 |
| `c1d08d3` | scene builder CELL 4 | nDSM extra scan added — captures vegetation not in OSM/VOM (road verges, motorway belts) |
| `7c8bd5c` | CELL 8e | O(n_rx × 67292) Weissberger loop — replaced with STRtree spatial index |
| `1b02870` | scene builder CELL 3 | terrain_veg.ply moved from CELL 4 to CELL 3 (no full rebuild needed) |
| `5ad27dd` | 2695/3602 MHz CELL 4A | `float(_mat3d.relative_permittivity)` TypeError — replaced with `_safe_f()` for Sionna tensor unwrapping |
| `ff8168d` | 2695/3602 MHz CELL DIAG | `_near` NearestNDInterpolator shadowed by `_near = _df_meas[...]` DataFrame — renamed to `_df_near` |
| `dfaa2c2` | 2695/3602 MHz CELL 3 | `_terrain_interp` captured `_near` by global ref — fixed to default-arg capture (`_n=_near`) |
| `9bb6be0` | 2695/3602 MHz CELL 5 | Receivers selected before bbox filter — first 1200 rows all outside scene for routes starting far from TX |
| `5b35e4e` | 2695/3602 MHz CELL 5 | Receivers sorted by distance only, not sequential CSV order — fixed to filter near-TX section then `head(NUM_RX)` |
| `ed841a6` | 3602 MHz CELL 1 + CELL 4A | DISABLE_CANOPY=True — λ=8.3 cm canopy cones block all rays >400m; makes canopy+trunk transparent |
| `8979235` | 3602 MHz CELL 1 | CAL_SCALAR_BOUNDS=(-30,20) clips +30 dB Phase 0 scalar — Phase 2 fights Phase 0; widened to (-60,60) |
| `0fadb7c` | 2695/3602 MHz CELL 8e | Per-path P.833: `_apply_per_path_veg_8e()` attenuates each ray segment via `paths.vertices` — fixes NLOS receivers with zero per-receiver correction |
| `b15eb12` | 2695/3602 MHz CELL 8e | Double vegetation fix: `_apply_weissberger` skips if PER_PATH_VEG=True — per-receiver was applied after bin scalar (fit without Weissberger) → inconsistent pipeline |
| `b15eb12` | 2695/3602 MHz CELL 8e | Height filter: per-path skips segments where min(z0,z1) > 30m scene-local — paths above canopy level were incorrectly counted as traversing vegetation |
| `b15eb12` | 3602 MHz CELL 1 | N_SCALAR_BINS 5 → 10: finer binning better resolves sharp 700m NLOS transition |

---

## Permanently Ruled Out
| Approach | Reason |
|----------|--------|
| Disc PLYs (any S > 0) | Scatter flood 700×+ ON/OFF ratio |
| Disc PLYs S=0 | Over-blocking +7.7 dB |
| VEG_AUGMENT_TERRAIN | wet_ground S=0.30 → scatter flood |
| MAX_DEPTH > 8 | Extra bounces → spatial noise, R² drops to 0.555 |
| NUM_SAMPLES_PS > 2M | Calibration-evaluation mismatch |
| CAL_MIN_DIST_KM = 0.30 | Worse than 0.15km — Powell converges to ~12.7 dB, far above 0.15km record |
| MAX eval samples > 100M | No systematic gain — 90M/100M/200M statistically equivalent |
| CAL_MAX_DIST_KM = 1.25 | Too few receivers (166) — Powell finds bad local minimum (R²=0.200, scalar=+9.5 dB) |

---

## Calibration Files (local, not committed)

| File | Contents |
|------|----------|
| `scalar_offset_915mhz.json` | scalar_factor_db (currently running: -0.064 dB was last full-scene cal) |
| `calibrated_materials_915mhz.json` | ITU material parameters after Powell optimisation |

To reset calibration: delete both files and set `USE_CALIBRATED_FILES = False` in simulation CELL 1.

Calibration settings: NUM_SAMPLES_PS=2M, CAL_MIN_DIST_KM=0.15, CAL_MAX_DIST_KM=1.5.
CAL_MAX_DIST_KM=1.25 (166 RX) is worse — less receiver diversity causes Powell to find a bad local minimum (R²=0.200, scalar=+9.5 dB). Use 1.5 km (208 RX) for correct calibration.
Expected calibration RMSE floor: ~8-9 dB on calibration set (evaluation RMSE is much lower at 100M samples).

---

## Scene Parameters Reference

| Parameter | Value | Notes |
|-----------|-------|-------|
| `SCENE_WEST` | -1.267685 | must match simulation notebook |
| `SCENE_EAST` | -1.119832 | |
| `SCENE_SOUTH` | 52.943165 | |
| `SCENE_NORTH` | 53.003037 | |
| `CITY_MAX_HEIGHT_M` | 40.0 | nDSM artefact cap — do not set to None |
| `VEG_HEIGHT_CAP_M` | None | data-driven, no cap |
| `TERRAIN_GRID_N` | 1000 | 1000×1000 terrain mesh (~10m grid spacing) |
| `TERRAIN_PAD_M` | 3000 | terrain extends 3km beyond scene bbox |
| `origin_elev_asl_m` | 50.55 m | scene centre elevation (EA LiDAR DTM, confirmed) |
| `TX terrain_z` | 79.2 m | TX above scene datum — correct for western Nottingham high ground |
| `TX scene-local Z` | 96.2 m | terrain_z + TX_AGL_M (17m) |
| `PROJ_EPSG` | 27700 | British National Grid |
