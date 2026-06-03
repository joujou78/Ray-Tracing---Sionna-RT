# Sionna RT Notebook — Debugging & Architecture Reference

Use this skill when diagnosing freezes, errors, or performance issues in
`sionna019_main_simulation.ipynb`.

---

## Pipeline Cell Map

| Cell | Name | What it does |
|------|------|-------------|
| 1–2 | Imports / Config | Loads libraries, sets `ACTIVE_CITY` |
| 3 | OSM Buildings | Fetches buildings, applies LiDAR heights from Cell 3b |
| 3a | DEM Build | `gdalbuildvrt` + `gdal_translate` merges DTM tiles → `DEM_TIFF` |
| 3b | LiDAR Refinement | Samples DSM−DTM per building, updates `gdf['height']` |
| 4 / Cell 21 | OSM Enrichment | Adds trees, walls, water, bridges, fences via Overpass |
| 5+ | Ray Tracing | RX placement, Sionna simulation, path loss export |

---

## Known Freeze: Enrichment Cell (Cell 4 / Cell 21)

### Symptom A — stuck at element 0
```
Building spatial index: 52248 footprints indexed
Processing elements 0/59088 ...
```
Hangs here indefinitely.

**Root cause:** `_add()` called `_merge()` which did `list_a + list_b` —
copies the **entire accumulated vertex list on every call**. After the first
large woodland polygon generates ~2000 tree cylinders, subsequent calls copy
tens of thousands of items. O(N²) total work.

**Fix applied (committed):**
```python
# BEFORE (O(N²)):
def _add(mat, V, F):
    if not V: return
    ev, ef = _geom[mat]
    _geom[mat] = _merge(ev, ef, V, F)   # _merge does list_a + list_b

# AFTER (O(1) amortised):
def _add(mat, V, F):
    if not V: return
    ev, ef = _geom[mat]
    off = len(ev)
    ev.extend(V)
    ef.extend((f[0]+off, f[1]+off, f[2]+off) for f in F)
```

### Symptom B — very slow progress through elements
Each 5000-element batch takes minutes instead of seconds.

**Root cause:** `_random_fill()` used a pure Python double loop for
point-in-polygon (ray casting):
```python
for cx, cy in cands:          # N_candidates
    for k in range(nv):       # N_polygon_vertices
        ...
```
For large woodland polygons (many vertices, many trees) this is millions of
Python iterations.

**Fix applied (committed):**
```python
def _random_fill(nodes_local, density_ha, rng):
    if len(nodes_local) < 3: return []
    pts = np.array(nodes_local, dtype=np.float64)
    xmin, ymin = pts.min(0); xmax, ymax = pts.max(0)
    area_ha = (xmax - xmin) * (ymax - ymin) / 10_000
    if area_ha > 200:          # skip enormous polygons (national parks)
        return []
    n_trees = min(2000, max(1, int(area_ha * density_ha)))
    n_cand  = min(n_trees * 4, 8000)
    cands   = rng.uniform([xmin, ymin], [xmax, ymax], (n_cand, 2))
    ax = pts[:, 0]; ay = pts[:, 1]
    bx = np.roll(ax, -1); by = np.roll(ay, -1)
    cx = cands[:, 0, None]; cy = cands[:, 1, None]   # (N,1) broadcast over (nv,)
    with np.errstate(invalid='ignore', divide='ignore'):
        cross = (((ay > cy) != (by > cy)) &
                 (cx < (bx - ax) * (cy - ay) / (by - ay + 1e-12) + ax))
    mask = cross.sum(axis=1) % 2 == 1
    return [tuple(p) for p in cands[mask][:n_trees]]
```
Key changes: numpy (N_cand × N_verts) broadcast replaces Python loop;
200 ha cap skips national-scale polygons.

---

## City Config Structure (`_CITY_CONFIGS` in Cell 8)

Each city dict requires:

```python
'CityName': dict(
    city_name    = 'CityName',
    scene_west/east/south/north = ...,   # bounding box (decimal degrees)
    base_dir     = '~/Documents/FYP2026/<city>',
    tx_lon       = ..., tx_lat = ...,    # transmitter GPS
    tx_height_m  = ...,                  # mast height above ground
    tx_power_dbm = ...,
    tx_ant_gain  = ..., tx_cable = ...,
    rx_ant_gain  = ..., rx_cable = ...,
    lna_gain     = ..., rx_bpf  = ...,
    noise_floor  = ...,
    frequency_hz = ...,
    site_corr_db = 0.0,                  # recalibrate after Cell 9d
    dem_tif      = '~/Documents/FYP2026/<city>/dem/<city>_dtm.tif',
    meas_csv     = '~/Documents/FYP2026/<city>/measurements_with_pathloss.csv',
    rx_file      = '~/Documents/FYP2026/<city>/receiver_locations.csv',  # optional
)
```

Switch city with one line in Cell 8:
```python
ACTIVE_CITY = 'London'   # 'Nottingham' | 'Boston' | 'London'
```

---

## LiDAR / DEM Setup (England — Environment Agency)

**Download:** `https://environment.data.gov.uk/DefraDataDownload/?Mode=survey`
Select *LIDAR Composite DTM* and *LIDAR Composite DSM*, draw AOI bounding box.

**File layout:**
```
BASE_DIR/
└── lidar/
    ├── *DTM*.tif   ← bare-earth terrain (auto-discovered by Cell 3a + 3b)
    └── *DSM*.tif   ← surface with buildings/trees (auto-discovered by Cell 3b)
```

**Cell 3a** — merges all `*DTM*.tif` tiles into `DEM_TIFF` using GDAL:
```
gdalbuildvrt /tmp/dtm_mosaic.vrt <tiles>
gdal_translate -of GTiff /tmp/dtm_mosaic.vrt <DEM_TIFF>
```
Only runs if `DEM_TIFF` is absent or < 10 MB. Skip if already built.

**Cell 3b** — refines `gdf['height']` using `DSM − DTM` per building footprint.
Run this **between Cell 2 and Cell 3**, then re-run Cell 3 to regenerate PLYs.

**City AOIs (approx):**

| City | West | East | South | North |
|------|------|------|-------|-------|
| Nottingham | -1.45 | -1.21 | 52.92 | 53.00 |
| Boston (Lincs) | -0.19 | -0.16 | 52.92 | 52.93 |
| London | -0.16 | -0.03 | 51.49 | 51.57 |

---

## Healthy Enrichment Output (Nottingham reference)

```
Merged total: ~59082 elements
Building spatial index: 52248 footprints indexed
Processing elements 0/59082 ...   ← should reach 59082 in < 2 min
...
Geometry summary:
  enrich_vegetation.ply   1521256 verts  2471744 faces
  enrich_brick.ply          12688 verts     9516 faces
  enrich_concrete.ply       11524 verts     8238 faces
  enrich_water.ply           8900 verts     8587 faces
  enrich_metal.ply          75657 verts    61167 faces
scene.xml patched: +5 enrichment PLY shape(s)
```

If enrichment PLY vertex counts are orders of magnitude lower, check that
ENRICH_WOODLAND / ENRICH_TREES flags are True and that Overpass returned data.

---

## Overpass Mirror Fallback

Cell 4 queries two Overpass endpoints. 406/504/403 errors are normal —
the code retries across mirrors automatically. As long as one mirror
succeeds the data is complete. No action needed.

---

## Run Order After a Fresh Pull

1. Cell 1–2 (imports + config)
2. Cell 3a (build DEM — skip if DEM_TIFF already exists and > 10 MB)
3. Cell 2 / Cell 3 (OSM buildings)
4. Cell 3b (LiDAR height refinement — optional but recommended)
5. Cell 3 again if Cell 3b ran
6. **Cell 4 / Cell 21** (enrichment — this is the cell that was freezing)
7. Cell 5+ (ray tracing)
