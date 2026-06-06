# Sionna RT 900 MHz Experiment Plan — Nottingham

## Site Information
- **Country:** United Kingdom
- **City:** Nottingham, England (East Midlands)
- **Area:** Radford / Hyson Green — dense urban residential, north-west of city centre
- **Environment:** Urban macro-cell — TX mast above rooftops, omni antenna, surrounding terraced brick housing 2–3 floors
- **Terrain:** Rolling sandstone hills (~50m elevation change across scene)
- **Campaign:** Ofcom sub-6GHz propagation measurement 2018, published 2019
- **Frequency:** 915.95 MHz
- **TX AGL:** 17m (pump-up mast)

---

## Phase 1 — Flat Terrain (FLAT_TERRAIN = True)

### Step 1 — Verify scattering is working
- Re-run scene loading cell (CELL 9 in notebook)
- Check verification printout — all materials should show scattering_coefficient > 0:
  - brick: 0.25, concrete: 0.20, glass: 0.10, metal: 0.05
  - wet_ground: 0.40, very_dry_ground: 0.30
- If still showing [0] → patch XML before load_scene() (guaranteed fix)

### Step 2 — Verify TX/RX positions
- Run CELL 5c (position verification + 2D map)
- Confirm TX is NOT inside a building footprint
- Confirm first 50 RX are NOT inside building footprints
- If TX is inside building → correct TX_LON / TX_LAT in CELL 0 by a few metres
- Expected: near-range bias (-4 dB at <300m) should reduce once TX is correctly placed

### Step 3 — Run cumulative band analysis
- Run CELL 8 (scattering ON vs OFF, cumulative bands)
- Target metrics with scattering working:
  - 0–500m:  RMSE < 6 dB,  R² > 0.7
  - 0–1000m: RMSE < 9 dB,  R² > 0.5
  - 0–3000m: RMSE < 15 dB, R² > 0.4
- If SCAT ON still equals SCAT OFF → patch XML before load

### Step 4 — Tune MAX_DEPTH if needed
- Current: MAX_DEPTH = 8 (too high, contributes to long-range over-prediction)
- If RMSE at >1km still high after scattering fix → reduce to MAX_DEPTH = 5
- Do not reduce below 3 (loses key reflected paths in urban canyon)

### Step 5 — Final flat terrain results
- Run CELL 7 (full 1200 RX path solver)
- Run CELL 8 (cumulative band analysis — final)
- Save results to results/ folder
- Record: Bias, RMSE, MAE, R² per band for both SCAT ON and OFF

---

## Phase 2 — Real Terrain / DEM (FLAT_TERRAIN = False)

### Step 1 — Download EA LiDAR DTM
- In CELL 0: set `FLAT_TERRAIN = False`, `TERRAIN_SOURCE = 'ea_lidar'`
- Run CELL 2b (EA LiDAR auto-download, 1m DTM, UK only)

### Step 2 — Rebuild terrain PLY
- Run CELL 3 (terrain PLY with real elevation)

### Step 3 — Re-run path solver
- Run CELL 7 (full 1200 RX)
- Run CELL 8 (cumulative band analysis)

### Step 4 — Compare flat vs DEM
- Compare RMSE, MAE, R² per band between Phase 1 and Phase 2
- Expected improvement: 2–5 dB RMSE reduction at >1km due to terrain shadowing

---

## Current Results (Flat Terrain, Scattering Broken)

| Band    |  N  | Bias (dB) | RMSE | MAE  |   R²   |
|---------|-----|-----------|------|------|--------|
| 0–100m  |   8 |    +0.8   |  5.5 |  4.8 | -1.293 |
| 0–200m  |  17 |    -3.2   |  6.4 |  5.9 | -2.162 |
| 0–300m  |  26 |    -4.0   |  6.6 |  5.8 | -0.228 |
| 0–500m  |  44 |    -4.2   |  7.1 |  5.9 |  0.524 |
| 0–750m  |  67 |    +0.7   | 10.6 |  8.8 |  0.489 |
| 0–900m  |  78 |    +0.6   | 10.6 |  8.9 |  0.528 |
| 0–1000m |  87 |    +0.0   | 11.5 |  9.7 |  0.511 |

**Key observations:**
- Scattering ON = Scattering OFF (scattering_coefficient was 0 on all materials — now fixed)
- Negative R² at <300m → simulation does not capture near-field variability (building blockage)
- Bias flips from negative (<500m) to positive (>500m) → possible TX position offset

---

## R² Formula (for Excel)

```
R² = 1 - SUMXMY2(sim_range, meas_range) / DEVSQ(meas_range)
```

- `sim_range`  = column of simulated RSSI (dBm)
- `meas_range` = column of measured RSSI (dBm)
- R² = 1.0 → perfect | R² = 0.0 → no better than mean | R² < 0 → worse than mean
