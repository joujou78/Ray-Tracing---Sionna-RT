# Thesis Brief — Ray Tracing Propagation Modelling with Sionna RT

## Purpose of this document
This is a briefing document for a new Claude session to assist with thesis writing.
It summarises the project, all results, methodology, and key findings.
The full technical reference is in `CLAUDE.md` in the same repository.

---

## Project Summary

**Topic:** Urban and rural radio propagation modelling using Sionna RT 2.0 (NVIDIA differentiable ray tracer), validated against real Ofcom 2018 measurement campaigns at multiple frequencies.

**Objective:** Quantify how well a calibrated geometric ray tracer predicts path loss across frequency bands (915 MHz → 3602 MHz), identify the physics floor, and characterise failure modes (vegetation, dual-slope, coherent interference).

**Tool:** Sionna RT 2.0 — surface-based ray tracer using DrJIT (differentiable), PathSolver (Monte Carlo path sampling), ITU-R material models.

**Datasets:** Ofcom 2018 UK propagation measurements — 4 sites, 4 frequencies.

---

## Sites and Frequencies

| Site | Frequency | Environment | Status |
|------|-----------|-------------|--------|
| Nottingham | 915 MHz | Dense urban | COMPLETE — best R²=0.835 @ 0-750m |
| Nottingham | 1802 MHz | Dense urban | COMPLETE — best R²=0.509 @ 0-1250m |
| Nottingham | 2695 MHz | Dense urban | IN PROGRESS — Run 4 CELL CAL running |
| Nottingham | 3602 MHz | Dense urban | IN PROGRESS — Run 5 CELL CAL running |
| London | 915 MHz | Dense urban | IN PROGRESS — CELL CAL at 8.966 dB |
| Scar Hill | 915 MHz | Rural hilltop | COMPLETE — best R²=0.083 @ 0-1250m |

---

## Key Results

### Nottingham 915 MHz (FINAL)
- **R²=0.835, RMSE=6.0 dB** at 0-750m (ON incoh, 100M eval samples)
- Best result across all sites/frequencies
- Full scene: buildings + terrain + vegetation (OSM/VOM/nDSM) + roads + water + bridges + railways
- MAX_DEPTH=8, 100M eval samples optimal
- Near-range (0-300m) R²~0 from 8 LOS mast-shadow receivers — structural, not calibration

### Nottingham 1802 MHz (FINAL)
- **R²=0.509, RMSE=10.6 dB** at 0-1250m (ON incoh, 15,486-tree scene)
- ON coh collapsed (R²=0.187) — 15,486 trees cause destructive coherent interference at λ=16.7 cm
- Accepted as physics floor: R²~0.44-0.51 matches literature ceiling for pure geometry+material cal
- DISABLE_VEG_DISCS=True, Weissberger post-processing, CAL_FIX_SCATTER=False

### Nottingham 2695 MHz (Run 2 — best so far)
- **R²=0.574, RMSE=12.7 dB** at 0-1250m (ON incoh, Run 2)
- Beats 1802 MHz at same range (R²=0.509) — higher frequency, better spatial resolution
- Dual-slope breakpoint Rbp=916m — calibrating beyond this range mixes physics regimes
- DISABLE_VEG_DISCS=True, P.833 post-hoc vegetation, CAL_MAX_DIST_KM=1.0
- Scattering critical: ON incoh (0.574) vs OFF incoh (0.070) — 50-point gap; model fails without scatter
- Run 4 in progress: N_SCALAR_BINS=10 + LOS/NLOS zone split → target R²~0.60-0.65

### Nottingham 3602 MHz (Run 3 — best so far, FINAL accepted)
- **R²=0.515, RMSE=9.4 dB** at 0-1250m (ON incoh, per-path P.833)
- DISABLE_CANOPY=True required — λ=8.3 cm causes total ray blockage through tree crowns
- Per-path ITU-R P.833 correction (applied per ray segment via paths.vertices)
- Hard NLOS collapse beyond 1250m (R²=-0.634 at 0-1500m)
- Run 5 in progress: disc absorption tuning → target modest improvement

### London 915 MHz (IN PROGRESS)
- CELL CAL at 8.966 dB (30M samples), FTOL imminent
- TX fixed at 25m AGL (bug: scan was selecting 45m — above buildings, near-LOS artefact causing +49 dB bias)
- Expected CELL 8e: R²~0.35-0.50 at 0-750m

### Scar Hill 915 MHz (COMPLETE)
- **R²=0.083** at 0-1250m — SRTM 30m terrain physics floor for rural hilltop site
- Only meaningful improvement: Scottish LiDAR 1m DTM (not yet downloaded)
- Scatter dominant: avg_rays ON=19k-40k vs OFF=55

---

## Frequency Comparison (Nottingham, all FINAL or best-to-date)

| Frequency | Best R² | Range | RMSE | Method | Key finding |
|-----------|---------|-------|------|--------|-------------|
| 915 MHz | **0.835** | 0-750m | 6.0 dB | ON incoh | Best result — short λ, good scatter |
| 1802 MHz | 0.509 | 0-1250m | 10.6 dB | ON incoh | Coherent collapsed; physics floor |
| 2695 MHz | 0.574 | 0-1250m | 12.7 dB | ON incoh | Beats 1802 MHz; dual-slope critical |
| 3602 MHz | 0.515 | 0-1250m | 9.4 dB | ON incoh | Canopy must be disabled; per-path P.833 |

---

## Calibration Methodology

### Scene geometry
- Buildings: 5-material classification (brick/concrete/glass/metal/wood PLYs)
- Terrain: EA LiDAR 1m DTM (Nottingham) / SRTM 30m (rural)
- Vegetation: OSM polygons + VOM LiDAR canopy + nDSM extra (road verges, motorway belts)
- Roads, water (River Trent), bridges, railways

### RT parameters
- PathSolver: Monte Carlo ray sampling
- MAX_DEPTH=8 (915/1802 MHz) / 20 (2695 MHz)
- NUM_SAMPLES_PS=100M for evaluation; 30M for calibration
- Diffraction + edge diffraction enabled

### Calibration pipeline (CELL CAL)
3-phase Powell optimizer:
1. **Phase 0** — scalar offset (1 eval): absorbs antenna gain, cable loss, absolute power uncertainty
2. **Phase 1** — coordinate descent warm-up (skipped in current runs)
3. **Phase 2** — joint Powell refinement: 19 free parameters (ε, σ, S per material + scalar)
- 6 free materials: itu_brick, itu_concrete, itu_glass, itu_wet_ground, itu_very_dry_ground, water_rt
- Fixed: itu_ceiling_board (disc proxy), itu_asphalt (road), itu_metal, canopy/trunk (3D trees)
- MC noise floor at 30M samples: ±0.12 dB → Powell cannot improve below this

### Post-processing (CELL 8e)
- **Scalar offset**: global additive correction (Phase 0 output)
- **Bin scalar**: per-distance-bin mean correction (N_SCALAR_BINS=10)
- **LOS/NLOS zone split**: separate mean offsets for LOS (d < Rbp) and NLOS (d ≥ Rbp) — new
- **Vegetation attenuation**: Weissberger (915/1802 MHz) or ITU-R P.833-10 (2695/3602 MHz)
- **Per-path P.833** (3602 MHz only): applied per ray segment via paths.vertices

---

## Key Physics Findings

### 1. Coherent vs incoherent summation
- 915 MHz: both methods comparable
- 1802 MHz: ON coh collapsed (R²=0.187) — 15,486 trees cause destructive coherent interference
- 2695 MHz: ON coh competitive (R²=0.436) — DISABLE_CANOPY=True reduces destructive interference
- 3602 MHz: ON coh negative R² — per-path correction changes amplitude, coherent sum unstable

### 2. Scattering is essential
- Without scattering (OFF methods): R² collapses at all frequencies
- 2695 MHz: ON incoh (0.574) vs OFF incoh (0.070) — 50-point gap
- Scattering provides 50+ "scatter-only" receiver paths (no LOS/specular) at 2695 MHz

### 3. Dual-slope breakpoint (ITU-R P.1411)
Rbp = 4 × hBS × hUT × f/c (hBS=17m, hUT=1.5m)

| Frequency | Rbp | Effect |
|-----------|-----|--------|
| 915 MHz | 311 m | LOS regime very short |
| 1802 MHz | 613 m | Within 0-1.5km range |
| 2695 MHz | 916 m | Critical — calibrate within 1.0km only |
| 3602 MHz | 1225 m | Near edge of evaluation range |

Calibrating across Rbp mixes LOS and NLOS physics → sign-flip in bias → R² collapse.

### 4. Vegetation modelling by frequency
| Frequency | Approach | Reason |
|-----------|----------|--------|
| 915 MHz | Disc geometry active + Weissberger | λ=32.7 cm, disc scatter realistic |
| 1802 MHz | DISABLE_VEG_DISCS=True + Weissberger | Scatter flood with discs active |
| 2695 MHz | DISABLE_VEG_DISCS=True + P.833 | Weissberger under-estimates ~40% above 2 GHz |
| 3602 MHz | DISABLE_CANOPY=True + per-path P.833 | λ=8.3 cm → total ray blockage through crowns |

### 5. Physics floor
- Literature: R²~0.5 ceiling for pure geometry+material calibration in dense urban (arXiv:2507.19653)
- 3GPP TR 38.901 UMa NLOS shadow fading: σ_SF=7.82 dB (2695 MHz) / 6.0 dB (3602 MHz)
- Reaching R²>0.70 requires hybrid RT + neural residual correction (out of scope)

---

## Material EM Properties (2695 MHz Run 3 calibrated)

| Material | εᵣ | σ (S/m) | S | Notes |
|----------|-----|---------|---|-------|
| itu_brick | 3.02 | 0.0723 | 0.509 | high scatter |
| itu_concrete | 6.34 | 0.1233 | 0.513 | high scatter |
| itu_glass | 7.49 | 0.0209 | 0.409 | |
| itu_wet_ground | 24.10 | 0.1855 | 0.250 | |
| itu_very_dry_ground | 3.58 | 0.0250 | 0.279 | |
| canopy_itu_vegetation | 1.50 | 0.0033 | 0.400 | near-transparent |
| itu_ceiling_board | 1.00 | 0.0000 | 0.050 | transparent (DISABLE_VEG_DISCS=True) |

---

## Key Literature References

| Reference | Used for |
|-----------|----------|
| 3GPP TR 38.901 v18 (2024) | LOS/NLOS path loss models, σ_SF=7.82 dB UMa NLOS, dual-slope Rbp |
| ITU-R P.1411-12 (2019) | Dual-slope breakpoint formula |
| ITU-R P.833-10 (2021) | Vegetation attenuation: A = Am(1−exp(−dγ/Am)); Am=25 dB, γ=2.0 dB/m at 3 GHz |
| ITU-R P.2040-2 (2021) | Building material EM properties; brick σ=0.038 S/m (freq-independent) |
| Weissberger (1982) | Empirical vegetation model for 915/1802 MHz |
| arXiv:2507.19653 | R²~0.5 ceiling for pure geometry+material cal in dense urban at 1.8 GHz |
| NYURay (Ju et al., NYU WIRELESS) | 3.2/5.8 dB LOS/NLOS RMSE with zone corrections + per-building material |
| NVLabs diff-rt-calibration (Hoydis et al.) | Gradient-based / neural material calibration |
| RadioUNet (Levie et al., 2021) | R²~0.80 urban outdoor with physics prior + CNN |

---

## Thesis Structure (to be filled by student)

Paste your chapter structure below and we will develop each chapter together.

Recommended structure for a propagation modelling thesis:

1. **Introduction** — motivation, objectives, contributions
2. **Background** — ray tracing theory, propagation mechanisms, related work
3. **Methodology** — Sionna RT, scene construction, calibration pipeline
4. **Scene Construction** — Nottingham urban scene, terrain, vegetation, buildings
5. **Results: Nottingham 915 MHz** — best result, scene evolution, calibration analysis
6. **Results: Multi-frequency Nottingham** — 1802/2695/3602 MHz comparison
7. **Results: London and Scar Hill** — urban/rural generalisation
8. **Discussion** — frequency trends, physics floor, failure modes, limitations
9. **Conclusion** — summary, contributions, future work

---

## Working Branch
`claude/cool-cori-rrWbY` on `joujou78/Ray-Tracing---Sionna-RT`

## Current Run Status (2026-08-16)
- 2695 MHz Run 4 CELL CAL: Phase 2 eval 1 = 14.524 dB, ~16 hrs remaining
- 3602 MHz Run 5 CELL CAL: eval 198, best = 14.924 dB, FTOL soon
- London 915 MHz CELL CAL: eval 150, 8.966 dB, FTOL imminent
- Scar Hill 915 MHz: ready to run after git pull
