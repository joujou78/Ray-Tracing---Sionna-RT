# 1802 MHz Calibration Improvement Recommendations

Date: 2026-07-19
Context: CELL CAL running — uncalibrated RMSE 16.59 dB, scalar -8.824 dB → 14.05 dB, Powell convergence expected ~12-13 dB (cal set), ~8-10 dB (100M eval).

---

## Levers in order of impact

### 1. Raise CAL_MIN_DIST_KM (highest potential)
- 0-300m R²=-2.281 — near-range receivers are poisoning Powell
- At 915 MHz, raising 0.15→0.30 hurt because only 208 RX total
- At 1802 MHz we have 721 RX — can afford to exclude more near-range noise
- **Try: CAL_MIN_DIST_KM = 0.30 or 0.40 km** after this run finishes

### 2. More samples per Powell eval
- Current: 1250k per eval (fast but noisy gradient signal)
- **Try: 2M–5M per eval** — cleaner gradient → better convergence
- Cost: 2-4× slower per eval

### 3. Remove noisy features
- `itu_very_dry_ground` (roads at 1802 MHz) and `water_rt` add free material parameters with little physical constraint
- Fewer free materials = cleaner optimisation surface

### 4. Fix range-dependent bias (MAX_DEPTH)
- Bias drifts: -5.5 dB @ 300m → -9.7 dB @ 1750m — not a scalar problem
- MAX_DEPTH=8 may be missing long-range paths
- **Try: MAX_DEPTH=10 or 12** to recover long-range paths and flatten bias curve
- Directly reduces RMSE floor

### 5. Scene geometry
- Already clean: buildings-below-ground fixed, 23 shapes all ID'd, B3 integrity check passes

---

## Current run reference
- NUM_SAMPLES_PS = 2M (eval), 1250k (Powell)
- CAL_MIN_DIST_KM = 0.15, CAL_MAX_DIST_KM = 1.5
- Calibration RX = 721
- DISABLE_VEG_DISCS = True
- MAX_DEPTH = 8
