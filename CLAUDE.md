# Sionna RT — Nottingham 915 MHz Scene: Session Reference

## Project Overview
Ray tracing simulation of the Ofcom 2018 Nottingham 915 MHz dataset using Sionna 2.0.
- Scene builder: `sionna019_scene_builder.ipynb`
- Simulation: `sionna2_915mhz_dem_simulation.ipynb`
- CRS: **EPSG:27700 (British National Grid)**, always_xy=True — never UTM
- Scene directory: `~/sionna_rt/nottingham_ofcom2018_915mhz_dem/scene_v4_full/`
- Working branch: `claude/cool-cori-rrWbY`

---

## Results Reference

Best method across all runs: **ON incoh** (scattering ON, incoherent sum).

### Step 1 — Buildings + terrain only (ON incoh, uncalibrated)

| Range | N | Bias (dB) | RMSE (dB) | R² | Notes |
|-------|---|-----------|-----------|-----|-------|
| 0-500m | 44 | -8.1 | 10.9 | -0.107 | |
| 0-750m | 67 | -3.1 | 11.0 | +0.447 | |
| 0-900m | 78 | -1.1 | 12.0 | +0.394 | |
| 0-1000m | 87 | +0.6 | 12.6 | +0.416 | near-zero bias |
| 0-1250m | 173 | +8.9 | 17.9 | +0.006 | |

> **Pre terrain-fix baseline** (building bases at Z=0, not terrain-anchored).
> Rerun after terrain-height bug fixes for corrected Step 1 baseline.

### Step 2 — + Vegetation / trees (ON incoh, uncalibrated)

| Range | N | Bias (dB) | RMSE (dB) | R² | Notes |
|-------|---|-----------|-----------|-----|-------|
| 0-300m | 26 | +6.1 | 11.6 | -2.795 | |
| 0-500m | 44 | +9.6 | 15.3 | -1.172 | |
| 0-750m | 67 | +15.2 | 21.0 | -1.016 | |

> Pre terrain-fix, building bases Z=0. Growing positive bias at long range.

### Step 3 — Full scene

| Step | Scene | Bias (dB) | RMSE (dB) | R² |
|------|-------|-----------|-----------|-----|
| 3 | + Roads / water / bridges / railways | TBD | TBD | TBD |

**Important:** The previously reported R²=0.601 was computed with a stale terrain.ply
built at SCENE_WEST=-1.293205 (852m wrong centre). All prior step results are invalid.
Current confirmed state (terrain bbox check passed, 4941m half-span):
- TX at (-1.2559, 52.9863): terrain_z=79.2m, tx_z=96.2m (correct — western Nottingham high ground)
- origin_elev_asl = 50.55m ASL (EA LiDAR DTM at scene centre)
- Step 1 must be rerun with full accuracy data (PC + oblique now confirmed present)

---

## Critical Rules (never break these)

1. **SCENE_WEST must match exactly** between scene builder and simulation notebook.
   - Current value: `SCENE_WEST = -1.267685` (both notebooks)
   - Mismatch of even 0.025° causes ~855m coordinate offset — buildings in wrong place.

2. **terrain.ply and building PLYs must share the same scene centre.**
   - If SCENE_WEST/EAST/SOUTH/NORTH changes, delete `terrain.ply` AND all `bld_*.ply` and rebuild both.
   - Never keep terrain.ply from a different bbox configuration.

3. **CELL 3 must always run after every kernel restart** — even when terrain.ply already exists.
   - It defines `local_z` from `dem.tif`. Without it, CELL 4 falls back to Z=0 for all building bases.
   - CELL 3 skips the terrain rebuild (fast, ~2s) but still restores `local_z`.

4. **Never change config without permission.** No bias tweaks, no hardcoded offsets.
   - All height caps must be None-aware: `_bld_cap = float(X) if X is not None else float('inf')`

5. **No automatic bbox from TX position.** `USE_GPS_CENTRE = False` always.
   - Scene extent must be independent of TX location.

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

---

## Step-by-Step Scene Testing

Current config is **Step 1: buildings only** (all non-building INCLUDE_ flags = False).

| Step | Features | Flags to set True |
|------|----------|-------------------|
| 1 | Buildings + terrain only | *(all False — current)* |
| 2 | + Vegetation / VOM / trees | `INCLUDE_VEGETATION=True`, `INCLUDE_TREES=True` |
| 3 | + Roads / water / bridges / infra | `INCLUDE_ROADS=True`, `INCLUDE_WATER=True`, `INCLUDE_BRIDGES=True`, `INCLUDE_HWY_BRIDGES=True`, `INCLUDE_RAILWAYS=True` |

For each step: change flags in CELL 0 → delete non-terrain PLYs → CELL 4 → CELL B3 → CELL 4A → CELL 8e.

**Calibration**: use the **same `scalar_factor_db`** across all steps (do not re-run CELL CAL between steps). This isolates geometry effects.

---

## Known Bugs Fixed

| Commit | File | Bug |
|--------|------|-----|
| `e410b9a` | scene builder CELL B3 | 17 `INCLUDE_` flags had no `_SKIP_PLY` guard — stale PLYs from old builds silently entered XML |
| `e410b9a` | scene builder CELL B3 | `surface_*_landuse.ply` has dynamic names — needed suffix-based skip |
| `e410b9a` | scene builder CELL 0 | `INCLUDE_FOOTWAYS`, `INCLUDE_GREENSPACES`, `INCLUDE_LANDUSE` missing from config (defaulted True silently) |
| `2bdcec4` | scene builder CELL 4 | All 5 building height clips hardcoded — replaced with None-aware `_bld_cap` / `_veg_cap` |
| `285eb13` | simulation CELL CAL | Memory leak: PathSolver result not deleted — swap filled at ~680 evals |
| `6e2b4e2` | simulation CELL CAL | DrJIT kernel caching: flat RMSE across all evals — added 3-probe sensitivity check |

---

## Calibration Files (local, not committed)

| File | Contents |
|------|----------|
| `scalar_offset_915mhz.json` | scalar_factor_db = +8.093 dB (full scene) |
| `calibrated_materials_915mhz.json` | ITU material parameters after Powell optimisation |

To reset calibration: delete both files and set `USE_CALIBRATED_FILES = False` in simulation CELL 1.

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
| `TERRAIN_GRID_N` | 500 | 500×500 terrain mesh (~20m grid spacing) |
| `TERRAIN_PAD_M` | 3000 | terrain extends 3km beyond scene bbox |
| `origin_elev_asl_m` | 50.55 m | scene centre elevation (EA LiDAR DTM, confirmed) |
| `TX terrain_z` | 79.2 m | TX above scene datum — correct for western Nottingham high ground |
| `TX scene-local Z` | 96.2 m | terrain_z + TX_AGL_M (17m) |
| `PROJ_EPSG` | 27700 | British National Grid |
