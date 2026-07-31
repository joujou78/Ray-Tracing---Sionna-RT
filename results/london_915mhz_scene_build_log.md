# London 915 MHz Scene Build Log

**Date:** 2026-07-31
**Frequency:** 915.95 MHz
**Dataset:** Ofcom London 915 MHz
**Scene builder:** `sionna019_scene_builder_london.ipynb`
**Simulation:** `sionna2_915mhz_dem_simulation_london.ipynb`

---

## Scene Configuration

| Parameter | Value |
|-----------|-------|
| SCENE_WEST | -0.222130 |
| SCENE_EAST | -0.085831 |
| SCENE_SOUTH | 51.506392 |
| SCENE_NORTH | 51.602239 |
| CRS | EPSG:27700 (BNG), always_xy=True |
| FREQUENCY_HZ | 915.95e6 |
| Terrain provider | ea_lidar |
| nDSM provider | ea |
| Terrain grid | 1000×1000 |
| Scene size | 9.18 km × 10.90 km (~100 km²) |
| Scene centre (WGS84) | -0.15405°, 51.55434° |
| BNG SW | 523485.4, 180104.8 |
| BNG NE | 532665.2, 191001.9 |

---

## Data Sources

| Source | Status | Notes |
|--------|--------|-------|
| EA LiDAR DTM | OK | 35000×35000 px, 1m res, EPSG:27700 |
| EA LiDAR DSM + nDSM | OK | Already existed, skipped recompute |
| EA VOM (WCS) | BLANK | WCS returned all-zero raster for London area |
| EA VOM (zip tiles) | **OK** | 13 tiles extracted from `national_lidar_programme_vom-*.zip` |
| VOM vegetation polygons | **OK** | 277,538 polygons |

### DTM Coverage Check (CELL 2c)
```
File       : dem.tif
CRS        : EPSG:27700
Size       : 35000 x 35000 px   res (1.0, 1.0)
Bounds WGS84: lon[-0.417941, 0.100035]  lat[51.455417, 51.777867]
AOI    WGS84: lon[-0.222130, -0.085831]  lat[51.506392, 51.602239]
COVERS AOI : YES
NoData frac (within AOI): 0.0%
Elev range (within AOI): -31.4 .. 137.0 m ASL
```

### VOM Merge (CELL 2vom-merge)
```
Valid VOM pixels: 30,967,485
Merged vom.tif: 15000×25000 px
Height range: 2.5 - 69.9 m
```

### VOM Vectorisation (CELL 2vom_poly)
```
pixel size   : 1.00 m
min height   : 2.76 m
min area     : 9.0 m²
VOM mask     : 29,419,089 pixels
pc_bld excl  : 15,396 confirmed-building pixels removed
polygons     : 277,538 clean vegetation polygons
tall (trees) : 277,538  |  low (ground veg): 0
height p50   : 7.2 m  |  p95: 15.5 m  |  max: 68.3 m
```

### Auto-derived Height Caps (CELL 2h)
```
VEG_HEIGHT_CAP_M  = 17.5 m  (VOM p95 of 1,936,313 vegetation pixels)
CITY_MAX_HEIGHT_M = 73.2 m  (nDSM p99.9 of 14,434,242 pixels > 3 m)
```

---

## Features Enabled (matching 1802 MHz scene)

| Feature | Status |
|---------|--------|
| 3D cone+cylinder tree model | TREE_MODEL='cone_cylinder' |
| LiDAR crown detection | LIDAR_TREES_FROM_NDSM=True, up to 15,000 trees |
| nDSM extra vegetation | VEG_NDMS_EXTRA=True |
| All road width types | including *_link, living_street |
| OS Open Roads support | OS_OPEN_ROADS_GPKG=None (plug in when available) |
| VOM vegetation polygons | 277,538 polygons from EA zip tiles |
| 915 MHz material values | VEG_CONDUCTIVITY=0.05, FREQUENCY_HZ=915.95e6 |

---

## Bugs Fixed During Build

| Fix | Description |
|-----|-------------|
| Bbox mismatch | Simulation had W=-0.231017 vs scene builder W=-0.222130 — fixed to match |
| VOM empty raster | EA WCS returns blank — CELL 2vom-merge added to handle zip tiles |
| CELL 2vom_poly empty array | `np.percentile` on empty `_valid` — added guard + graceful SystemExit(0) |

---

## Next Steps

1. Run optional data cells (CELL 2d-bha, CELL 2d-nfi, CELL 2d-conservation) — or skip
2. **CELL 3** — terrain PLY build (~10-20 min)
3. **CELL 4** — buildings + roads + trees + vegetation
4. **CELL B3** — XML scene assembly
5. Switch to simulation notebook: CELL 1 → CELL 2 → CELL 3 → CELL 4A → CELL 8e

---

## Notes

- VOM via EA WCS is blank for London — always use zip tile approach (CELL 2vom-merge)
- 277,538 VOM polygons gives excellent vegetation coverage for London parks + street trees
- CITY_MAX_HEIGHT_M=73.2m covers London tall buildings (City, Canary Wharf area)
- VEG_HEIGHT_CAP_M=17.5m appropriate for London street trees and parks
