# Sionna RT — Nottingham 915 MHz Scene: Session Reference

## Project Overview
Ray tracing simulation of the Ofcom 2018 Nottingham 915 MHz dataset using Sionna 2.0.
- Scene builder: `sionna019_scene_builder.ipynb`
- Simulation: `sionna2_915mhz_dem_simulation.ipynb`
- CRS: **EPSG:27700 (British National Grid)**, always_xy=True — never UTM
- Scene directory: `~/sionna_rt/nottingham_ofcom2018_915mhz_dem/scene_v4_full/`
- Working branch: `claude/cool-cori-rrWbY`

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
| CAL_MAX_DIST_KM | 1.25 | hard ceiling — do not extend to 1.5 km (Powell diverges on hard receivers) |
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
| CAL_MAX_DIST_KM = 1.5 | Powell diverges — 1387 evals, only 1.06 dB improvement, bad material params |

---

## Calibration Files (local, not committed)

| File | Contents |
|------|----------|
| `scalar_offset_915mhz.json` | scalar_factor_db (currently running: -0.064 dB was last full-scene cal) |
| `calibrated_materials_915mhz.json` | ITU material parameters after Powell optimisation |

To reset calibration: delete both files and set `USE_CALIBRATED_FILES = False` in simulation CELL 1.

Calibration settings: NUM_SAMPLES_PS=2M, CAL_MIN_DIST_KM=0.15, CAL_MAX_DIST_KM=1.25 (hard ceiling).
CAL_MAX_DIST_KM=1.5 caused Powell divergence (1387 evals, only 1.06 dB improvement, R²=-1.77 at 0-500m).
Expected calibration RMSE floor: ~10-11 dB on calibration set (evaluation RMSE is much lower at 100M samples).

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
