# Chapter 2 — Literature Review (State of the Art)

This chapter provides a critical, structured review of existing scientific and technical knowledge relevant to calibrated ray-tracing propagation modelling. It summarises and compares key theories, methods, and prior findings, distinguishes what is well established from what remains uncertain, and identifies the specific gap in current knowledge that this thesis addresses.

## 2.1 Background of the Research Area

Propagation modelling provides the mathematical and physical framework for estimating radio wave behaviour, underpinning coverage prediction, interference estimation, and resource planning. This section reviews the classical empirical models, the deterministic ray-tracing alternative, and the material and geometric modelling considerations that together form the theoretical foundation for the methodology developed in this thesis.

### 2.1.1 Classical Propagation Models: Strengths and Limitations

**Free-Space Path Loss (FSPL).** The FSPL model represents the idealised case of unobstructed signal propagation through free space, calculating attenuation from distance and frequency alone:

**Equation (2.1):** FSPL (dB) = 20 log₁₀(d) + 20 log₁₀(f) + 32.44

where *d* is distance in kilometres and *f* is frequency in MHz. This form follows directly from the Friis transmission formula [11]. Despite its analytical simplicity, FSPL excludes reflection, diffraction, and scattering, limiting its applicability beyond idealised line-of-sight links [2], [11].

**Okumura–Hata model and the COST-231 extension.** The Hata model is an empirical extension of Okumura's measurements, estimating median path loss in urban areas as:

**Equation (2.2):** PL_urban = 69.55 + 26.16 log₁₀(f) − 13.82 log₁₀(h_b) − a(h_m) + (44.9 − 6.55 log₁₀(h_b)) log₁₀(d)

where *f* is frequency in MHz (150–1500 MHz), *h_b* is base station antenna height in metres, *h_m* is mobile antenna height in metres, *a(h_m)* is a city-size-dependent correction term, and *d* is distance in km [9]. The COST-231 extension adapts this formula for frequencies up to 2 GHz and dense urban environments [10], but like the original Hata model it relies on statistically fitted parameters and does not represent the geometry or material composition of the specific environment being modelled [9], [10].

**[TABLE 2.1]**

| Model | Frequency | Assumptions | Advantages | Limitations |
|---|---|---|---|---|
| FSPL [11] | Any | Free space, no obstructions | Analytical, simple | Ignores reflections, diffraction |
| Okumura–Hata [9] | 150–1500 MHz | Empirical, field data | Good for large-scale planning | No detailed geometry/material representation |
| COST-231 [10] | Up to 2 GHz | Empirical, urban adaptation | Dense urban applicability | Limited spatial accuracy |

*Table 2.1 — Comparative overview of classical propagation models.*

**Limitations in complex historical/dense urban settings.** Classical models assume environmental homogeneity and uniform building distributions. In dense, architecturally varied urban environments — such as the Nottingham city-centre site studied in this thesis, with its narrow streets, mixed building ages, and varied façade materials — such assumptions introduce significant inaccuracies. Classical models also offer coarse spatial resolution, typically on the order of 100 m or more, insufficient for applications such as small-cell deployment or site-specific link-budget analysis that require spatially precise, location-specific prediction [9], [10].

### 2.1.2 Ray Tracing: A Deterministic Modelling Solution

Ray Tracing (RT), founded on geometric optics, explicitly models signal interaction with environmental geometry and materials, capturing multipath propagation directly rather than through statistical averaging [2]. Each electromagnetic wave is represented as a discrete ray traced through a three-dimensional scene; at the receiver, the total electric field is the coherent sum of all resolved multipath rays:

**Equation (2.3):** E_total = Σᵢ₌₁ⁿ Eᵢ · e^(−jφᵢ)

where *Eᵢ* and *φᵢ* are the amplitude and phase of the *i*-th ray. This explicit representation makes RT well suited to capturing multipath-induced fading and delay spread, which are central to the failure modes investigated in this thesis (see Chapters 5–6) [2].

**[FIGURE 2.1 — PLACEHOLDER]**
*Illustration of ray-tracing propagation mechanisms in an urban street canyon: direct/LOS ray, specular reflection off a façade, edge diffraction at a rooftop or corner, and diffuse scattering off a rough surface. To be inserted.*

RT models three principal interaction mechanisms:
- **Reflection** — governed by Snell's law and the Fresnel equations, which relate reflected and transmitted field amplitude to the incidence angle and the material's electromagnetic properties [2].
- **Diffraction** — commonly modelled using the Uniform Theory of Diffraction (UTD), which extends geometrical optics to the shadow and reflection-boundary transition regions around edges such as rooftops and building corners, and is essential for representing non-line-of-sight propagation around urban corners [23].
- **Scattering** — handled through empirical or surface-roughness-based models representing diffuse re-radiation from irregular surfaces (brickwork, foliage, vegetation) that cannot be captured by specular reflection alone [2].

Together these mechanisms give RT significantly improved spatial resolution and explicit material sensitivity compared with the classical empirical models of Section 2.1.1, at the cost of requiring accurate three-dimensional geometry and calibrated material data as direct inputs [2].

### 2.1.3 Material Modeling and Spatial Resolution

Accurate RT simulation requires precise characterisation of the electromagnetic properties of the materials present in the scene: surfaces such as brick, concrete, and glass interact with incident waves differently, and these differences materially affect predicted path loss.

**ITU-R material standards.** ITU-R Recommendation P.2040 provides standardised methods and reference values for the permittivity, conductivity, and reflection/transmission behaviour of common building materials as a function of frequency [17], [22]. Example reflection-loss figures at 2.4 GHz are sometimes quoted for brick, glass, and concrete walls in secondary literature discussing this recommendation.

> **Caution — unverified figures.** I could not independently confirm specific numeric reflection-loss values (e.g., "brick ≈ 8 dB," "glass ≈ 4 dB," "concrete ≈ 10–12 dB" at 2.4 GHz) against the primary ITU-R P.2040-1 [22] document or any secondary source in this session's research. Per this project's citation-verification rule, these figures should not be presented as confirmed ITU-R values until checked directly against the recommendation's own tables — see `references.md`, entry [22]. This thesis's own calibration work (Chapters 4–5) instead derives material permittivity, conductivity, and scattering coefficients directly from measurement-based Powell optimisation, referencing ITU-R P.2040-2 [17] and P.833-10 [16] only for initial parameter bounds — so the specific values used later in the thesis do not depend on resolving this citation.

**[TABLE 2.2 — PLACEHOLDER]**
*Literature-reported material reflection-loss/EM-property values by frequency (brick, concrete, glass) once the ITU-R P.2040-1 [22] figures above are verified against the primary source, alongside this thesis's own calibrated values from Chapter 5 for comparison. To be inserted.*

**Importance of geometry fidelity.** Spatial accuracy in the scene model is as important as material accuracy. In this thesis, the Nottingham (dense urban) and Scar Hill (rural) scenes are built from UK Environment Agency LiDAR digital terrain and surface models [8] combined with OpenStreetMap building footprints, preserving building outlines, terrain relief, and vegetation canopy structure at metre-scale resolution (Chapter 3 describes this scene-construction pipeline in full, including the role of Blender in material/texture preparation rather than manual building-by-building modelling).

### 2.1.4 Vegetation Attenuation, Dual-Slope Propagation, and Differentiable Ray Tracing

Two further propagation phenomena recur throughout the literature and are directly relevant to this thesis's scope. First, at short range in urban macrocell geometries, basic transmission loss is commonly characterised by two slopes separated by a breakpoint distance determined by transmitter height, receiver height, and frequency; ITU-R Recommendation P.1411-10 formalises this dual-slope behaviour for outdoor short-range systems [15]. Second, vegetation introduces attenuation that is difficult to model geometrically: the empirical Weissberger model, developed from measurements between 230 MHz and 95 GHz, was among the first widely used models for foliage-obstructed links [18], and has since been supplemented by the more recent ITU-R Recommendation P.833-10, which extends vegetation attenuation modelling up to 100 GHz using a saturating exponential form [16]. Both remain empirical corrections layered on top of, rather than derived from, the underlying geometric propagation mechanism described in Section 2.1.2.

Recent years have also seen the emergence of GPU-accelerated, differentiable ray tracers — notably Sionna RT, built on the Mitsuba 3 rendering engine [13] and the Dr.Jit differentiable compiler [12] — which make gradient-based calibration of material and scene parameters computationally practical at a scale not previously accessible [3]. This development underpins the broader digital-twin vision for 6G network planning introduced in Chapter 1 [4].

## 2.2 Review of Existing Approaches

**Classical empirical approaches.** Okumura–Hata [9] and its COST-231 extension [10] remain widely used for macro-level network planning because of their low computational cost and minimal input data requirements, but as discussed in Section 2.1.1 they operate at coarse spatial resolution and cannot represent site-specific geometry.

**Deterministic ray tracing and its calibration.** Site-specific ray tracing has a long history in radio propagation research [2], and recent work has focused heavily on *calibrating* ray tracers against real measurements rather than relying on generic material assumptions. Kanhere, Poddar, and Rappaport calibrated NYURay, a 3D mmWave and sub-THz ray tracer, against 28 GHz, 73 GHz, and 142 GHz channel measurements collected in indoor, outdoor, and factory scenarios, obtaining a standard deviation in directional multipath power error of under 3 dB indoors and under 2 dB outdoors and in factory environments after calibration [19]. Separately, Hoydis et al. introduced a gradient-based calibration method for Sionna RT that jointly optimises differentiable parametrisations of material properties, scattering, and antenna patterns against measured channel impulse responses, validating it on synthetic data and real indoor measurements from a distributed MIMO channel sounder [21].

**Data-driven alternatives.** A parallel body of work addresses propagation prediction with machine learning rather than explicit geometric simulation. Levie et al.'s RadioUNet uses a convolutional neural network trained on a large simulated dataset (RadioMapSeer) to estimate 2D radio maps directly from city geometry, reporting strong accuracy at a fraction of the computational cost of full ray tracing [20]. Such approaches trade physical interpretability and generalisation to unseen geometries for prediction speed.

**Validation against real urban measurements.** Fewer studies validate ray-tracing fidelity directly against real outdoor cellular measurements at sub-6 GHz frequencies. Manukyan et al. evaluated Sionna-based ray tracing against real 4G/5G measurements collected across six base stations in Rome (0.8–4 GHz), using Spearman rank correlation between measured and simulated received power and k-nearest-neighbour localisation accuracy as fidelity metrics, and found that antenna location and orientation assumptions were decisive to simulator fidelity — greedy re-optimisation of these assumptions alone improved correlation by 5% to 130% depending on the base station [7].

**[FIGURE 2.2 — PLACEHOLDER]**
*Taxonomy of propagation modelling approaches: Empirical (Okumura–Hata, COST-231, FSPL) / Deterministic Ray Tracing (image-based, SBR, Sionna RT) / Data-driven (RadioUNet). To be inserted.*

**[TABLE 2.3 — PLACEHOLDER]**
*Comparison of reviewed calibration studies: NYURay [19] / Sionna RT gradient-based calibration [21] / RadioUNet [20] — columns: frequency range, environment type, calibration method, reported accuracy metric. To be inserted.*

## 2.3 Critical Analysis of Existing Work

The reviewed literature establishes that calibrated ray tracing can achieve strong accuracy, but this has predominantly been demonstrated in two settings that differ from the one this thesis addresses. NYURay's calibration results are strongest at mmWave and sub-THz frequencies (28–142 GHz) over indoor, outdoor-microcell, and factory distances [19], while the Sionna RT differentiable calibration method has so far been validated primarily on synthetic scenes and a single real indoor MIMO measurement set [21]. Neither directly demonstrates calibration accuracy across multiple sub-6 GHz macrocell frequencies at the same outdoor urban site — the regime in which the ITU-R P.1411 dual-slope breakpoint [15] and vegetation attenuation [16], [18] are most consequential, since breakpoint distances at these frequencies (hundreds of metres to just over a kilometre, given typical macrocell heights) fall inside the range of interest for network planning rather than being negligible as at mmWave.

The vegetation and dual-slope literature itself provides physical models but not a systematic account of how they interact with ray-tracer calibration. Weissberger [18] and ITU-R P.833-10 [16] specify attenuation as a function of foliage depth, but neither addresses how attenuation should be combined with a surface-based ray tracer that, by construction, computes electromagnetic interactions only at discrete surface intersections (Section 2.1.2) and cannot represent volumetric absorption through a tree canopy directly — a limitation that becomes more severe as wavelength shrinks toward the physical scale of vegetation structures. Similarly, ITU-R P.1411-10's breakpoint formula [15] defines where LOS and NLOS regimes separate, but the literature reviewed here does not address the practical calibration consequence: fitting a ray tracer's free parameters to measurements spanning both regimes risks averaging over two physically distinct propagation mechanisms.

The data-driven alternative represented by RadioUNet [20] achieves high accuracy efficiently, but at the cost of requiring large, environment-specific training data and offering limited insight into which physical mechanism (reflection, diffraction, vegetation attenuation) is responsible for a given prediction error — a diagnostic capability that a calibrated ray tracer retains by construction (Table 2.1, Section 2.1.1).

Finally, Manukyan et al.'s finding that ray-tracing fidelity against real measurements is highly sensitive to antenna placement and orientation assumptions [7] is a caution rather than a solution: it demonstrates that ray-tracing accuracy cannot be assumed from the simulator alone and must be established empirically for each deployment scenario, but its evaluation metrics (rank correlation, localisation accuracy) do not directly report the path-loss-level accuracy metrics (R², RMSE, bias) that are standard in network planning and that this thesis uses throughout.

## 2.4 Identification of Research Gap

Taken together, the reviewed literature has separately established: (i) that ray tracing can be calibrated to real measurements with strong accuracy at mmWave/sub-THz frequencies and short-to-medium range [19]; (ii) that gradient-based, differentiable calibration is computationally practical using modern frameworks such as Sionna RT [3], [21]; (iii) physical models for vegetation attenuation [16], [18] and dual-slope breakpoint behaviour [15] at sub-6 GHz; and (iv) that ray-tracing fidelity against real urban measurements is sensitive to scene and antenna assumptions and must be empirically validated rather than assumed [7].

No study identified in this review combines these elements into a single, systematic evaluation: a purely geometric, calibrated ray tracer validated against a large, public, multi-frequency measurement dataset spanning sub-6 GHz macrocell frequencies (915 MHz–3602 MHz) at the same dense urban site, extended to a rural comparison site, with explicit attention to how vegetation modelling choice and dual-slope-aware calibration range affect the resulting accuracy at each frequency. This is the gap this thesis addresses, directly motivating the research questions and objectives set out in Section 1.5: quantifying how calibrated ray-tracing accuracy varies with frequency, establishing what scene and vegetation modelling choices are required as wavelength decreases, and identifying the accuracy ceiling achievable through geometry-and-material calibration alone before any learned or statistical residual correction is introduced.

## 2.5 Sionna RT: Simulation Framework and Real Pipeline

Sionna RT, developed by NVIDIA, is the open-source Python library used throughout this thesis, integrating the Mitsuba 3 rendering engine [13] and the Dr.Jit differentiable compiler [12] for GPU-accelerated ray-tracing simulation [3].

### 2.5.1 Components and Workflow

The pipeline actually used in this thesis (as implemented across `sionna019_scene_builder.ipynb` and the per-frequency simulation notebooks) proceeds as follows:

1. **Terrain acquisition** — UK Environment Agency 1 m LiDAR Digital Terrain and Surface Models are downloaded and merged for the scene area, and a normalised Digital Surface Model (nDSM = DSM − DTM) is computed to recover above-ground clutter height (scene-builder cells CELL 2b–2e) [8].
2. **Terrain and building geometry** — the DTM is sampled onto a regular grid to build a terrain mesh, and OpenStreetMap building footprints are extruded into building PLY meshes, with nDSM-derived heights used to fill gaps in sparse OSM height tags (CELL 3–4). Where finer building detail is required, geometry is authored/refined in Blender, with materials standardised to Sionna-compatible names and exported per material as PLY meshes for import into the scene.
3. **Scene assembly** — all PLY meshes are assembled into a single Sionna 2.0-format scene XML file (CELL B3).
4. **Material assignment** — the scene is loaded into Sionna RT and each surface is assigned a `RadioMaterial` (relative permittivity, conductivity, scattering coefficient), initialised from ITU-R P.2040-2 reference values [17] and later calibrated against measurements (CELL 4A/4B; calibration procedure detailed in Chapter 4).
5. **Transmitter and receiver placement** — the transmitter is placed at the site's documented location and antenna height (CELL 4C), and receivers are extracted from the corresponding Ofcom 2018 drive-test CSV for that site and frequency [5] (CELL 5–6).
6. **Path solving** — Sionna's `PathSolver` traces rays between transmitter and receivers, resolving reflection, diffraction, and scattering interactions (CELL 7, with a stratified distance-band variant in CELL 8 for scattering ON/OFF comparison across the full receiver set).
7. **Vegetation post-processing** — ITU-R P.833-10 or Weissberger vegetation attenuation is applied post-hoc based on the vegetation depth intersected by each path (CELL P.833) [16], [18].
8. **Evaluation** — simulated path loss is compared against the Ofcom measurements to compute bias, RMSE, and R² (CELL REPORT), the metrics used throughout Chapters 5–6.

**[FIGURE 2.3 — PLACEHOLDER]**
*Side-by-side comparison of coarse vs. detailed urban geometry for the Nottingham scene: (a) OSM-only building footprints with default heights, (b) full LiDAR/nDSM-informed geometry with Blender-refined building detail. To be inserted.*

**[FIGURE 2.4 — PLACEHOLDER]**
*Pipeline workflow diagram: EA LiDAR + OSM + Blender geometry → Sionna 2.0 scene XML → RadioMaterial assignment → PathSolver ray tracing → vegetation post-processing → radio environmental map / evaluation metrics. To be inserted.*

### 2.5.2 Hardware and Computational Configuration

Simulations in this thesis are GPU-accelerated. `sionna019_calibration.ipynb` documents the compute configuration directly: an NVIDIA Tesla V100-SXM2-16GB GPU, using Mitsuba's `cuda_ad_rgb` variant with `FORCE_CPU_RT=False` (i.e., GPU ray tracing, not a CPU fallback). This was independently confirmed via a live `nvidia-smi` query on the training VM (hostname `sti-virtual-machine`), which reports:

| Parameter | Value |
|---|---|
| GPU | NVIDIA Tesla V100-SXM2-16GB |
| GPU memory | 16,384 MiB (16 GB) |
| Driver version | 580.126.20 |
| CUDA version | 13.0 |
| Host | Virtual machine (`sti-virtual-machine`) |

At the time of the query, GPU utilisation was at 100% across four concurrent Python processes (two `sionna_gpu`/`sionna_gpu_final` conda environments plus two unlabelled `python` processes), consistent with CLAUDE.md's record of multiple calibration runs (2695 MHz, 3602 MHz, London 915 MHz) executing in parallel on this machine.

> **[PLACEHOLDER — still pending]** CPU core count and system RAM are not shown by `nvidia-smi` and have not yet been provided; add the output of `lscpu` and `free -h` (or equivalent) here once available.

### 2.5.3 Installation and Software Environment

The exact, pinned software environment is documented in the project's `requirements_sionna019.txt` and is reproduced here for completeness:

```
Core framework:   sionna==0.19.2, tensorflow==2.15.0, keras==2.15.0
RT backend:       mitsuba==3.5.2, drjit==0.4.6
Numerics:         numpy==1.26.4, scipy==1.15.3
Geospatial/OSM:    osmnx==2.0.7, geopandas==1.1.3, shapely==2.1.2,
                   pyproj==3.7.1, rasterio==1.4.4
Visualisation:     matplotlib==3.10.8, pyvista==0.47.3, open3d==0.19.0, plotly==6.7.0
```

Installation follows the standard Python packaging workflow: create an isolated environment (e.g., `conda create -n sionna019 python=3.10`), activate it, and install the pinned dependency set with `pip install -r requirements_sionna019.txt`. Note that this project also contains a separate, Sionna 2.0-targeted notebook set (`sionna2_*`) using a newer Sionna/Mitsuba/Dr.Jit combination; the two environments are kept independent to avoid version conflicts, consistent with the scene-format distinction between the legacy Sionna 0.19 XML and the Sionna 2.0 XML written by CELL B3.

As open-source software, Sionna RT supports academic rigour, reproducibility, and flexibility relative to proprietary ray-tracing tools, which is part of why it was selected for this project [3].

## 2.6 Related Research and Relevance

Beyond the calibration-focused studies already reviewed in Section 2.2, several earlier works established that site-specific, geometry-aware modelling is necessary to capture real urban propagation behaviour. Chizhik et al. measured MIMO channels in Manhattan and demonstrated substantial, geometry-driven variation in angular and delay spread between sites — variation that classical statistical models cannot reproduce because they do not represent individual street and building geometry [24]. Rappaport et al.'s wideband millimetre-wave measurement campaign further showed that propagation characteristics are highly sensitive to the specific materials and geometry of the measurement environment, reinforcing the case for material-aware, site-specific simulation rather than generic path-loss exponents [25].

More directly comparable to this thesis is a 2025 University of Bologna undergraduate/master's thesis that used Sionna RT to generate high-resolution radio environmental maps for Bologna's historic centre, with building geometry authored in Blender and CPU-based ray-tracing execution [26]. That work demonstrates Sionna RT's applicability to architecturally complex, dense historic urban environments and reports qualitative phenomena such as waveguiding beneath porticoes and diffraction in narrow alleyways. It differs from this thesis in three respects relevant to the research gap identified in Section 2.4: it targets a single frequency and city rather than a multi-frequency, multi-site comparison; it does not calibrate material properties against an independent, public path-loss measurement dataset (relying instead on qualitative/simulated observations); and its CPU-based execution limits the sample counts practical for Monte Carlo path solving, whereas this thesis's GPU-accelerated pipeline (Section 2.5.2) supports the 30–100 million sample counts used for calibration and evaluation in Chapters 4–5.

This chapter has critically reviewed classical propagation models and their limitations, introduced Ray Tracing as a deterministic, geometry-aware alternative, discussed material and geometry modelling considerations, described the Sionna RT simulation framework and this thesis's own pipeline, and situated this work relative to related studies. Together with the research gap identified in Section 2.4, these findings directly inform the methodology developed in Chapter 3.

---

*References for this chapter reuse [2], [3], [4], [5], [7], [8]–[13] from Chapter 1 and add [15]–[26]; see `references.md` for the full, verified reference list shared across all chapters. Note: a "Loyka & Kouki (2008)" citation appearing in an earlier draft could not be verified and has been omitted — see `references.md`, "Not used" section.*
