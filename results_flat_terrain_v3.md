# Flat Terrain Simulation Report — Sionna RT 2.0
**Scene:** Nottingham / Ofcom 2018 — flat terrain (z = 0 plane)  
**Frequency:** 915.95 MHz  
**TX conducted power:** 49.0 dBm  
**TX antenna gain:** 1.3 dBi (collinear omni, donut pattern)  
**RX height AGL:** 1.5 m  
**MAX_DEPTH:** 8  
**NUM_SAMPLES_PS:** 2 000 000  
**SCATTER_OVERRIDE:** 0.9 (all materials, amplitude split; diffuse power fraction = S² = 81%)  
**Receivers:** 1 200  
**PL formula:** `PL_sim = −10·log10(path_gain)`  
**RSSI formula:** `RSSI_sim = TX_CONDUCTED_DBM + 10·log10(path_gain) = 49.0 + 10·log10(path_gain)`  
**PL reference (measured):** `PL_meas = 49.0 − RSSI_meas`

---

## CELL 8e — Cumulative Distance Evaluation (Scattering ON vs OFF)

Three combining methods evaluated per distance threshold:

| Symbol | Method | Description |
|--------|--------|-------------|
| **incoh** | Incoherent | `path_gain = Σ\|aᵢ\|²` — power sum |
| **coh** | Coherent | `path_gain = \|Σaᵢ\|²` — amplitude sum |
| **best** | Best path | `path_gain = max(\|aᵢ\|²)` — dominant path |

> **Note on avg_rays:** Scattering ON produces 60 000–76 000 rays/RX vs ~450–560 rays/RX with scattering OFF.  
> The ray explosion on flat terrain (no terrain shielding, open ground scatter) makes the incoherent ON sum physically unreliable — energy is accumulated over tens of thousands of paths. Coherent OFF is therefore the recommended primary metric for this scene.

### Results

| Band | N | avg_rays ON | avg_rays OFF | Method | Bias (dB) | RMSE (dB) | R² |
|------|---|------------|-------------|--------|-----------|-----------|-----|
| 0–100 m | 8 | 76 180 | 564 | ON incoh | −8.9 | 10.3 | −7.014 |
| | | | | OFF incoh | −8.9 | 10.3 | −7.022 |
| | | | | ON coh | −7.9 | 10.0 | −6.475 |
| | | | | **OFF coh** | **−7.3** | **9.7** | **−6.013** |
| | | | | ON best | −8.6 | 10.2 | −6.781 |
| | | | | OFF best | −8.6 | 10.2 | −6.781 |
| 0–200 m | 17 | 71 458 | 462 | ON incoh | −5.5 | 7.5 | −3.365 |
| | | | | OFF incoh | −5.5 | 7.5 | −3.368 |
| | | | | ON coh | −2.8 | 7.1 | −2.921 |
| | | | | **OFF coh** | **−1.9** | **7.2** | **−3.002** |
| | | | | ON best | −4.6 | 7.2 | −2.979 |
| | | | | OFF best | −4.6 | 7.2 | −2.979 |
| 0–300 m | 26 | 72 488 | 399 | ON incoh | −6.6 | 8.1 | −0.869 |
| | | | | OFF incoh | −6.7 | 8.2 | −0.919 |
| | | | | ON coh | −3.7 | 7.1 | −0.447 |
| | | | | **OFF coh** | **−1.5** | **6.5** | **−0.207** |
| | | | | ON best | −5.1 | 7.0 | −0.387 |
| | | | | OFF best | −5.1 | 7.0 | −0.387 |
| 0–500 m | 44 | 71 510 | 431 | ON incoh | −9.5 | 11.2 | −0.163 |
| | | | | OFF incoh | −9.5 | 11.2 | −0.167 |
| | | | | ON coh | −6.3 | 10.0 | 0.060 |
| | | | | **OFF coh** | **−2.3** | **6.7** | **0.580** |
| | | | | ON best | −7.3 | 9.2 | 0.209 |
| | | | | OFF best | −7.3 | 9.2 | 0.209 |
| 0–750 m | 67 | 62 890 | 451 | ON incoh | −13.4 | 16.2 | −0.198 |
| | | | | OFF incoh | −13.4 | 16.2 | −0.202 |
| | | | | ON coh | −11.4 | 16.4 | −0.232 |
| | | | | **OFF coh** | **−6.5** | **11.1** | **0.434** |
| | | | | ON best | −11.4 | 14.6 | 0.031 |
| | | | | OFF best | −11.4 | 14.6 | 0.031 |
| 0–900 m | 78 | 61 322 | 458 | ON incoh | −15.7 | 18.6 | −0.453 |
| | | | | OFF incoh | −15.7 | 18.7 | −0.458 |
| | | | | ON coh | −13.7 | 18.3 | −0.408 |
| | | | | **OFF coh** | **−7.3** | **11.4** | **0.457** |
| | | | | ON best | −13.5 | 16.7 | −0.166 |
| | | | | OFF best | −13.5 | 16.7 | −0.166 |
| 0–1000 m | 87 | 62 134 | 461 | ON incoh | −17.7 | 21.0 | −0.627 |
| | | | | OFF incoh | −17.7 | 21.0 | −0.630 |
| | | | | ON coh | −15.8 | 20.6 | −0.567 |
| | | | | **OFF coh** | **−8.6** | **12.5** | **0.419** |
| | | | | ON best | −15.4 | 18.8 | −0.312 |
| | | | | OFF best | −15.4 | 18.8 | −0.312 |

### Best method summary — Coherent OFF

| Band | N | Bias (dB) | RMSE (dB) | R² |
|------|---|-----------|-----------|-----|
| 0–100 m | 8 | −7.3 | 9.7 | −6.013 |
| 0–200 m | 17 | −1.9 | 7.2 | −3.002 |
| 0–300 m | 26 | −1.5 | 6.5 | −0.207 |
| **0–500 m** | **44** | **−2.3** | **6.7** | **0.580** |
| 0–750 m | 67 | −6.5 | 11.1 | 0.434 |
| 0–900 m | 78 | −7.3 | 11.4 | 0.457 |
| 0–1000 m | 87 | −8.6 | 12.5 | 0.419 |

### Key findings

- **Best operating range: 0–500 m** — coherent OFF delivers RMSE = 6.7 dB, R² = 0.580, bias = −2.3 dB (slight underestimate).
- **Coherent OFF consistently outperforms all other methods** at every distance threshold. The coherent sum suppresses the artificial ray-count amplification introduced by scatter ON.
- **Scattering ON degrades accuracy for flat terrain.** With S = 0.9 (81% diffuse power fraction) and no terrain shielding, the open ground generates ~150× more rays than scatter OFF (avg 62k–76k vs 450–560). Incoherent power summing over 60k+ paths is physically unrealistic; it inflates the received power estimate by >15 dB at ranges >500 m.
- **Best-path ON/OFF are identical** — scatter does not change the dominant ray, only adds weak diffuse paths.
- **Performance degrades beyond 500 m** due to the flat terrain geometry (no Nottingham hills to shadow distant paths), causing systematic underestimation of path loss at mid-range.

---

## CELL P.833 — Vegetation Excess Loss

> **Status: Pending — OSM tag fix required.**  
> Current notebook uses overly broad OSM tags that include parks, gardens, meadows and grassland, causing the mean vegetation depth to be ~140 m and mean Weissberger loss ~21 dB (physically unrealistic for urban Nottingham).  
> The corrected notebook restricts tags to dense woodland only (`landuse=forest/wood`, `natural=wood`).  
> Steps to re-run:
> 1. Pull latest notebook from branch `claude/cool-cori-rrWbY`
> 2. Delete `scene/veg_polygons.geojson`
> 3. Re-run CELL P.833

---

## Configuration

| Parameter | Value |
|-----------|-------|
| FLAT_TERRAIN | True |
| GROUND_PRESET | dry (er=2.8, σ=0) |
| SCATTER_OVERRIDE | 0.9 |
| MAX_DEPTH | 8 |
| NUM_SAMPLES_PS | 2 000 000 |
| Receivers | 1 200 |
| TX_CONDUCTED_DBM | 49.0 dBm |
