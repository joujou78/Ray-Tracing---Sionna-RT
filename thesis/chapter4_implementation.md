# Chapter 4 — Implementation / Experimental Setup / Simulation

This chapter shows how the methodology of Chapter 3 was concretely built, configured, and run. Where Chapter 3 established *what* was done and *why* (the scientific approach, tools, and procedure), this chapter documents *how* it was implemented in software: the code/notebook architecture, the exact configuration values used at each site and frequency, how raw input data was obtained and cleaned, and the real technical challenges encountered along the way. Content already established in Chapters 2–3 (the Sionna RT component overview in Section 2.5.1, the hardware/software environment in Sections 2.5.2–2.5.3, the procedural steps in Section 3.4) is referenced rather than repeated.

## 4.1 Model Development / System Implementation

The methodology of Chapter 3 is implemented as a pair of Jupyter notebooks per site/frequency combination, following a consistent, config-driven architecture (Figure 4.1): a **scene-builder notebook** that turns raw geospatial data into a Sionna 2.0 scene file, and a **simulation notebook** that loads that scene, assigns and calibrates materials, places transmitter and receivers, runs the ray tracer, and evaluates the result. Each notebook follows the same internal convention: a single configuration cell (`CELL 0`/`CELL 1`) holds every site-specific parameter, and every other cell is a self-contained processing step identified by a stable label (`CELL 2b`, `CELL 4A`, `CELL 8e`, etc.) that later documentation and this thesis both refer to directly — the cell labels used throughout Chapters 2–3 are not an abstraction invented for this thesis, they are the actual notebook structure.

**Figure 4.1 — Code/notebook architecture and data-artefact interfaces.**

![Figure 4.1 — Code/notebook architecture and data-artefact interfaces](figures/fig4_1_architecture.png)

*Figure 4.1 — The scene-builder and simulation notebooks are separate programs connected only through file artefacts (the scene XML, and the calibrated-material/scalar-offset JSON files), not through shared in-memory state or function imports. This is a deliberate design choice: it lets the expensive scene-construction step (LiDAR download, mesh generation) be run once and frozen (Section 3.3), while the simulation notebook is iterated on repeatedly during calibration without ever risking a scene rebuild.*

Within the simulation notebook, each methodological step of Section 3.4 corresponds to a specific implementation:
- **Material assignment** (Step 2) is implemented via Sionna's `RadioMaterial` constructor, e.g. `RadioMaterial(name, relative_permittivity=<ε_r>, conductivity=<σ>, scattering_coefficient=<S>)`, with one instantiation per material in Table 3.2, initialised from ITU-R P.2040-2 [17].
- **Calibration** (Step 4, Equation 3.1) is implemented behind a `CAL_OPTIMIZER` configuration flag that selects between interchangeable optimiser back-ends sharing the same three-phase structure (scalar-offset pre-fit, joint parameter search, scalar re-fit) and the same objective function — a full scene evaluation (path solve + Equation 2.15) per candidate parameter vector *θ*. Early development and several per-site calibration runs used `scipy.optimize`'s Powell method [28], a derivative-free conjugate-direction search. For the final calibration passes reported in this thesis, the joint-search phase was switched to the **Covariance Matrix Adaptation Evolution Strategy (CMA-ES)** [31], implemented via the `cma` package: a population-based, derivative-free global optimiser that adapts its search covariance to the local objective landscape. This switch was made because the free material parameters (ε_r, σ, S per material — up to 18 simultaneously at 1802 MHz) are not independent: permittivity, conductivity, and scattering interact in the underlying Fresnel/scattering physics (Section 2.1.4, Equation 2.16), making the objective non-separable — a regime Powell's coordinate-wise search handles poorly but CMA-ES's covariance adaptation is designed for. A differential-evolution back-end was also implemented and evaluated during this exploration but converged more slowly (≈5.5 h vs ≈2–3 h for CMA-ES at matched sample counts) and was not used for the final results.
- **Frequency-dependent vegetation geometry** (Section 3.3, Figure 3.2's decision point) is implemented as a configuration branch: `VEG_DISC_LAYERS = 1` and fixed layer height fractions for the 915/1802 MHz scenes, versus `VEG_DISC_LAYERS = 3` with fractions `[0.30, 0.65, 1.0]` for the shared 2695/3602 MHz HF scene — the same branch depicted abstractly in Figure 3.2 is, concretely, this configuration variable. The standard (single-layer) scene uses horizontal disc PLYs at 20 m grid spacing (`VEG_DISC_SPACING_M = 20`) across OSM and EA VOM polygon extents, supplemented by an nDSM-derived extra scan at 10 m resolution (`VEG_NDMS_EXTRA_RES_M = 10`) to capture road verges, garden trees, and motorway vegetation belts not represented in polygon layers. The 3-layer HF scene (used for 3602 MHz) stacks three discs per crown at height fractions [0.30, 0.65, 1.0] of crown depth, spaced at 10 m (4× denser), with up to 1,000 discs per polygon.
- **Individual trees** are placed from the LiDAR nDSM using local maximum detection with a 5 m minimum inter-tree spacing, a height band of 3–30 m, and a building-footprint exclusion mask. For the Nottingham scene, this yields **15,486 individual trees**, each represented as a 3D canopy cone (`canopy_itu_vegetation`) and trunk cylinder (`trunk_itu_wood`), alongside the disc PLY layer.
- **Building height derivation** in the (verified, committed) scene-builder notebook `sionna019_scene_builder.ipynb` follows a four-level fallback chain per building footprint, implemented as ordered conditional logic rather than a single lookup (Figure 4.2): the LiDAR nDSM height at the building centroid is used when available and physically plausible; otherwise the OSM `height=` tag; otherwise `building:levels × 3.5 m`; otherwise a fixed `DEFAULT_HEIGHT_M`. This ordering is deliberate — nDSM is preferred because OSM height/level tags are sparse enough that relying on them alone causes far-field signal under-attenuation from buildings modelled too short.
- **Vegetation geometry** in this verified notebook is, by default, written as **flat, ground-level patches** carrying the `itu_vegetation` scattering material — not extruded 3D canopy volumes. This is a deliberate choice: at 915 MHz a solid extruded canopy is opaque to Sionna's surface-based ray tracer (Section 2.1.7) and was found to block 100% of rays passing through it, producing −10 to −15 dB of over-attenuation in wooded corridors. Flat patches instead let the scattering material contribute diffuse loss at the ray level, while the bulk excess attenuation is added separately in post-processing (Weissberger [18] at 915/1802 MHz; ITU-R P.833-10 [16] at 2695/3602 MHz).

**Figure 4.2 — Building-height derivation fallback chain.**

![Figure 4.2 — Building-height derivation fallback chain](figures/fig4_2_height_logic.png)

*Figure 4.2 — Implemented exactly as documented in `sionna019_scene_builder.ipynb`'s own configuration notes: nDSM is tried first, with three progressively coarser fallbacks so that every building footprint receives a height even where LiDAR/OSM data is incomplete. In the Nottingham scene, 92% of buildings successfully resolve to nDSM heights.*

**Table 4.1 — LiDAR/DEM provider abstraction.**

| `NDSM_PROVIDER` | Coverage | Data source | Resolution |
|---|---|---|---|
| `'ea'` | England (≤55.9°N) | Environment Agency WCS (free, open) | 1 m |
| `'usgs'` | USA | USGS 3DEP WCS (free, open) | 1 m |
| `'opentopo'` | Global fallback | OpenTopography REST API (SRTM) | 30 m |

*Table 4.1 — The provider is auto-selected by scene latitude/longitude rather than hard-coded. English sites (Nottingham, London, Stevenage) use `'ea'`; the Scottish Scar Hill site falls through to `'opentopo'` as it lies north of the EA LiDAR boundary at 55.9°N (Section 3.3).*

**[FIGURE 4.3 — PLACEHOLDER — requires a real scene screenshot, not fabricated]**
*3D scene preview (scene-builder notebook, `CELL PREVIEW`) for the Nottingham 915 MHz scene, showing the assembled terrain, building, vegetation disc, and individual tree geometry as actually loaded into Sionna RT.*

## 4.2 Experimental / Simulation Setup

The compute platform and pinned software environment are documented in Sections 2.5.2–2.5.3 and are not repeated here. This section documents the concrete simulation-architecture parameters — the actual configuration values loaded by `CELL 0`/`CELL 1` — that instantiate the general ray-tracing theory of Section 2.1.2 for this specific implementation.

**Table 4.2 — Ray-tracing and calibration configuration by site and frequency.** All frequencies share EPSG:27700 (British National Grid, `always_xy=True`), MAX_DEPTH=8, diffraction and edge diffraction enabled, and TERRAIN_PAD_M=3000. RX AGL=1.5 m throughout.

| Parameter | Nottm 915 MHz | Nottm 1802 MHz | Nottm 2695 MHz | Nottm 3602 MHz | London 915 MHz | Scar Hill 915 MHz |
|---|---|---|---|---|---|---|
| TX AGL | 17 m | 17 m | 17 m | 17 m | 45 m | 17 m |
| TX EIRP | — | — | 56 dBm | 54 dBm | 49 dBm | 46.9 dBm |
| Noise floor | −124 dBm | — | −120 dBm | −109 dBm | — | −124 dBm |
| `CAL_SAMPLES_PS` | 2 M | 2 M | 10 M | 30 M | 15 M | 10 M |
| `NUM_SAMPLES_PS` | 100 M | 100 M | 100 M | 100 M | 100 M | 10 M |
| `CAL_MAX_DIST_KM` | 1.5 | 1.5 | 1.0 | 1.0 | 1.75 | 1.5 |
| `CAL_MIN_DIST_KM` | 0.15 | 0.15 | 0.15 | 0.15 | 0.15 | 0.15 |
| `CAL_SCALAR_BOUNDS` | (−20, 5) | (−20, 5) | (−30, 20) | (−60, 60) | (−60, 60) | (−30, 20) |
| `DISABLE_VEG_DISCS` | False | True | False | False | False | False |
| `DISABLE_CANOPY` | False | False | False | True | False | False |
| Terrain source | EA LiDAR 1 m | EA LiDAR 1 m | EA LiDAR 1 m | EA LiDAR 1 m | EA LiDAR 1 m | SRTM 30 m |
| Vegetation formula | Weissberger | Weissberger | ITU-R P.833-10 | ITU-R P.833-10 | Weissberger | Weissberger |
| Dual-slope Rbp | 311 m | 613 m | 916 m | 1225 m | 458 m | 311 m |
| **Best R² (ON incoh)** | **0.835 @ 0–750 m** | **0.509 @ 0–1250 m** | **0.574 @ 0–1250 m** | **0.515 @ 0–1250 m** | **0.365 @ 0–1000 m** | **0.083 @ 0–1250 m** |

*Table 4.2 — Scar Hill uses 10 M evaluation samples (matching calibration) rather than 100 M, as the coarser SRTM terrain does not benefit from the additional MC precision. The dual-slope breakpoint Rbp = 4·hBS·hUT·f/c (ITU-R P.1411 [15]) is computed for each frequency at the transmitter and receiver heights above ground.*

**Table 4.3 — CMA-ES calibration hyperparameters** (shared across all sites using the CMA-ES back-end).

| CMA-ES parameter | Value | Meaning |
|---|---|---|
| Search space | Normalised [0,1] per dimension | ε_r, log σ, S for each free material, min–max scaled |
| σ₀ (initial step size) | 0.25–0.3 | Fraction of the normalised parameter range |
| Population size (λ) | 4 + 3·ln n (auto), or 36 (explicit) | n = number of free parameters; larger λ reduces ranking noise from MC objective |
| Max generations | 200–300 | Site-dependent stopping criterion |
| `tolfun` | 0.10 | Terminate when function value std across population < 0.10 dB |
| Samples per evaluation | 10–30 M | Matched to `CAL_SAMPLES_PS` to keep calibration/evaluation MC noise floors consistent |
| Fixed seed | 42 | Reproducibility; shared with the Powell back-end |
| Warm start | Enabled | Initialised from ITU-R P.2040-2 defaults with S warm prior = 0.35 |

*Table 4.3 — The objective function, EM parameter bounds, and output files (`calibrated_materials_<freq>.json`, `scalar_offset_<freq>.json`) are shared with the Powell back-end, so switching optimisers required no change to the surrounding pipeline (Figure 4.1).*

**Table 4.4 — Final calibration results by site and frequency.**

| Site / Frequency | Optimiser | Cal RX | Free mats | Cal RMSE | Best R² | Range | Notes |
|---|---|---|---|---|---|---|---|
| Nottingham 915 MHz | Powell | 208 | 6 | ~8–9 dB | **0.835** | 0–750 m | 100 M eval; ON incoh |
| Nottingham 1802 MHz | Powell | — | 6 | — | **0.509** | 0–1250 m | DISABLE_VEG_DISCS=True; 15,486-tree scene |
| Nottingham 2695 MHz | Powell | 373 | 6 | ~13.7 dB | **0.574** | 0–1250 m | CAL_MAX=1.0 km (below Rbp=916 m); DISABLE_VEG_DISCS=False |
| Nottingham 3602 MHz | Powell | 601 | 6 | ~15.4 dB | **0.515** | 0–1250 m | DISABLE_CANOPY=True; per-path P.833-10; height filter z>30 m |
| London 915 MHz | CMA-ES | 223 | 5 | 6.888 dB | **0.365** | 0–1000 m | scalar=+28.766 dB; metals locked |
| London 1802 MHz | CMA-ES | 86 | 5 | in progress | TBD | 0–750 m | S caps brick/concrete ≤0.45; Run 4 in progress |
| Scar Hill 915 MHz | Powell | 202 | — | 10.71 dB | **0.083** | 0–1250 m | SRTM 30 m terrain physics floor; R² limited by terrain resolution |
| Stevenage 915 MHz | — | — | — | — | TBD | — | Scene built; calibration pending |

*Table 4.4 — All R² values report ON incoh (scattering ON, incoherent summation), which consistently outperforms coherent and OFF-scatter modes across all sites. The 3GPP TR 38.901 [6] UMa NLOS shadow fading floor (σ_SF = 7.82 dB) sets the irreducible RMSE minimum for the urban sites.*

For the Nottingham scenes specifically, the scene bounding box is fixed across builder and simulation notebooks — `SCENE_WEST = -1.267685`, `SCENE_EAST = -1.119832`, `SCENE_SOUTH = 52.943165`, `SCENE_NORTH = 53.003037` — because even a 0.025° mismatch produces an ~855 m coordinate offset between terrain and building geometry. This bounding box is treated as an implementation-level invariant, checked automatically (Section 4.4) rather than trusted to manual consistency.

**[FIGURE 4.4 — PLACEHOLDER — requires real notebook output, not fabricated]**
*2D scene map (`CELL 6c`): all receivers plotted on an OpenStreetMap basemap, coloured by measured RSSI, transmitter marked with a star, with 500 m / 1 km / 2 km / 3 km distance rings.*

**[FIGURE 4.5 — PLACEHOLDER — requires real notebook output, not fabricated]**
*DTM → DSM → nDSM raster progression, three panels side by side: (a) bare-earth DTM, (b) surface DSM with above-ground clutter, (c) derived nDSM = DSM − DTM giving above-ground heights.*

## 4.3 Data Collection and Processing

Three raw data sources feed the implementation, each requiring its own acquisition and cleaning step before use in the methodology of Chapter 3.

**Ofcom measurement data.** Each site/frequency combination's ground truth is a single CSV exported from the Ofcom 2018 campaign [5], with one row per drive-test sample (WGS84 latitude/longitude, measured RSSI, and header metadata for transmitter height, EIRP, and noise floor).

**Table 4.5 — Ofcom 2018 dataset statistics by site and frequency.**

| Site | Frequency | Total records | Within scene bbox | Cal receivers (range) | Noise floor | TX EIRP |
|---|---|---|---|---|---|---|
| Nottingham | 915 MHz | — | ~985 (0–2.5 km) | 208 (≤1.5 km) | −124 dBm | — |
| Nottingham | 1802 MHz | — | ~1,177 (0–2.5 km) | — | — | — |
| Nottingham | 2695 MHz | 261,967 | 36,351 | 373 (≤1.0 km) | −120 dBm | 56 dBm |
| Nottingham | 3602 MHz | — | — | 601 (≤1.0 km) | −109 dBm | 54 dBm |
| London | 915 MHz | — | ~179 (0–2.0 km) | 223 (≤1.75 km) | — | 49 dBm |
| London | 1802 MHz | — | — | 86 (≤0.75 km) | — | — |
| Scar Hill | 915 MHz | 143,541 | — | 202 (≤1.5 km) | −124 dBm | 46.9 dBm |

*Table 4.5 — Cal receivers are those passing all three filters (noise floor margin, distance bounds, per-bin valid-path coverage ≥65%) and represent the set used in the calibration objective function. The Nottingham 2695 MHz dataset illustrates the density reduction from raw to usable: 261,967 total → 36,351 in scene → 373 calibration receivers within 1.0 km.*

Processing this file involves: reprojecting from WGS84 to the scene's local EPSG:27700-derived coordinate frame; filtering to receivers falling inside the scene bounding box (Section 3.4 documents a bug in an early implementation where the first *N* rows were taken before this filter, silently selecting receivers outside the scene for routes starting far from the transmitter — commit `9bb6be0`); and the sequence of geometric validity checks (DEM sanity, 2D/3D building-interior tests) detailed procedurally in Section 3.4, Step 3.

Before calibration, records are filtered by three criteria:
- **Noise floor margin:** Records within 10 dB of the receiver noise floor are discarded to avoid SNR-limited measurements biasing the calibration objective.
- **Distance bounds:** Records below `CAL_MIN_DIST_KM` (0.15 km) are excluded as near-field geometry dominates; records above `CAL_MAX_DIST_KM` are excluded to keep calibration within a single propagation regime (see dual-slope constraint, Section 4.4).
- **Valid-path coverage:** Per-100 m distance bin coverage is evaluated; bins where fewer than 65% of receivers have valid simulated paths are excluded from calibration range discovery.

**LiDAR terrain and vegetation data.** UK Environment Agency 1 m DTM and DSM tiles are queried from the EA's public WCS endpoint for the scene bounding box with a 3,000 m padding margin. The concrete on-disk file chain for each site is:

1. **`dem.tif`** — bare-earth DTM, downloaded per-tile from the EA WCS endpoint and merged into a single GeoTIFF covering the padded scene extent (`CELL 2b`).
2. **`dsm.tif`** — corresponding surface model including buildings, trees, and above-ground clutter (`CELL 2d`).
3. **`ndsm.tif`** — normalised surface model, computed as nDSM = DSM − DTM (`CELL 2d`), giving above-ground clutter height at every pixel.
4. **`terrain.ply`** — DTM resampled onto a 1,000 × 1,000 regular mesh and triangulated into the ground-plane PLY geometry Sionna RT traces rays against (`CELL 3`).

For the Scar Hill site (Scotland, north of EA LiDAR boundary at 55.9°N), the equivalent raster pair is obtained via SRTM 30 m from OpenTopography, auto-selected by scene latitude — the same downstream code path executes identically, producing terrain at categorically coarser resolution (Section 3.3). This is why Scar Hill's best R² (0.083) reflects a terrain physics floor rather than a calibration shortfall.

**OpenStreetMap vector data.** Building footprints, roads, waterways, and land-use polygons are queried via `osmnx`/`geopandas` for the scene bounding box, held as in-memory `GeoDataFrame` objects, reprojected to scene-local coordinates, and converted directly into per-material PLY meshes without an intermediate file format — `bld_itu_brick.ply`, `bld_itu_concrete.ply`, `veg_itu_vegetation.ply`, `road_itu_asphalt.ply`, `water_itu_water.ply`, etc. (`CELL 4`). Road junction polygons are dissolved via union to remove self-intersecting overlaps that would cause rendering artefacts. All three raw sources are reprojected into the same EPSG:27700 local coordinate frame before combination; a reprojection error at this stage would silently misalign every subsequent geometry and measurement comparison.

## 4.4 Challenges and Adjustments

Implementing the methodology of Chapter 3 surfaced a number of concrete technical problems, distinct from the modelling limitations already discussed in Section 3.3. Reporting them here — with root cause, fix, and version-control commit — demonstrates a reproducible implementation: several would silently corrupt results if left unfixed, rather than causing an obvious failure.

**Table 4.6 — Implementation bugs encountered, root causes, and fixes.**

| Problem | Root cause | Fix | Commit |
|---|---|---|---|
| Calibration RMSE completely flat across all Powell evaluations | DrJIT kernel caching reused a compiled kernel across evaluations with different material parameters | 3-probe sensitivity check before calibration run; abort if Δ < 0.05 dB per probe | `6e2b4e2` |
| GPU memory exhausted (swap filled) after ~680 calibration evaluations | `PathSolver` result objects not explicitly deleted between evaluations | Explicit deletion of solver result each iteration | `285eb13` |
| ±4 dB drift between nominally identical evaluations | No fixed random seed; MC path sampling varied run to run | `CAL_FIXED_SEED = 42` applied throughout calibration and evaluation | — |
| Buildings appearing below ground level in the scene | `local_z` height lookup numerically unreliable at scene boundaries | Replaced with `RegularGridInterpolator` sampling the terrain PLY directly | `2bec77c` |
| A large vegetation polygon (M1 motorway corridor) received only 10 discs | `VEG_MAX_DISCS_PER_POLYGON` hard-capped at 10 | Raised to 500 (standard scene) / 1,000 (HF scene) | `c1d08d3` |
| O(n_receivers × 67,292) nested loop made Weissberger correction impractically slow | Naive per-receiver, per-polygon distance search | Replaced with `STRtree` spatial index for vegetation geometry | `7c8bd5c` |
| Receivers silently placed outside the scene for routes starting far from the transmitter | CSV rows truncated to first N before bounding-box filtering | Filter to bounding box first, then take first N in sequential order | `9bb6be0` |
| 2695/3602 MHz `RadioMaterial` property access raised `TypeError` | Sionna tensor-wrapped properties read with bare `float()` cast | Introduced `_safe_f()` unwrapping helper | `5ad27dd` |
| A `NearestNDInterpolator` silently shadowed by an unrelated variable | Variable name collision (`_near`) between fitted interpolator and a DataFrame slice | Renamed DataFrame variable to `_df_near` | `ff8168d` |
| At 3602 MHz, calibration RMSE stuck with scalar pinned at its bound | `CAL_SCALAR_BOUNDS = (-30, 20)` clipped the true optimum (~+30 dB); Phase 2 fought Phase 0 | Widened bounds to `(-60, 60)` | `8979235` |
| 17 scene XML `INCLUDE_*` flags had no `_SKIP_PLY` guard — stale PLYs silently entered the XML | Missing guard condition in scene export cell (`CELL B3`) | Added `_SKIP_PLY` guard to all inclusion flags | `e410b9a` |
| All 5 building height clips hardcoded, ignoring `None`-aware config | `None` values triggered `TypeError` in height comparisons | Replaced with `None`-aware `_bld_cap` / `_veg_cap` pattern | `2bdcec4` |
| Phase 3 re-scalar comparison was inverted — kept worse result | Boolean condition `if new_rmse > old_rmse: keep` rather than `< ` | Fixed comparison direction | — |
| `itu_ceiling_board` not explicitly activated when `DISABLE_VEG_DISCS=False` | `CELL 4A` only had a branch to transparentise ceiling_board (when True); no `else` to activate it | Added `else` branch setting er=17, σ=0.15 S/m, S=0.50 explicitly before any PathSolver call | `470ab4a`, `2959d6b` |
| Stevenage EA VOM raster storing canopy height in decimetres, not metres | EA VOM tile convention for this area; median ~178 dm → 17.8 m, but naive interpretation → 178 m and negative nDSM | Auto-detect: if VOM tile median > 20 → divide by 10. Fixed nDSM p5/p50/p95 = 1.9/17.8/19.8 m | `ff637c2`, `ac0f341` |

*Table 4.6 — Commit hashes refer to the project repository at `joujou78/Ray-Tracing---Sionna-RT`. All are on branch `claude/cool-cori-rrWbY`. Several additional minor fixes are documented in the project history.*

Four challenges merit extended discussion beyond the table.

**Vegetation geometry at high frequencies.** At 3602 MHz (λ = 8.3 cm), tree branch diameters approach the wavelength, making individual tree canopy cones nearly opaque to the ray tracer. Calibration attempts with active canopy geometry (`DISABLE_CANOPY = False`) produced a Phase 0 scalar of +30 dB and an uncalibratable RMSE above 29 dB, as all rays beyond ~400 m were absorbed by tree cones before reaching the receiver. The adopted solution disables the 3D tree canopy geometry (`DISABLE_CANOPY = True`), making individual trees electromagnetically transparent, and compensates with a per-path ITU-R P.833-10 correction applied to each ray segment in post-processing. This applies attenuation proportional to the depth of canopy traversed, computed from intersection tests against the scene geometry using `paths.vertices` data. A height filter (`z > 30 m` scene-local) excludes ray segments both of whose endpoints lie above canopy level, preventing erroneous correction of ray paths travelling entirely above the trees (commit `b15eb12`).

**Dual-slope breakpoint and calibration range.** Urban propagation transitions from a LOS-dominated regime to an NLOS regime at the dual-slope breakpoint distance R_bp = 4·h_BS·h_UT·f/c (ITU-R P.1411 [15]). For 2695 MHz at Nottingham (h_BS = 17 m, h_UT = 1.5 m), R_bp = 916 m; for London 915 MHz (h_BS = 45 m, h_UT = 1.5 m), R_bp = 458 m. Calibrating across this boundary mixes two distinct propagation physics: at 2695 MHz, the per-range bias changes sign at ~916 m, forcing the calibration scalar toward zero and collapsing R² from 0.246 (single-regime calibration within 1.0 km) to 0.173 (dual-slope calibration to 1.5 km). The calibration range upper bound was restricted to `CAL_MAX_DIST_KM` values below R_bp for each frequency — a non-obvious implementation constraint that has material impact on the reported R².

**Scatter budget consistency (CELL 4A bug).** A critical constraint for reproducible results is that the material state at calibration time must be identical to the state at final evaluation time. `CELL 4A` (the material-loading cell) contained an `if DISABLE_VEG_DISCS: ... ` branch that transparentised the vegetation disc material (`itu_ceiling_board`) but no `else` branch to explicitly activate it. As a result, Sionna loaded `itu_ceiling_board` at its internal default (ε_r ≈ 1, σ ≈ 0.02 S/m, S = 0.10), and the calibration Phase 0 scalar inflated to +9.7 dB rather than the expected −2.3 dB. All subsequent material optimisation converged to parameters that compensated for near-transparent discs — producing a scatter budget inconsistent with the evaluation scene state, where the discs were nominally active. The fix adds an explicit `else` branch that sets `itu_ceiling_board` to ε_r = 17, σ = 0.15 S/m, S = 0.50 before any PathSolver invocation (commits `470ab4a`, `2959d6b`). The Phase 0 scalar diagnostic (should be ≈ −2.3 dB for the Nottingham 2695 MHz scene with discs active; was +9.7 dB before the fix) was the primary indicator used to detect this discrepancy.

**CMA-ES S-cap tuning.** CMA-ES calibration runs for London 1802 MHz stalled at local minima when per-material scattering coefficient caps were set too tightly. With S_max(brick) = 0.35, the calibration RMSE plateaued at 15.6 dB with no improvement over 200 evaluations. Raising to S_max = 0.40 reduced this to 14.9 dB but produced brick S = 0.400 exactly at the cap boundary after 348 evaluations — a diagnostic signature that the optimiser was trapped against the bound rather than at a genuine minimum. The scatter flood observed in an earlier calibration run (Run 1, Section 4.2) had been caused not by brick or concrete scatter but by `concrete_barrier` (S = 0.949, at its uncapped ceiling) and uncapped `metal_barrier` conductivity; both were independently fixed by locking metals as perfect conductors and capping `concrete_barrier` at S ≤ 0.70. Raising brick and concrete S_max to 0.45 was therefore safe, and allows the calibration to descend past the prior plateau.

**[FIGURE 4.6 — PLACEHOLDER — requires real notebook output, not fabricated]**
*Calibration convergence plot: calibration RMSE (dB) versus CMA-ES generation number, showing convergence toward the Monte Carlo noise floor.*

**[FIGURE 4.7 — PLACEHOLDER — requires real notebook output, not fabricated]**
*Runtime scattering-coefficient sensitivity sweep (`CELL 8c`): RMSE/R² as a function of a runtime-overridden scattering coefficient, independent of the full joint-parameter search.*

Note: the coverage-map comparison and coarse-vs-detailed geometry figures flagged as placeholders in Chapter 3 (Figures 3.3 and 3.7), and the vegetation disc-layer schematic in Chapter 3 (Figure 3.4), are not repeated here — they belong to the methodology-level illustration of those concepts, not to this chapter's implementation-level record.

---

*Figures 4.3–4.7 are marked as placeholders because they require running the actual notebooks and capturing real output — this environment has no GPU, no Sionna RT installation, and no access to the underlying scene/CSV files needed to produce them, so none have been fabricated. Figures 4.1 and 4.2 are original diagrams built from verified source material (the notebook architecture and the documented building-height fallback chain).*

*References for this chapter reuse [3], [5], [6], [8], [15], [16], [17], [18], [28] from Chapters 1–3 and newly introduce [31] (CMA-ES). See `references.md` for the full verified reference list shared across all chapters.*
