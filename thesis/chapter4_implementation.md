# Chapter 4 — Implementation / Experimental Setup / Simulation

This chapter shows how the methodology of Chapter 3 was concretely built, configured, and run. Where Chapter 3 established *what* was done and *why* (the scientific approach, tools, and procedure), this chapter documents *how* it was implemented in software: the code/notebook architecture, the exact configuration values used at each site and frequency, how raw input data was obtained and cleaned, and the real technical challenges encountered along the way. Content already established in Chapters 2–3 (the Sionna RT component overview in Section 2.5.1, the hardware/software environment in Sections 2.5.2–2.5.3, the procedural steps in Section 3.4) is referenced rather than repeated.

## 4.1 Model Development / System Implementation

The methodology of Chapter 3 is implemented as a pair of Jupyter notebooks per site/frequency combination, following a consistent, config-driven architecture (Figure 4.1): a **scene-builder notebook** that turns raw geospatial data into a Sionna 2.0 scene file, and a **simulation notebook** that loads that scene, assigns and calibrates materials, places transmitter and receivers, runs the ray tracer, and evaluates the result. Each notebook follows the same internal convention: a single configuration cell (`CELL 0`/`CELL 1`) holds every site-specific parameter, and every other cell is a self-contained processing step identified by a stable label (`CELL 2b`, `CELL 4A`, `CELL 8e`, etc.) that later documentation and this thesis both refer to directly — the cell labels used throughout Chapters 2–3 are not an abstraction invented for this thesis, they are the actual notebook structure.

**Figure 4.1 — Code/notebook architecture and data-artefact interfaces.**

![Figure 4.1 — Code/notebook architecture and data-artefact interfaces](figures/fig4_1_architecture.png)

*Figure 4.1 — The scene-builder and simulation notebooks are separate programs connected only through file artefacts (the scene XML, and the calibrated-material/scalar-offset JSON files), not through shared in-memory state or function imports. This is a deliberate design choice: it lets the expensive scene-construction step (LiDAR download, mesh generation) be run once and frozen (Section 3.3), while the simulation notebook is iterated on repeatedly during calibration without ever risking a scene rebuild.*

Within the simulation notebook, each methodological step of Section 3.4 corresponds to a specific implementation:
- **Material assignment** (Step 2) is implemented via Sionna's `RadioMaterial` constructor, e.g. `RadioMaterial(name, relative_permittivity=<ε_r>, conductivity=<σ>, scattering_coefficient=<S>)`, with one instantiation per material in Table 3.2, initialised from ITU-R P.2040-2 [17].
- **Calibration** (Step 4, Equation 3.1) is implemented as a call to `scipy.optimize`'s Powell method [28], with the objective function wrapping a full scene evaluation (path solve + Equation 2.15) for each candidate parameter vector *θ*.
- **Frequency-dependent vegetation geometry** (Section 3.3, Figure 3.2's decision point) is implemented as a configuration branch: `VEG_DISC_LAYERS = 1` and fixed layer height fractions for the 915/1802 MHz scenes, versus `VEG_DISC_LAYERS = 3` with fractions `[0.30, 0.65, 1.0]` for the shared 2695/3602 MHz scene — the same branch depicted abstractly in Figure 3.2 is, concretely, this configuration variable. **Verification note:** this disc-layer configuration is documented in the project's working notes for a 2695/3602 MHz-specific scene-builder notebook that has not yet been added to this repository; it is reported here as the intended design pending that notebook being committed for direct code verification (see `references.md`'s pending-verification note).
- **Building height derivation** in the (verified, committed) scene-builder notebook `sionna019_scene_builder.ipynb` follows a four-level fallback chain per building footprint, implemented as ordered conditional logic rather than a single lookup (Figure 4.2): the LiDAR nDSM height at the building centroid is used when available and physically plausible; otherwise the OSM `height=` tag; otherwise `building:levels × 3.5 m`; otherwise a fixed `DEFAULT_HEIGHT_M`. This ordering is deliberate — nDSM is preferred because, per the notebook's own documentation, OSM height/level tags are sparse enough that relying on them alone "causes far-field signal under-attenuation" from buildings silently modelled too short.
- **Vegetation geometry** in this same verified notebook is, by default (`VEG_3D_GEOMETRY = False`), written as **flat, ground-level patches** carrying the `itu_vegetation` scattering material — not extruded 3D canopy volumes. This is a deliberate, documented choice, not an oversight: at 915 MHz a solid extruded canopy is opaque to Sionna's surface-based ray tracer (Section 2.1.7) and was found to block 100% of rays passing through it, producing −10 to −15 dB of over-attenuation in wooded corridors. Flat patches instead let the scattering material contribute diffuse loss at the ray level, while the *bulk* excess attenuation is added separately in post-processing (Weissberger [18], ≈10 dB per 30 m of woodland traversed) — precisely the division of labour between ray-level scattering and post-hoc correction already established theoretically in Section 2.1.7.

**Figure 4.2 — Building-height derivation fallback chain.**

![Figure 4.2 — Building-height derivation fallback chain](figures/fig4_2_height_logic.png)

*Figure 4.2 — Implemented exactly as documented in `sionna019_scene_builder.ipynb`'s own configuration notes: nDSM is tried first, with three progressively coarser fallbacks so that every building footprint receives a height even where LiDAR/OSM data is incomplete.*

**[TABLE 4.1]**

| `NDSM_PROVIDER` | Coverage | Data source |
|---|---|---|
| `'ea'` | England | Environment Agency WCS (free, 1 m) |
| `'usgs'` | USA | USGS 3DEP WCS (free, 1 m) |
| `'opentopo'` | Global | OpenTopography REST API (30 m SRTM, API key required) |

*Table 4.1 — LiDAR/DEM provider abstraction in the scene-builder notebook. The provider is auto-selected by scene latitude/longitude rather than hard-coded, which is what allows the same notebook logic to build both the English sites (`'ea'`) and Scar Hill (falling through to SRTM coverage, Section 3.3) without a separate code path.*

**[FIGURE 4.3 — PLACEHOLDER — requires a real scene screenshot, not fabricated]**
*3D scene preview (scene-builder notebook, `CELL PREVIEW`) for the Nottingham 915 MHz scene, showing the assembled terrain, building, and vegetation geometry as actually loaded into Sionna RT. To be inserted by running `CELL PREVIEW` and exporting the interactive viewer's render.*

## 4.2 Experimental / Simulation Setup

The compute platform and pinned software environment are documented in Sections 2.5.2–2.5.3 and are not repeated here. This section instead documents the concrete simulation-architecture parameters — the actual configuration values loaded by `CELL 0`/`CELL 1` — that instantiate the general ray-tracing theory of Section 2.1.2 for this specific implementation.

**[TABLE 4.2]**

| Parameter | Nottingham 915/1802 MHz | Nottingham 2695/3602 MHz | Scar Hill 915 MHz |
|---|---|---|---|
| `MAX_DEPTH` (interaction depth) | 8 | 20 | 8 |
| `NUM_SAMPLES_PS` (evaluation) | 100,000,000 | 100,000,000 | 10,000,000 |
| `CAL_SAMPLES_PS` (calibration) | 2,000,000 | 30,000,000 | 10,000,000 |
| Diffraction / edge diffraction | Enabled | Enabled | Enabled |
| `TERRAIN_GRID_N` | 1000 × 1000 | 1000 × 1000 | (SRTM-derived) |
| `TERRAIN_PAD_M` | 3000 | 3000 | 3000 |
| Coordinate system | EPSG:27700 | EPSG:27700 | EPSG:27700 |

*Table 4.2 — Representative ray-tracing and scene-grid configuration values by site/frequency, as set in the simulation notebooks' configuration cells. Scar Hill's lower evaluation sample count matches its calibration sample count deliberately (Section 2.5, "Scar Hill Run sequence") to keep calibration and evaluation self-consistent given the coarser SRTM terrain.*

For the Nottingham scenes specifically, the scene bounding box is fixed across builder and simulation notebooks — `SCENE_WEST = -1.267685`, with `SCENE_EAST`, `SCENE_SOUTH`, `SCENE_NORTH` similarly pinned — because, as noted in Section 3.4 Step 1, even a 0.025° mismatch between the two notebooks produces an ~855 m coordinate offset between terrain and building geometry. This bounding box is treated as an implementation-level invariant, checked automatically (Section 4.4) rather than trusted to manual consistency.

**[FIGURE 4.4 — PLACEHOLDER — requires real notebook output, not fabricated]**
*2D scene map (`CELL 6c`): all receivers plotted on an OpenStreetMap basemap, coloured by measured RSSI, transmitter marked with a star, with 500 m/1 km/2 km/3 km distance rings — the actual diagnostic used to sanity-check receiver placement and route coverage for each site.*

**[FIGURE 4.5 — PLACEHOLDER — requires real notebook output, not fabricated]**
*DTM → DSM → nDSM raster progression, three panels side by side: (a) bare-earth DTM (`CELL 2b` output, `dem.tif`), (b) surface-with-clutter DSM (`CELL 2d` output), (c) the derived nDSM = DSM − DTM clutter-height heatmap (`CELL 3c`, `ndsm.tif`) that feeds the height logic in Figure 4.2. Showing all three panels together, rather than nDSM alone, makes the raster-subtraction step (Section 4.3) visually explicit.*

**[FIGURE 4.6 — PLACEHOLDER — requires real notebook output, not fabricated]**
*DEM terrain elevation heatmap with TX/RX positions overlaid (`CELL 6b`): a second, terrain-focused sanity check distinct from Figure 4.5's OSM-basemap view — used specifically to confirm receiver elevations sampled from the DTM are physically reasonable (Section 3.4, Step 3's "DEM sanity check").*

## 4.3 Data Collection and Processing

Three raw data sources feed the implementation, each requiring its own acquisition and cleaning step before use in the methodology of Chapter 3:

**Ofcom measurement data.** Each site/frequency combination's ground truth is a single CSV exported from the Ofcom 2018 campaign [5], with one row per drive-test sample (WGS84 latitude/longitude, measured RSSI, and header metadata for transmitter height, EIRP, and noise floor — the values tabulated in Chapter 3, Section 3.3). Processing this file involves: reprojecting from WGS84 to the scene's local EPSG:27700-derived coordinate frame; filtering to the receivers falling inside the scene's bounding box (Section 3.4 documents a bug found in an early implementation, where the first *N* rows were taken *before* this filter, silently selecting receivers entirely outside the scene for routes starting far from the transmitter); and the sequence of geometric validity checks (DEM sanity, 2D/3D building-interior tests) already detailed procedurally in Section 3.4, Step 3.

**LiDAR terrain and vegetation data — the concrete file chain.** UK Environment Agency 1 m DTM and DSM tiles [8] are queried from the EA's public WCS endpoint for the scene's bounding box (with a padding margin, `TERRAIN_PAD_M = 3000`, so that terrain features just outside the simulated area still contribute correctly to diffraction geometry at the scene edge). Each stage of this raster pipeline produces a named, on-disk file, in this order:

1. **`dem.tif`** — the bare-earth DTM, downloaded per-tile from the EA WCS endpoint and merged into a single GeoTIFF covering the padded scene extent (`CELL 2b`; `NDSM_PROVIDER` selects the WCS source, Table 4.1).
2. **`dsm.tif`** — the corresponding surface model, including buildings, trees, and other above-ground clutter, downloaded the same way (`CELL 2d`).
3. **`ndsm.tif`** — the normalised surface model, computed as the simple raster subtraction nDSM = DSM − DTM (`CELL 2d`), giving above-ground height directly at every pixel. This is the file that feeds both the building-height fallback chain (Figure 4.2) and vegetation-canopy height where used.
4. **`terrain.ply`** — the DTM resampled onto a regular `TERRAIN_GRID_N`-resolution mesh grid and triangulated into the ground-plane geometry Sionna RT actually traces rays against (`CELL 3`).

This ordering — two independent raster downloads, one raster-algebra step, then one mesh-generation step — is why the pre-run consistency check in Section 3.4, Step 1 explicitly re-derives the expected terrain half-span from the scene bounding box and compares it against `terrain.ply`'s actual vertices: an inconsistency introduced at any of these four stages would otherwise only surface much later, as an unexplained accuracy loss.

For Scar Hill, outside EA coverage, the equivalent `dem.tif`/`ndsm.tif` pair is obtained via a different `NDSM_PROVIDER` (30 m SRTM, auto-selected by scene latitude — Table 4.1), which is why this site's terrain resolution differs categorically from the English sites (Section 3.3) despite using an identical downstream code path.

**OpenStreetMap vector data.** Building footprints, roads, waterways, and land-use/natural polygons (the source for vegetation areas) are queried via `osmnx`/`geopandas` for the same bounding box and tag-filtered to the feature classes relevant to the scene. This vector data is **not** written to an intermediate file format (no `.geojson` or shapefile export was found in the scene-builder notebook): it is held as in-memory `GeoDataFrame` objects, reprojected directly to local scene coordinates, and converted straight into per-material PLY meshes (`bld_itu_brick.ply`, `bld_itu_concrete.ply`, `veg_itu_vegetation.ply`, `road_itu_asphalt.ply`, `water_itu_water.ply`, etc. — `CELL 4`) without a separate serialisation step. Building height is resolved via the fallback chain in Figure 4.2; vegetation polygons are rasterised into flat ground-level patches, not extruded volumes, for the physical reason given above.

**Scene assembly.** Once all PLY meshes exist on disk, `CELL B3` assembles them — together with `terrain.ply` — into the single Sionna 2.0 scene description, `scene_sionna2.xml`, which is the sole interface artefact the simulation notebook consumes (Figure 4.1).

All three raw sources are combined only after independently being reprojected into the same local scene coordinate frame (WGS84 → EPSG:27700 → scene-local metres), which is itself a processing step worth stating explicitly: a reprojection error at this stage would silently misalign every subsequent geometry and measurement comparison, which is precisely the class of error the bounding-box and terrain consistency checks in Section 3.4 and Section 4.4 exist to catch.

## 4.4 Challenges and Adjustments

Implementing the methodology of Chapter 3 surfaced a number of concrete technical problems, distinct from the modelling limitations already discussed in Section 3.3. Reporting them here — with root cause and fix — is itself part of demonstrating a reproducible implementation: several would silently corrupt results if left unfixed, rather than causing an obvious failure.

**[TABLE 4.3]**

| Problem | Root cause | Fix |
|---|---|---|
| Calibration RMSE completely flat across all Powell evaluations | Dr.Jit kernel caching reused a compiled kernel across evaluations with different material parameters, masking real sensitivity | Added a 3-probe sensitivity check before calibration to detect this condition before trusting any calibration run |
| GPU memory exhausted (swap filled) after ~680 calibration evaluations | `PathSolver` result objects were not explicitly deleted between evaluations | Explicit deletion of the solver result each iteration |
| ±4 dB drift between nominally identical evaluations | No fixed random seed; Monte Carlo path sampling varied run to run | `CAL_FIXED_SEED = 42` fixed throughout calibration and evaluation |
| Buildings appearing below ground level in the scene | `local_z` height lookup was numerically unreliable | Replaced with a `RegularGridInterpolator` sampling the terrain PLY directly |
| A single large vegetation polygon (the M1 motorway corridor) received only 10 discs, leaving it under-vegetated | `VEG_MAX_DISCS_PER_POLYGON` was hard-capped at 10 | Raised to 500 (and 1000 for the shared HF scene) |
| O(n_receivers × 67,292) nested loop made Weissberger vegetation correction impractically slow | Naive per-receiver, per-polygon distance search | Replaced with an `STRtree` spatial index for the vegetation geometry |
| Receivers silently placed outside the scene for routes starting far from the transmitter | CSV rows were truncated to the first *N* before bounding-box filtering | Filter to bounding box first, then take the first *N* in sequential order (Section 4.3) |
| 2695/3602 MHz `RadioMaterial` property access raised `TypeError` | Sionna tensor-wrapped properties were read with a bare `float()` cast | Introduced a `_safe_f()` unwrapping helper |
| A `NearestNDInterpolator` was silently shadowed by an unrelated variable of the same name | Variable name collision (`_near`) between a fitted interpolator and a DataFrame slice | Renamed the DataFrame variable to `_df_near` |
| At 3602 MHz, calibration RMSE was stuck at ~46 dB with a scalar offset pinned at its bound | `CAL_SCALAR_BOUNDS = (-30, 20)` clipped the true optimum (~+30 dB), and Phase 2 fought Phase 0 trying to reduce it | Widened bounds to `(-60, 60)` |
| Solid 3D canopy geometry blocked essentially all rays beyond ~400 m at 3602 MHz | At λ = 8.3 cm, canopy cone geometry is large relative to the wavelength and acts as an opaque obstacle rather than a scatterer | `DISABLE_CANOPY = True`, with bulk attenuation recovered via per-path ITU-R P.833-10 correction instead (Section 2.1.7, Section 3.4 Step 5) |

*Table 4.3 — Representative implementation-level bugs encountered during this project, their root causes, and the fixes applied (all committed to the project's version history). This is a representative subset, not exhaustive; several additional fixes of the same character are documented alongside the code itself.*

Two adjustments are significant enough to discuss beyond the table. First, the discovery that `DISABLE_CANOPY` was *necessary* at 3602 MHz (rather than an arbitrary simplification) came directly from the RMSE behaviour in Table 4.3 — the model was not merely inaccurate with canopy geometry active, it was structurally blocking propagation beyond a few hundred metres, which is a qualitatively different failure from a calibration shortfall. Second, the sequence of fixes to receiver selection and coordinate handling (Section 4.3) reflects an adjustment to the overall implementation discipline: after the second such bug, an explicit bounding-box consistency check (Section 3.4, Step 1) was added as a mandatory pre-run step for every subsequent site, rather than relying on catching each new instance of the same underlying class of error individually.

**[FIGURE 4.7 — PLACEHOLDER — requires real notebook output, not fabricated]**
*Calibration convergence plot (`calibration_summary.png`, produced by the calibration notebook's post-calibration analysis cell): Powell objective value (Equation 3.1) versus evaluation number, showing convergence to the Monte Carlo noise floor discussed in Section 3.4, Step 4.*

**[FIGURE 4.8 — PLACEHOLDER — requires real notebook output, not fabricated]**
*Runtime scattering-coefficient sensitivity sweep (`CELL 8c`): RMSE/R² as a function of a runtime-overridden scattering coefficient, independent of the full Powell search — the targeted sensitivity analysis mentioned in Section 3.4, Step 6.*

Note: the coverage-map comparison and coarse-vs-detailed geometry figures already flagged as placeholders in Chapter 3 (Figures 3.3 and 3.7), and the vegetation disc-layer schematic already in Chapter 3 (Figure 3.4), are not repeated here — they belong to the methodology-level illustration of those concepts, not to this chapter's implementation-level record.

---

*Figures 4.3–4.8 are marked as placeholders because they require running the actual notebooks and capturing real output — this environment has no GPU, no Sionna RT installation, and no access to the underlying scene/CSV files needed to produce them, so none have been fabricated. Figures 4.1 and 4.2 are original diagrams built directly from this chapter's verified source material (the notebook architecture and the documented building-height fallback chain), not simulation output, and so were produced directly.*

*References for this chapter reuse [3], [5], [8], [17], [18], [28] from Chapters 1–3. See `references.md` for the full, verified reference list shared across all chapters.*
