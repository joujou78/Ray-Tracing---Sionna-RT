# Nottingham Sionna RT Diagnostic Report — Working Notes
**Date:** 2026-06-03  
**Simulation:** sionna019_main_simulation.ipynb  
**Scene:** Nottingham, UK | TX: 52.9863°N, -1.2559°E | Freq: 3602.5 MHz  
**Dataset:** 4000 Ofcom drive-test RSSI measurements  

---

## Configuration (Cell 8)
| Parameter | Value |
|-----------|-------|
| TX_CONDUCTED_DBM | 45.0 dBm |
| RX_EXTRA_GAIN_DB | 18.0 dB |
| SITE_CORRECTION_DB | 0.0 dB |
| TX_AGL_M | 30.0 m |
| DSM_HEIGHT_PERCENTILE | 75 (under test → 70) |
| TX scene-local Z | 95.4 m (terrain 65.4m + 30m AGL) |

---

## RSSI Formula (confirmed correct)
```
RSSI = TX_CONDUCTED_DBM + 10·log10(Σ|paths.a|²) + RX_EXTRA_GAIN_DB + SITE_CORRECTION_DB
```
- `paths.a` = normalized channel coefficient (Sionna 0.19.2)
- TX power applied in post-processing only — do NOT set `tx.power`
- Confirmed at 11m: simulated -30.2 dBm vs measured -29.7 dBm → **error = -0.5 dB** ✅

---

## DIAG STEP 1 — Path Loss Sanity Check
Near receivers (50–300m), Mean PL-FSPL = **+11.3 dB** (expected +5 to +15 dB for urban LOS) ✅

Key near-LOS measurements that constrain scene geometry:
| Receiver | Distance | Measured RSSI | PL-FSPL | Condition |
|----------|----------|--------------|---------|-----------|
| RX_058059 | 176m | -17.8 dBm | -0.7 dB | Essentially free-space LOS |
| RX_058060 | 180m | -19.4 dBm | +0.7 dB | Essentially free-space LOS |
| RX_058054 | 167m | -21.3 dBm | +3.3 dB | Near-LOS |
| RX_058055 | 167m | -22.9 dBm | +4.8 dB | Near-LOS |
| RX_058056 | 167m | -24.8 dBm | +6.7 dB | Near-LOS |

---

## DIAG STEP 4 — Simulation vs Measurement Error by Band

| Band | Path count | Sim error | Verdict |
|------|-----------|-----------|---------|
| 11–13 m | 3893–4078 | -0.5 to +8.6 dB | ✅ Formula correct |
| 167–185 m | 0–20 | -32 to -50 dB | ❌ LOS blocked — scene geometry |
| 300–327 m | 3–10 | -9 to -26 dB | ❌ Residual shadowing |
| 703–724 m | 10–15 | -15 to -28 dB | ❌ Accumulated shadowing |
| 1202 m | 0 | NaN | ⚠ Outside scene RT radius |

---

## CELL SIGHTLINE — Root Cause Identified

### Near-field blockage (167–185m, az≈55° NE)

All three near-field receivers blocked by the **same building row** at 125–135m from TX:

| Receiver | Distance | Clearance at blocker | Blocked by |
|----------|----------|---------------------|-----------|
| RX_058056 | 167m | -0.32m at 125m | **32 cm** |
| RX_058059 | 176m | -0.06m at 132m | **6 cm** |
| RX_058060 | 180m | -0.27m at 135m | **27 cm** |

Blocker building properties:
- **Location:** ~125–135m from TX, azimuth 55° NE
- **Roof_Z:** 75.70m scene-local (consistent from 27m to 130m along path → large building row)
- **Terrain at blocker:** ~65.4m → **building height ≈ 10.3m** (~3 storeys, Victorian terrace row)
- This is the same 75.70m rooftop cluster visible in STEP 3 TX surroundings (N/NE/E at 50m)

**Conclusion:** The LOS ray is geometrically blocked by 6–32 cm. This is a real building (not an OSM error). The DSM P75 percentile assigns 10.3m to this building; P70 would reduce it to ~9m, providing +1.2m clearance.

### 325m receiver (az=74.6°)
- Blocked at 244m by Roof_Z=75.58m (different building, same height band)
- Clearance: -0.42m

### 703m receiver (az=87.6°)
- Intermittent blockage at 562m (Roof_Z=69.99m, -1.85m) and 632m (Roof_Z=68.66m, -3.93m)
- These are smaller buildings (~4–5m) on terrain that drops from 65m to 60m
- Less critical — ray is clear for majority of 703m path

---

## Research Summary — Sionna RT at Macro Cell Scale

From community practice, GitHub Issues, and arXiv papers:

| Use case | Typical scene radius | Approach |
|----------|---------------------|----------|
| Single-TX, single GPU | 300–700m | Direct RT |
| City scale | 512×512m tiles | NVlabs/sionna-large-radio-maps |
| Our Nottingham scene | ~1000m | At single-GPU practical limit |

Key finding (arXiv 2507.19653, Rome study): **Antenna placement and scene fidelity matter 5–130× more than `max_depth` or `num_samples`.** Increasing ray count does not fix geometry errors.

Official NVIDIA production parameters (`sionna-large-radio-maps`):
```python
max_depth          = 6
min_samples_per_tx = 20_000_000
cm_cell_size       = [5, 5]   # to 100m for large scenes
tx_search_distance = 2000     # m beyond tile boundary
```

Our config (30M samples, depth=6) is above the minimum ✅

**1202m receivers:** Outside practical single-GPU RT envelope (≥1km). Industry solution is tiling, not larger scene. Recommend excluding from RMSE comparison and documenting as out-of-range.

---

## Bugs Fixed This Session

| Bug | Impact | Fix |
|-----|--------|-----|
| `_dem_z2()` returned 0.0 ASL on DEM miss | Buildings placed at -64m (underground) | Fallback to `origin_elev2` |
| DIAG STEP 4 used stale CSV z_m for RX height | False -3.3 dB result (RX 60m above buildings) | Priority 0: use `scene.receivers` position |
| DIAG Priority 3 returned ASL as scene-local | RX placed 64m too high | Subtract `_SCENE_ORIGIN_ELEV` |
| Cell CAL RSSI used EIRP+SYS_GAIN | Wrong formula | Use TX_CONDUCTED + RX_EXTRA_GAIN |
| Cell 36 CSV height (17m) overrode config (30m) | TX at 82.4m instead of 95.4m | Sync CSV from config at Cell 36 start |
| Cell 36 summary showed TX_AGL_M regardless of actual Z | Masked the 17m vs 30m bug | Summary now reads from `tx.position[2]` |
| CELL SIGHTLINE hardcoded to RX_085xxx | "not in scene" error | Updated to RX_058xxx |

---

## Proposed Fix Sequence

### Step 1 — Lower DSM_HEIGHT_PERCENTILE to 70
- In Cell 8: `DSM_HEIGHT_PERCENTILE = 70`
- Run Cell 3b → verify mean building height drops from 6.5m to ~5.5m
- Run Cell 3 (scene rebuild)
- Run CELL SIGHTLINE → 125–135m rows should show `Clear > 0`
- Run CELL DIAG → 167m band should improve from -47 dB to < -15 dB

### Step 2 — If near-field error still > -15 dB: raise TX_AGL_M = 33m
- Additional +2.6m ray clearance at the 125m blocker
- Re-run Cell 36 → CELL DIAG

### Step 3 — Exclude 1202m receivers from RMSE
- Add to Cell 8: `MAX_COMPARISON_DIST_M = 1000`
- Document as outside RT validation envelope

### Step 4 — Run full path solver (Cell 9b) and Cell CAL
- Once geometry is validated (near-field error < -10 dB)
- Full 4000-point RSSI map comparison

---

## Expected Outcome After Fixes

| Band | Current error | Expected after P70 |
|------|-------------|-------------------|
| 11–13m | -0.5 to +8.6 dB | No change (already good) |
| 167–185m | -32 to -50 dB | < -15 dB (LOS unblocked) |
| 300–327m | -9 to -26 dB | -5 to -15 dB |
| 703–724m | -15 to -28 dB | -10 to -20 dB |
| Overall RMSE target | — | < 15 dB |

Target from calibration guide: near-field mean error in **[-5, +5] dB** range.
