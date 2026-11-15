# Per-Building Material Classification -- PhD Research Decision

**Date:** 2026-11-15
**Decision:** Build Option A -- enhanced LiDAR/imagery-driven material classification

---

## Two options considered

| Option | Description | Verdict |
|--------|-------------|---------|
| **A -- Enhanced classification** | Better per-building material assignment using LiDAR intensity, RGBN aerial imagery, and street-level images (Mapillary) | **CHOSEN -- publishable PhD contribution** |
| **B -- Per-building Sionna material** | Give each individual building its own unique calibrated εᵣ/σ/S | **REJECTED -- underdetermined; ~200-800 measurements vs 5,000-20,000 buildings** |

---

## Why Option A is the right PhD contribution

### Literature basis

| Source | Finding |
|--------|---------|
| **NYURay** (Rappaport group, NYU WIRELESS) | Achieves 3.2 dB LOS / 5.8 dB NLOS using per-building material classification from LiDAR. Per-class ITU-R P.2040-2 lookup -- no extra free parameters. |
| **arXiv:2507.19653** | Uniform material per building type is a 6-12 dB error source -- the dominant remaining error after geometry calibration |
| **Sionna RT** (Hoydis et al., NVIDIA) | "Significant improvement with photogrammetric point clouds + semantic segmentation" |
| **CLAUDE.md physics floor table** | Per-building material diversity: -1 to -2 dB RMSE improvement; classified as "Partially fixable" |

### What NYURay actually does (the model to follow)

NYURay does NOT calibrate a unique material per building. It:

1. LiDAR point cloud or aerial imagery → semantic segmentation
2. Each building surface labelled: brick / concrete / glass / metal / wood
3. ITU-R P.2040-2 properties assigned from lookup table (no free parameters added)
4. Result: more buildings get the physically correct material class rather than the fallback `itu_brick`

---

## Current material priority chain (scene builder CELL 4)

```
Priority 0  : building_materials_vlm.json (CELL 3b -- OSM Overpass tags + heuristics)
Priority 1b : oblique_facade_materials.json (CELL 2oblique -- aerial photo)
Priority 1  : OSM building:material= tag
Priority 2  : Use-type heuristic (greenhouse->glass, industrial->metal, residential->brick, civic->concrete)
Priority 3  : Age override (pre-1940->brick, 1940-1980->concrete, post-1980->type-based)
Fallback    : itu_brick
```

**New priority to add:**

```
Priority -2 : LiDAR intensity + RGBN roof classification (NEW)
Priority -1 : oblique_facade_materials.json (existing)
Priority 0  : building_materials_vlm.json (existing)
...
```

---

## Specific PhD contribution

Three complementary classification signals, each feeding into `_bld_mat()` as Priority -2:

### Signal 1 -- LiDAR intensity (roof material proxy)

- Building rooftop LiDAR return intensity correlates with material
- Metal sheds: high intensity (specular return)
- Concrete panels: mid intensity
- Clay tiles (brick buildings): mid-low
- Vegetation: noisy / variable
- Already partially implemented in notebook via `_material_from_intensity()`
- Data already downloaded (EA LiDAR DSM for all sites)

### Signal 2 -- RGBN aerial imagery (roof colour + NIR ratio)

- EA VOM tiles are RGBN (Red/Green/Blue/Near-Infrared)
- Roof colour + NIR ratio separates:
  - Clay tiles (brick buildings): warm red/brown, low NIR
  - Concrete panels: grey, moderate NIR
  - Metal roofs: bright/reflective, high NIR
  - Green roofs/vegetation: high NIR
- Already downloaded as part of nDSM workflow
- Implement as `_material_from_rgb(geometry)` in CELL 4 (stub already exists)

### Signal 3 -- Street-level facade (Mapillary + ONNX)

- Already built in `lod3/` module (commit `290824e`)
- Facade segmentation from Mapillary street-level images
- Output: per-facade material label -> aggregated to per-building

---

## Multi-frequency novelty

Test whether the SAME per-building classification improves R² at 915 / 1802 / 2695 / 3602 MHz simultaneously across Nottingham, Stevenage, and Southampton. This cross-frequency, multi-site validation has not been done with Sionna RT on Ofcom data.

---

## Revised priority chain (updated 2026-11-15)

Based on Paper 1 (Yun & Iskander 2023), wall defragmentation is now Priority -3 -- a geometry pass before material classification:

```
Priority -3 (NEW): Wall defragmentation -- merge co-planar OSM wall surfaces (Yun & Iskander 2023)
Priority -2: LiDAR intensity + RGBN roof colour classifier (NEW)
Priority -1: Oblique facade labels (confidence-gated; ceiling ~72% F1 per GT-LOD3 benchmark)
Priority  0: OSM Overpass + VLM enrichment (building_materials_vlm.json)
Priority  1: OSM building:material= tag
Priority  2: Use-type heuristic
Priority  3: Age override
Fallback: itu_brick
```

---

## Expected improvement

| Improvement | Basis | Expected delta R² |
|-------------|-------|------------------|
| Wall defragmentation | Eliminates systematic scatter double-counting from co-planar OSM surfaces | +0.02 to +0.05 |
| RGBN roof classifier (Signal 2) | LiDAR intensity / VOM colour separates metal/concrete/clay | +0.03 to +0.06 |
| LOD3 facade material (Signal 3) | Glass window surfaces; ceiling 56.5% F1 (GT-LOD3 benchmark) | +0.01 to +0.02 |
| **Total** | | **+0.05 to +0.12 R²** |

| Site | Current best R² | Expected with classification |
|------|----------------|------------------------------|
| Nottingham 1802 MHz | 0.509 | 0.55-0.62 |
| Nottingham 2695 MHz | 0.574 | 0.62-0.69 |
| Stevenage 1802 MHz | 0.735 | 0.78-0.85 |
| London 915 MHz | 0.365 | 0.40-0.47 |

---

## Implementation plan (updated)

1. **Wall defragmentation pass** in CELL 4 after building PLY generation -- co-planar merge using dot product of face normals (threshold 0.99); reduces triangle count ~36%, eliminates ray double counting
2. **Implement `_material_from_rgb(geometry)`** -- RGBN VOM roof colour classifier (warm/grey/bright = clay/concrete/metal)
3. **Implement `_material_from_intensity(geometry, fallback)`** properly -- LiDAR intensity thresholds
4. **Add Priority -2 hook** in `_bld_mat()` calling these two signals; return if confidence > threshold
5. **Connect LoD3 module output** (Mapillary facade labels) as Signal 3; window pixels --> glass surfaces
6. **Evaluate** at all sites and frequencies; compare RMSE/R² before and after

---

## Literature notes added 2026-11-15

### Paper 1 -- Yun & Iskander (2023 IEEE APS)
"Simplifying Building Structures for Efficient Radio Propagation Modeling"

- Tests on 24,023 NYC buildings from GML LOD2 data
- Co-planar wall merging: 33 surfaces --> 21 (36% reduction) for a typical building
- Method: dot product of face normals; if parallel (threshold ~0.99) and sharing edge, merge with RDP simplification
- Eliminates ray double counting at co-planar junctions (adjacent fragments hit twice by same ray)
- Small rooftop appendages can be dropped at <6 GHz without accuracy loss
- **Direct relevance:** Our OSM Shapely extrusion produces fragmented walls with the same problem; a defragmentation pass on each material PLY would reduce scatter variance and speed up path solving

### Paper 2 -- Kim et al. (ISPRS Annals 2026, GT-LOD3 Benchmark)
"GT-LOD3: LOD3 Semantic 3D Building Reconstruction Benchmark Dataset"

- First standardised benchmark for automatic LOD3 building reconstruction
- Two sites: Gold Coast (Ohio, USA) and TUM campus (Munich, DE -- same as TUM2TWIN)
- Pipeline: Point Transformer segmentation (5 classes) --> facade-aligned 2D projection --> opening extraction --> LOD3 CityGML
- Only 3 datasets worldwide currently reach LOD3: TUM2TWIN, Ingolstadt, Poznań
- **Window detection F1 = 56.5% instance-level** -- this is the current state of the art; our Mapillary approach will not exceed this
- Wall and roof: F1 = 89-95% -- reliable input for facade material labelling
- Simple facades (IV, V): F1 = 76-99%; complex/occluded (I, II): F1 = 46-56%
- London canyon facades are more complex than Stevenage suburb -- expect lower window recall in London
- Dataset: https://github.com/gdslab/GT-LOD3-Benchmark (CC BY 4.0)

---

## Key references to cite

- Yun, Z. and Iskander, M.F. -- "Simplifying Building Structures for Efficient Radio Propagation Modeling," IEEE APS 2023. DOI: 10.1109/USNC-URSI52151.2023.10238157
- Kim, H.S. et al. -- "GT-LOD3: LOD3 Semantic 3D Building Reconstruction Benchmark Dataset," ISPRS Annals XI-2-2026. DOI: 10.5194/isprs-annals-XI-2-2026-293-2026
- Ju, S., Xing, Y., Kanhere, O., Rappaport, T.S. -- NYURay outdoor calibration paper (IEEE Xplore)
- ITU-R P.2040-2 (2021) -- building material EM properties
- Hoydis, J. et al. (NVIDIA) -- Sionna RT + semantic segmentation
- arXiv:2507.19653 -- R²~0.5 physics floor, uniform material as dominant error source
- 3GPP TR 38.901 -- UMa NLOS physics floor sigma_SF
