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

## Expected improvement

| Site | Current best R² | Expected with per-building classification |
|------|----------------|------------------------------------------|
| Nottingham 1802 MHz | 0.509 | 0.55-0.60 |
| Nottingham 2695 MHz | 0.574 | 0.60-0.65 |
| Stevenage 1802 MHz | 0.735 | 0.76-0.80 |
| London 915 MHz | 0.365 | 0.40-0.45 |

Gain: approximately -1 to -2 dB RMSE, +0.05 to +0.10 R² per site and frequency.

---

## Implementation plan

1. **Implement `_material_from_rgb(geometry)`** in CELL 4 -- RGBN VOM roof colour classifier
2. **Implement `_material_from_intensity(geometry, fallback)`** properly -- LiDAR intensity thresholds
3. **Add Priority -2 hook** in `_bld_mat()` that calls these two signals and returns if confident
4. **Connect LoD3 module output** (Mapillary facade labels) as a third signal
5. **Evaluate** at all sites and frequencies; compare RMSE/R² before and after

---

## Key references to cite

- Ju, S., Xing, Y., Kanhere, O., Rappaport, T.S. -- NYURay outdoor calibration paper (IEEE Xplore)
- ITU-R P.2040-2 (2021) -- building material EM properties
- Hoydis, J. et al. (NVIDIA) -- Sionna RT + semantic segmentation
- arXiv:2507.19653 -- R²~0.5 physics floor, uniform material as dominant error source
- 3GPP TR 38.901 -- UMa NLOS physics floor sigma_SF
