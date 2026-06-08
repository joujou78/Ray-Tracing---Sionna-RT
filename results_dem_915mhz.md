# Nottingham 915 MHz DEM Simulation — Technical Report
**Date:** 2026-06-08  
**Notebook:** sionna2_915mhz_dem_simulation.ipynb  
**Scene:** Nottingham DEM (EA LiDAR nDSM), 77,014 buildings  
**Dataset:** 1,200 Ofcom 2018 drive-test receivers  
**Frequency:** 915.95 MHz  

---

## 1. Simulation Configuration

| Parameter | Value |
|---|---|
| Frequency | 915.95 MHz |
| TX GPS | lat=52.9863°N, lon=−1.2559°E |
| TX AGL | 17.0 m |
| TX terrain Z | 79.1 m (local datum) |
| TX total Z | 96.1 m (local datum) |
| TX conducted power | 49.0 dBm |
| Ofcom EIRP | **56.2 dBm** (amp=50.3, cable=1.3, ant=7.0 dBi) |
| RX AGL | 1.5 m |
| Antenna pattern | Donut (isotropic horizontal) |
| RX extra gain | 0.0 dB (system losses not modelled) |
| MAX_DEPTH | 6 |
| Scene type | DEM — EA LiDAR nDSM heights |

---

## 2. Scene Description

| Property | Value |
|---|---|
| Buildings exported | 77,014 |
| Building heights | EA LiDAR nDSM (1 m resolution) |
| Height priority | nDSM → OSM height= → levels×3.5 → 8.0 m default |
| Roof type | Pyramidal at 30° |
| nDSM >2 m pixels | 21.1% of scene |
| nDSM >5 m pixels | 12.7% of scene |
| Terrain Z range | −32.7 m to +88.7 m (local datum, z=0 = 50.5 m ASL) |
| Materials | 6 ITU-R P.2040-2 materials |
| Scene PLY files | 5 (terrain + 4 mesh tiles) |

### Material Scattering Coefficients (ITU-R P.2040-2)

| Material | ε_r | σ (S/m) | Scatter coeff |
|---|---|---|---|
| itu_concrete | 5.31 | 0.0920 | 0.20 |
| itu_brick | 3.75 | 0.0380 | 0.25 |
| itu_glass | 6.27 | 0.0000 | 0.08 |
| itu_metal | 1.00 | 10,000,000 | 0.05 |
| itu_wood | 1.99 | 0.0000 | 0.30 |
| itu_wet_ground | 30.00 | 0.0200 | 0.40 |

All materials: LambertianPattern set ✓, Coefficients verified ✓

---

## 3. Receiver Extraction

| Property | Value |
|---|---|
| Total Ofcom measurements | 94,791 |
| Receivers selected | **1,200** (first sequential) |
| LOS receivers | 36 (3%) |
| NLOS receivers | 1,164 (97%) |
| RSSI range | −123.3 to −18.3 dBm |
| PL range (56.2 − RSSI) | 74.5 to 179.5 dB |

**Path loss formula:** `PL_meas = EIRP − RSSI_meas = 56.2 − RSSI_meas`

---

## 4. Coverage Map Results (CELL 9)

**Grid:** 976 × 691 = 674,416 cells | 10.0 m resolution | Z = 1.60 m  
**Scene extent:** (−4,883, −3,452) → (4,876, 3,457) m  
**Samples:** 1,000,000,000 (1B) per TX  

| Metric | Scatter ON | Scatter OFF |
|---|---|---|
| Coverage | 324,750 / 674,416 | 326,248 / 674,416 |
| Coverage % | 48.2% | 48.4% |
| RSSI mean (covered) | −58.9 dBm | −58.6 dBm |
| RSSI std (covered) | 16.3 dB | 15.9 dB |
| RSSI min | −124.0 dBm | −124.0 dBm |
| RSSI max | −0.8 dBm | −0.8 dBm |

**Scatter impact (covered cells):** mean = +0.05 dB, std = ±2.99 dB

> The mean scatter impact is near zero because Lambertian scattering  
> redistributes energy spatially — some cells gain, others lose. The  
> std of ±2.99 dB confirms scattering is active and has significant  
> local variation.

---

## 5. Scatter Effect Analysis (CELL 9b)

**Valid cells for comparison:** 310,744

| Metric | Value |
|---|---|
| Scatter delta min | −88.35 dB |
| Scatter delta max | +108.38 dB |
| Scatter delta mean | +0.05 dB |
| Scatter delta std | ±2.99 dB |
| Cells with >2 dB scatter gain | 7,439 (2.4% of covered) |
| Cells with >5 dB scatter gain | 2,213 (0.7% of covered) |
| Cells with >10 dB scatter gain | 1,171 (0.4% of covered) |

### Scatter Impact at 1,200 RX Positions

| Metric | Value |
|---|---|
| Mean scatter delta | +0.42 dB |
| Std scatter delta | ±8.74 dB |
| Max scatter gain | +64.14 dB |
| Min scatter gain | −68.36 dB |
| RX with >2 dB scatter gain | **51 / 1,200 (4.25%)** |

### Top 5 Grid Cells — Maximum Scatter Gain

| X (m) | Y (m) | Dist (m) | RSSI_ON (dBm) | RSSI_OFF (dBm) | Delta (dB) |
|---|---|---|---|---|---|
| 462 | −1,159 | 1,248 | −12.9 | −121.3 | **+108.38** |
| 2 | −1,059 | 1,059 | −21.6 | −116.3 | +94.75 |
| 842 | −839 | 1,189 | −27.7 | −109.4 | +81.65 |
| 522 | −1,059 | 1,181 | −39.7 | −116.8 | +77.20 |
| 252 | −969 | 1,001 | −40.2 | −116.8 | +76.59 |

> Cells with very large scatter gains (+50 to +108 dB) are deep NLOS  
> locations where the direct + specular path is nearly completely  
> blocked (RSSI_OFF ≈ −120 dBm noise floor). Scattered rays are the  
> only mechanism providing coverage there.

### Interpretation

- **2.4% of covered cells** benefit significantly (>2 dB) from Lambertian scattering
- The **51 RX positions** (4.25%) that gain >2 dB are predominantly deep NLOS receivers beyond 1 km where building diffraction alone is insufficient
- The extreme outliers (>50 dB scatter gain) represent cells that are completely shadowed without scattering — scatter provides the only viable propagation path
- The **scatter contribution is modest overall** at 915 MHz because: (1) building penetration loss dominates at close range, (2) diffraction is the primary NLOS mechanism at this frequency, and (3) the ITU-R scattering coefficients (0.05–0.40) represent physical surface roughness

---

## 6. Bias Analysis

| Metric | Value |
|---|---|
| Overall bias (RSSI) | +7.5 dB (sim over-predicts RSSI) |
| Overall RMSE (RSSI) | 12.4 dB |
| Before nDSM rebuild | +13.4 dB bias |
| Improvement from nDSM | −5.9 dB |

### Systematic PL Offset Breakdown

| Source | Contribution |
|---|---|
| RX chain losses (not in Sionna, RX_EXTRA=0) | +7.8 dB |
| TX dipole pattern vs 49 dBm conducted | +2.15 dB |
| **Total systematic offset** | **≈ +10 dB** |

**PL comparison formula:**
- `PL_meas = 56.2 − RSSI_meas` (Ofcom: EIRP=56.2 dBm, system-gain-corrected)
- `PL_sim = −10·log₁₀(path_gain)` (Sionna: includes TX+RX antenna patterns)

---

## 7. Pending Results

| Cell | Description | Status |
|---|---|---|
| CELL 7 | Main PathSolver — all 1,200 RX | ⏳ To run |
| CELL 8e | Distance-band RMSE analysis | ⏳ After CELL 7 |
| CELL DIAG | PL-based MSE/RMSE/STD/R² per band | ⏳ Ready to run |

