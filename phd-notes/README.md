# PhD Research: Ray Tracing for Path Loss Prediction in Telecommunications

Research notes on open-source ray tracers and public measurement datasets for **urban outdoor** path loss prediction.

**Target bands:** 900 MHz, 1.8 GHz, 2.6 GHz, 3.6 GHz, 5.8 GHz
**Scenario:** Urban outdoor

> Status: literature and tools search in progress. All information should be verified against the original sources.

---

## 1. Open-Source Ray Tracers

| Tool | Language / Engine | Why it matters | Note |
|---|---|---|---|
| **NVIDIA Sionna RT** | Python, GPU (Mitsuba 3 / Dr.Jit) | Most widely used in current research; differentiable, allows material calibration | Main recommended tool |
| **Opal** | C++, NVIDIA OptiX | Peer-reviewed (PLoS ONE 2021), couples with OMNeT++; MIT license | Repo: https://gitlab.com/esteban.egea/opal |
| **DiffeRT / DiffeRT2d** | Python, JAX | Differentiable, multiple reflections and diffractions, published in JOSS | UCLouvain; solver at https://github.com/jeertmans/fpt-jax |
| **PyLayers** | Python | Older general-purpose wireless simulator | Mature but less active |

**Supporting tool:** OpenGERT automates terrain and building data collection to build Sionna RT scenes.

**Commercial reference tools (not open source, used as benchmarks):** Altair WinProp, Remcom Wireless InSite, Ranplan.

**Note:** NYURay (NYU WIRELESS) is well validated, but its open-source status is not confirmed.

### Evidence relevant to our bands
- Sionna RT validated at 5.9 GHz in an urban vehicular scenario (arXiv: 2610.20387).
- Sionna RT tested against real urban cellular data (0.8 to 4 GHz) in Rome (arXiv: 2507.19653).
- Sionna RT tested at 5G n78 (3.349 GHz) indoors with an OAI testbed (arXiv: 2605.10352).

---

## 2. Accuracy Notes and Possible PhD Gaps

- **Key review paper:** Mbugua et al., "Review on Ray Tracing Channel Simulation Accuracy in Sub-6 GHz Outdoor Deployment Scenarios," IEEE OJAP, 2020. DOI: 10.1109/OJAP.2020.3041953. Most RT tools reach a mean path loss error below 4 dB in sub-6 GHz outdoor scenarios.
- **Calibration matters:** a Glasgow study found calibration reduced mean error by 46.3% (MATLAB RT) and 58.1% (Sionna RT), but a calibrated log-distance model still had the lowest error.
- **Antennas dominate:** in urban outdoor tests, antenna placement and orientation affected accuracy more than solver parameters.
- **Materials:** most works assign uniform materials to the whole scene; material properties are frequency dependent across 900 MHz to 5.8 GHz.
- **Map accuracy:** common map sources (e.g., OpenStreetMap) rarely publish their accuracy.
- **Residual urban error:** precise geometry and antenna models are necessary but not sufficient (Rome study).
- **900 MHz (own assessment, to verify):** rooftop and edge diffraction is dominant at lower frequencies; check how the chosen Sionna version models diffraction.
- **Sionna limitation:** no integrated measurement data or built-in calibration mechanism. Calibration and material estimation are strong PhD research directions.

---

## 3. Public Measurement Datasets (non-UK)

### 3.1 Vienna 4G/5G Drive-Test Dataset (Austria) - best fit for RT
- City-scale georeferenced LTE and 5G NR measurements.
- Includes estimated BS locations, sector azimuths, antenna heights, and high-resolution building and terrain models.
- Collected June 2024 to March 2025, about 100 km2 (per arXiv v2).
- Bands: LTE 800/1800/2600 MHz, NR 2100/3500 MHz. No 900 MHz or 5.8 GHz.
- Includes a `pathloss_db` column. Full review: paper-review-2603.02638.md
- License: CC BY 4.0
- Paper: https://arxiv.org/abs/2603.02638

### 3.2 Rome 4G / NB-IoT / 5G NSA Dataset (Italy)
- LTE Bands 1, 3, 7, 20; NB-IoT; 5G NR n78. Covers ~0.8 to 4 GHz.
- Collected Dec 2020 to Jan 2021 on two operators' networks.
- Access: IEEE DataPort (free login), DOI: 10.21227/7a8s-nt68
- Already used to evaluate Sionna RT (arXiv: 2507.19653): good for reproducing a baseline.

### 3.3 DoNext Dataset (Dortmund, Germany)
- 4G and 5G measurements: mobile, static and rail campaigns over two years.
- Not confirmed: whether BS locations or 3D building models are included.

### 3.4 Excluded
- Ofcom (UK): excluded by choice.

### Gap: 5.8 GHz
None of the datasets above covers 5.8 GHz. Options: own measurements (SDR or spectrum analyzer with a known transmitter), or Wi-Fi / V2X datasets (not yet verified).

### Validation requirement
For path loss validation, the dataset needs known transmit power, antenna pattern, BS position and height. Datasets with only RSRP force estimation of these and add error.

---

## 4. Suggested Starting Steps

1. Read the Mbugua et al. 2020 review and the Sionna RT technical report.
2. Install Sionna RT and run urban tutorials with OpenGERT or Blender + OpenStreetMap scenes.
3. Reproduce the Rome dataset comparison as a baseline.
4. Move to the Vienna dataset for calibrated RT validation.
5. Plan own measurements for 5.8 GHz.

---

## 5. Paper Reviews

- paper-review-2507.19653.md: Sionna RT realism in Rome (Manukyan et al., 2025)
- paper-review-2603.02638.md: Vienna 4G/5G Drive-Test Dataset (Wiedner et al., 2026)
- paper-review-2510.10190-DDRD.md: RIS deployment with calibrated Sionna RT, UK data (Beyraghi et al., 2025). Contains a material calibration method: RSRP error std reduced from 5.71 to 2.57 dB.

- paper-review-GT-LOD3.md: LOD3 building reconstruction benchmark (Kim, Wysocki et al., ISPRS 2026). Automatic LOD3 not mature (window detection F1 56.5%).

**Topic deep dives:**
- topic-material-calibration.md: Sionna material model, gradient-based calibration (Hoydis et al. 2024), and DDRD adaptation
- topic-uk-digital-twin.md: TUM2TWIN layers mapped to UK sources; Defra findings (EA aerial photography, VOM, Trees Outside Woodland)

**Data notes:**
- data-ofcom-london.md: Ofcom London 915.95 / 3602.5 MHz files, path loss formula, EIRP open issue, band comparison

**Site plan:**
- lod3-build-plan-london.md: concrete LoD3 build plan for the London Ofcom site (zones, tiles TQ28SE/TQ38SW, Rx map-matching, Tx building priority, pilot)

**Code reviews / handovers:**
- handover-scene-builder-review-lod3.md: review of the Stevenage scene builder notebook (8 issues) + automatic LoD3 module proposal (no Blender)

**Methodology drafts:**
- methodology-3d-scene-lod3-sionna.md: step-by-step pipeline to build a multi-LoD (LoD1/2/3) scene for Sionna RT, with QA, export, variants and validation plan

---

## 6. Open Tasks

- [ ] Check whether DDRD repo includes the material calibration code
- [x] Read Hoydis et al., "Learning radio environments by differentiable ray tracing" (IEEE TMLCN 2024): see topic-material-calibration.md
- [ ] Verify ITU-R P.2040 frequency-dependent material models
- [ ] Ofcom ITU-R drive test (449, 915, 1802, 2695, 3602, 5850 MHz): check TX antenna patterns and EIRP in documentation
- [ ] Choose first Ofcom city; check EA LiDAR point cloud density and survey dates (match 2015 to 2018)
- [ ] Evaluate street-level imagery (Mapillary) licensing for window/glass detection
- [ ] Consider LOD1 vs LOD2 vs LOD3 per-frequency study (TUM2TWIN LOD3 model)
- [ ] Check if frequency-dependent calibration across bands exists for urban outdoor

- [ ] Search for a public 5.8 GHz urban outdoor dataset
- [ ] Verify DoNext dataset contents
- [ ] Check Sionna RT diffraction support in the latest version
- [ ] Confirm NYURay open-source status
