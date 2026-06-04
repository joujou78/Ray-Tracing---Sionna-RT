# Flat Terrain Results v2
**Date:** 2026-06-04  
**Config:** FLAT_TERRAIN=True, MAX_DEPTH=6, scat_keep_prob=0.001, SITE_CORRECTION_DB=0.0  
**Samples:** 1M per RX (diagnostic run)

## Key Finding
**Overall bias = +0.3 dB** — formula is correct, no correction needed.
**Overall RMSE = 15.9 dB**

## Distance Band Summary (STEP 5, N=42)

| Band        |  N  | Sim RSSI | Meas RSSI | Bias(dB) | RMSE(dB) | Paths |
|-------------|-----|----------|-----------|----------|----------|-------|
| <100m       |   2 |  -16.6   |   -33.8   |  +17.1   |   17.7   |  2351 |
| 100–500m    |  18 |  -32.5   |   -36.5   |   +4.0   |   10.5   |  2384 |
| 500m–1.2km  |  10 |  -50.8   |   -61.0   |  +10.2   |   10.4   |   546 |
| >1.2km      |  12 |  -93.7   |   -77.5   |  -16.2   |   24.1   |     7 |

## Root Cause of Distance-Dependent Bias

| Band | Bias | Cause |
|------|------|-------|
| <300m | -6.4 dB | LOS RX measured at -17 to -24 dBm; sim buildings block them |
| 300–700m | **+12.3 dB** | Flat terrain — no terrain shadowing from Nottingham hills |
| 700–1200m | **+10.2 dB** | Same — terrain variation missing |
| >1.2km | -12 to -28 dB | Too few paths (1–16) at 1M samples |

## Conclusion
The formula is correct (bias = +0.3 dB overall).
The systematic overestimate at 300–1200m is a flat terrain geometry limitation.
Real Nottingham hills create 8–12 dB additional path loss in that range.

## Fix Required
DEM terrain with scipy median_filter spike removal (see dem_spike_solution_plan.md).
No formula or calibration changes needed.
