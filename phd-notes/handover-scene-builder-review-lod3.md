# Handover: Scene Builder Review + Automatic LoD3 Module Proposal

> Context for continuing work in the chat where the Sionna OSM Scene Builder notebook (Stevenage / Ofcom 915 MHz) was developed.
> Findings come from reading the notebook code, not from running it. Verify each item.

---

## 0. Project Context (short)

- PhD: ray tracing path loss prediction, urban outdoor, Ofcom ITU-R drive test (449, 915, 1802, 2695, 3602, 5850 MHz)
- First LoD3 site: London Ofcom Tx at 51.5305, -0.13399 (BNG E 529533.7, N 182937.9, tile TQ28SE), Tx height 25 m, Eversholt Street / Euston area
- Plan: LoD3 zone Z1 = 400 m radius around Tx (facades facing driven streets + Tx building), LoD2 to 2 km, LoD1 beyond
- Facade imagery: Mapillary (CC BY-SA 4.0). Google Street View only for visual checks (terms prohibit extraction, detection, 3D modelling)
- Goal: build LoD3 automatically in Python (no Blender)

---

## 1. What the Notebook Already Does

- **Inputs:** EA LiDAR (DTM, DSM, VOM, point cloud, intensity), EA aerial RGBN + oblique photos, OSM, OS BHA, Microsoft / Overture footprints, EPC, NFI
- **Geometry:** terrain mesh, extruded buildings (LiDAR p95 heights), synthetic pitched roofs, roads, water, vegetation (disc / cap / shell), trees (cone + cylinder), infrastructure
- **Materials:** priority chain (oblique colour, OSM tags, EPC, use type, age, aerial RGB, LiDAR intensity); P.2040 parameters per frequency
- **Export:** Sionna 0.19 XML (differentiable calibration) and Sionna 2.0 XML

---

## 2. Issues to Fix Before Adding LoD3

1. **Near-TX height cap distorts geometry:** `TX_NEAR_HEIGHT_CAP_M = TX_AGL_M - 2` caps all buildings within `TX_NEAR_CAP_RADIUS_M = 400` m. In London (Tx 25 m) this lowers real buildings exactly where a ~24 dB excess loss near the Tx was measured (both 915 and 3602 MHz). Recommendation: disable for geometry accuracy studies (or make it an explicit ablation variant).
2. **PLY filename mismatches in `mat_plys` (CELL 4):**
   - fuel canopies: writes `infra_itu_metal_canopy.ply`, registers `infra_itu_metal_fuel_canopies.ply`
   - bus stations: writes `infra_itu_metal_busstation.ply`, registers `infra_itu_metal_bus_stations.ply`
   - rooftop equipment: writes `infra_itu_metal_rooftop.ply`, registers `infra_itu_metal_rooftop_equip.ply`
   - CELL B1 / B3 rebuild from disk (work); CELL 5 would reference missing files.
3. **CELL 2 guard bug:** `else: pass` does not wrap the AWS download code (unindented), so it runs even when `TERRAIN_SOURCE='ea_lidar'`.
4. **Inconsistent material tables:**
   - `itu_vegetation`: er = 1.5 (CELL 5) vs 17 (B1 / B3)
   - metal conductivity: 1e7 vs 1e4 in different cells
   - `itu_floorboard` defined twice in the B1 dict with different values (later silently wins)
   - Recommendation: one single material table module used by all cells.
5. **Proxy materials in Sionna 0.19:** water, vegetation, asphalt, barriers mapped to other ITU types (e.g. vegetation to ceiling_board). Radio properties are wrong unless the simulation notebook overrides them. Verify the override happens.
6. **Leftover Nottingham values:** `_TERRAIN_ASL = 12.0` in CELL 2oblique, plot titles, EPC fallback postcode list (London postcodes labelled "Stevenage").
7. **Roofs are synthetic:** pitched roofs from 30 degree default + centroid apex, not LiDAR roof planes. Describe as "pseudo-LoD2" in the thesis, or replace with LiDAR roof-plane reconstruction.
8. **Performance (minor):** CELL 3 terrain sampling loops N x N in Python (N = 1000 means 1e6 calls); vectorise with rasterio sampling.

---

## 3. Proposed Automatic LoD3 Module (no Blender)

Insert as a new stage after CELL 4 (e.g. `CELL 4-LoD3`), only for buildings inside the LoD3 zone.

| Step | What it does | Tools |
|---|---|---|
| 1. Facade extraction | Each footprint edge becomes a facade plane with local 2D frame (u = along wall, v = height) | shapely, numpy |
| 2. Image selection | Mapillary images whose camera pose (`computed_geometry`, `computed_rotation`) looks at the facade; filter by date (prefer 2016-2018 for Ofcom 2017) | Mapillary API v4 |
| 3. Rectification | Project facade corners into the image with `camera_parameters` + pose; homography to a metric frontal view (e.g. 100 px/m) | OpenCV |
| 4. Element detection | Windows, doors, balconies as rectangles (pretrained facade segmentation, e.g. trained on ZAHA / Mapillary Vistas) | PyTorch |
| 5. Regularisation | Snap to floor / column grids; merge detections from several images | numpy |
| 6. Geometry | Wall polygon minus window holes in 2D facade coords; triangulate with holes; reveal faces + glass panes at recess depth; balconies as boxes | shapely + `trimesh.creation.triangulate_polygon` |
| 7. Materials | Separate PLYs, e.g. `bld_itu_glass_windows.ply`, `bld_itu_concrete_balconies.ply`; register in `mat_plys` | existing pipeline |
| 8. QA | Watertight walls, no overlapping coplanar faces (LoD2 wall must be replaced, not duplicated), triangle budget | trimesh |

### Facade element table (intermediate output)
`building_id, facade_id, type, u_m, v_m, width_m, height_m, depth_m, material, image_id, image_date, confidence, source(image|procedural)`

### Fallback without imagery
Procedural "statistical LoD3": floors = height / 3 m; window-to-wall ratio from EPC glazing + building type. Must be flagged `source=procedural` and never silently mixed with image-derived LoD3.

### New config knobs (CELL 0)
- `LOD3_ENABLE`, `LOD3_ZONE_RADIUS_M = 400`, `LOD3_CORRIDOR_BUFFER_M = 30`
- `LOD3_DETAIL_THRESHOLD_M = 0.10` (frequency-linked; 10 cm for 5.85 GHz)
- `LOD3_DEFAULT_RECESS_M = 0.20`, `LOD3_IMAGE_DATE_RANGE = ('2016-01-01', '2018-12-31')`
- `LOD3_ALLOW_PROCEDURAL = False`

### Scene variants to generate (same origin, same materials)
V1 LoD1 / V2 LoD2 / V3 LoD3 corridor + Tx building / V3-noVeg / V3-TxLoD2 (isolates Tx rooftop effect)

---

## 4. Open Question for the Other Chat

Share the simulation notebook and `sionna019_differentiable_rt_fixed.ipynb` so the LoD3 module fits the calibration pipeline (material IDs, PLY naming, Sionna version target).
